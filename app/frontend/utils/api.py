import os
import requests
import streamlit as st

# ============================================================
# FASTAPI ENDPOINTS & CLOUD COMPATIBILITY
# ============================================================

def _get_url_list():
    """
    Returns configured API URLs. If none are provided, returns an empty list
    so that Streamlit Community Cloud immediately executes in-process models
    without hanging or timing out on localhost.
    """
    urls = []
    # 1. Check Streamlit Cloud secrets
    try:
        if hasattr(st, "secrets") and "API_URL" in st.secrets:
            val = str(st.secrets["API_URL"]).strip().rstrip("/")
            if val and val not in urls:
                urls.append(val)
    except Exception:
        pass

    # 2. Check Environment Variable
    env_api = os.getenv("API_URL", "").strip().rstrip("/")
    if env_api and env_api not in urls:
        urls.append(env_api)

    return urls

# Public alias for views
get_api_urls = _get_url_list


def _make_post_request(endpoint_path, payload, timeout=2.5):
    """Helper to try API URLs with quick failover."""
    url_list = _get_url_list()
    if not url_list:
        return None
    for url_base in url_list:
        try:
            response = requests.post(f"{url_base}{endpoint_path}", json=payload, timeout=timeout)
            if response.status_code == 200:
                return response.json()
        except Exception:
            continue
    return None


def _make_get_request(endpoint_path, timeout=2.5):
    """Helper to try API URLs with quick failover."""
    url_list = _get_url_list()
    if not url_list:
        return None
    for url_base in url_list:
        try:
            response = requests.get(f"{url_base}{endpoint_path}", timeout=timeout)
            if response.status_code == 200:
                return response.json()
        except Exception:
            continue
    return None


# ============================================================
# DL IMAGE CLASSIFICATION
# ============================================================

def classify_image_api(image_bytes, filename="issue.jpg"):
    """
    Classify an uploaded civic issue photo via FastAPI or direct local DL model fallback.
    """
    for url_base in _get_url_list():
        try:
            files = {"file": (filename, image_bytes, "image/jpeg")}
            response = requests.post(f"{url_base}/predict/image", files=files, timeout=6)
            if response.status_code == 200:
                data = response.json()
                if "error" not in data:
                    return data
        except Exception:
            continue

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
    api_res = _make_post_request("/rag/query", payload, timeout=4)
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

    api_res = _make_post_request("/predict", payload, timeout=3)
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
    api_res = _make_get_request(f"/track/{complaint_number}", timeout=3)
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

    api_res = _make_post_request("/government/update-status", payload, timeout=3)
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