import os
import requests
import streamlit as st

# ============================================================
# FASTAPI ENDPOINTS & CLOUD COMPATIBILITY
# ============================================================

def _is_port_open(host="127.0.0.1", port=8000, timeout=0.3):
    """Fast non-blocking check to see if local backend is alive."""
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _get_url_list():
    """
    Returns configured API URLs in order of priority:
    1. Streamlit Secrets (API_BASE_URL, API_URL, BACKEND_URL)
    2. Environment Variables (API_BASE_URL, API_URL, BACKEND_URL)
    3. Local development fallback (localhost:8000) only if running locally and port is active.
    """
    urls = []

    # 1. Check Streamlit Cloud secrets
    try:
        if hasattr(st, "secrets"):
            for key in ("API_BASE_URL", "API_URL", "BACKEND_URL"):
                if key in st.secrets:
                    val = str(st.secrets[key]).strip().rstrip("/")
                    if val and val not in urls:
                        urls.append(val)
    except Exception:
        pass

    # 2. Check Environment Variables
    for env_key in ("API_BASE_URL", "API_URL", "BACKEND_URL"):
        env_val = os.getenv(env_key, "").strip().rstrip("/")
        if env_val and env_val not in urls:
            urls.append(env_val)

    # 3. Local Development Fallback: if no cloud URL is set, check if local port 8000 is running
    if not urls:
        # Check if running locally (not inside Streamlit Cloud container)
        is_cloud = os.getenv("STREAMLIT_SERVER_GATHER_USAGE_STATS") == "false" and os.path.exists("/app")
        if not is_cloud:
            if _is_port_open("127.0.0.1", 8000):
                urls.append("http://127.0.0.1:8000")

    return urls

# Public aliases for views
get_api_urls = _get_url_list


def get_primary_api_url():
    """Returns the primary configured backend URL or None."""
    urls = _get_url_list()
    return urls[0] if urls else None


@st.cache_data(ttl=20)
def is_backend_available():
    """Checks if any configured backend is responsive via /health probe."""
    urls = _get_url_list()
    if not urls:
        return False
    for base in urls:
        try:
            r = requests.get(f"{base}/health", timeout=1.5)
            if r.status_code == 200:
                return True
        except Exception:
            continue
    return False


def render_backend_status_pill():
    """Renders a status badge indicating whether FastAPI is connected or running in-process."""
    primary = get_primary_api_url()
    if primary:
        if is_backend_available():
            st.sidebar.success(f"🟢 **FastAPI Backend Connected**\n`{primary}`")
        else:
            st.sidebar.warning(f"🟡 **Backend Offline / Waking Up**\n`{primary}` (Using in-process fallback)")
    else:
        st.sidebar.info("⚡ **In-Process Engine Active**\n*(To connect dedicated backend, set `API_BASE_URL` in Secrets)*")


def api_get(endpoint_path, timeout=3.5):
    """
    Standard GET request across configured backend URLs with quick failover.
    Returns JSON dict on success or None.
    """
    for url_base in _get_url_list():
        try:
            response = requests.get(f"{url_base}{endpoint_path}", timeout=timeout)
            if response.status_code == 200:
                return response.json()
        except Exception:
            continue
    return None


def api_post(endpoint_path, payload=None, files=None, timeout=5.0):
    """
    Standard POST request across configured backend URLs with quick failover.
    Returns JSON dict on success or None.
    """
    for url_base in _get_url_list():
        try:
            if files:
                response = requests.post(f"{url_base}{endpoint_path}", data=payload, files=files, timeout=timeout)
            else:
                response = requests.post(f"{url_base}{endpoint_path}", json=payload, timeout=timeout)
            if response.status_code == 200:
                return response.json()
        except Exception:
            continue
    return None

# Backward compatibility alias
_make_get_request = api_get
_make_post_request = lambda path, payload, timeout=2.5: api_post(path, payload=payload, timeout=timeout)


# ============================================================
# DL IMAGE CLASSIFICATION
# ============================================================

def classify_image_api(image_bytes, filename="issue.jpg"):
    """
    Classify an uploaded civic issue photo via FastAPI or direct local DL model fallback.
    """
    files = {"file": (filename, image_bytes, "image/jpeg")}
    api_res = api_post("/predict/image", files=files, timeout=8.0)
    if api_res and "error" not in api_res:
        return api_res

    # Direct local DL execution fallback if API is unreachable
    try:
        from app.dl.image_classification.predict_image import classify_image
        return classify_image(image_bytes)
    except Exception as e:
        return {
            "error": f"Image classification model unavailable: {e}"
        }


# ============================================================
# CIVIC RAG KNOWLEDGE QUERY
# ============================================================

def query_rag_api(query, top_k=3):
    """
    Queries the Civic RAG Knowledge Base via FastAPI or direct local fallback.
    """
    payload = {"query": query, "top_k": top_k}
    api_res = api_post("/rag/query", payload=payload, timeout=4.0)
    if api_res and "error" not in api_res:
        return api_res

    # Direct local execution fallback if API is unreachable
    try:
        from app.rag.rag_service import ask_civic_rag
        return ask_civic_rag(query, top_k=top_k)
    except Exception as e:
        return {
            "error": f"Civic AI Help service unavailable: {e}"
        }


# ============================================================
# SUBMIT COMPLAINT
# ============================================================

def submit_complaint(text, state="Karnataka", district="Bengaluru Urban", image_meta=None):
    """
    Send a citizen complaint to FastAPI with location details or fallback to local processing.
    Optionally enriches with deep learning visual evidence.
    """
    enriched_text = text
    if image_meta and image_meta.get("display_name"):
        conf = image_meta.get("confidence", 0)
        disp = image_meta.get("display_name")
        enriched_text = f"[Visual Evidence: {disp} ({conf}% confidence)]\n{text}"

    payload = {
        "text": enriched_text,
        "state": state,
        "district": district
    }

    api_res = api_post("/predict", payload=payload, timeout=4.0)
    if api_res and "error" not in api_res:
        if image_meta:
            api_res["image_meta"] = image_meta
        return api_res

    # Direct local execution fallback if API is unreachable
    try:
        from app.backend.predict import process_complaint
        from app.database.database import save_complaint

        result = process_complaint(enriched_text)

        # Corroborate or refine department if high-confidence image was provided
        if image_meta and image_meta.get("is_confident"):
            if image_meta.get("suggested_department"):
                result["department"] = image_meta["suggested_department"]
            if image_meta.get("suggested_reason"):
                result["complaint_reason"] = image_meta["suggested_reason"]
            if image_meta.get("suggested_priority") == "Urgent":
                result["priority"] = "Urgent"

        try:
            saved = save_complaint(
                complaint_text=enriched_text,
                sentiment=result.get("sentiment"),
                feedback_category=result.get("feedback_category"),
                complaint_reason=result.get("complaint_reason"),
                department=result.get("department"),
                harmful=(result.get("harmful_content") == "Harmful"),
                emergency=result.get("emergency"),
                priority=result.get("priority"),
                recommended_schemes=result.get("recommended_schemes"),
                state=state,
                district=district
            )
            result["complaint_id"] = saved.get("id")
            result["complaint_number"] = saved.get("complaint_number")
            result["storage_status"] = "persisted_in_database"
            result["storage_error"] = None
        except Exception as db_err:
            from datetime import datetime, timezone
            offline_num = f"OFFLINE-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            result["complaint_id"] = None
            result["complaint_number"] = offline_num
            result["storage_status"] = "offline_database_unavailable"
            result["storage_error"] = str(db_err)

        if image_meta:
            result["image_meta"] = image_meta
        return result
    except Exception as e:
        return {
            "error": f"Unable to process complaint: {e}"
        }


# ============================================================
# TRACK COMPLAINT
# ============================================================

@st.cache_data(ttl=15)
def track_complaint(complaint_number):
    """
    Retrieve complaint information using Complaint ID.
    """
    api_res = api_get(f"/track/{complaint_number}", timeout=3.0)
    if api_res and "error" not in api_res:
        return api_res

    # Direct database fallback
    try:
        from app.database.database import get_complaint_by_number
        complaint = get_complaint_by_number(complaint_number)
        if complaint:
            return {
                "complaint_number": complaint.get("complaint_number"),
                "status": complaint.get("status"),
                "department": complaint.get("department"),
                "complaint_reason": complaint.get("complaint_reason"),
                "assigned_officer": complaint.get("assigned_officer"),
                "officer_remarks": complaint.get("officer_remarks"),
                "created_at": complaint.get("created_at"),
                "updated_at": complaint.get("updated_at")
            }
        return {"error": "Complaint not found"}
    except Exception as e:
        return {"error": f"Unable to retrieve complaint: {e}"}


# ============================================================
# UPDATE COMPLAINT STATUS
# ============================================================

def update_complaint_status(complaint_number, status, assigned_officer=None, officer_remarks=None, department=None, priority=None):
    """
    Update complaint status, assigned officer, remarks, department, and priority.
    """
    payload = {
        "complaint_number": complaint_number,
        "status": status,
        "assigned_officer": assigned_officer,
        "officer_remarks": officer_remarks,
        "department": department,
        "priority": priority
    }

    api_res = api_post("/government/update-status", payload=payload, timeout=4.0)
    if api_res and "error" not in api_res:
        return api_res

    # Direct database fallback
    try:
        from app.database.database import update_complaint_status as db_update
        from app.utils.sla_engine import compute_sla
        updated = db_update(
            complaint_number=complaint_number,
            status=status,
            assigned_officer=assigned_officer,
            officer_remarks=officer_remarks,
            department=department,
            priority=priority
        )
        if updated:
            return {
                "message": "Complaint status updated successfully.",
                "complaint": compute_sla(updated)
            }
        return {"error": "Failed to update complaint status."}
    except Exception as e:
        return {"error": f"Unable to update status: {e}"}
