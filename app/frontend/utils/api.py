import os
import requests
import streamlit as st

# ============================================================
# FASTAPI ENDPOINTS
# ============================================================

ENV_API_URL = os.getenv("API_URL")
RENDER_API_URL = "https://government-ai-api.onrender.com"
LOCAL_API_URL = "http://127.0.0.1:8000"

def _get_url_list():
    if ENV_API_URL:
        return [ENV_API_URL.rstrip("/"), RENDER_API_URL, LOCAL_API_URL]
    return [RENDER_API_URL, LOCAL_API_URL]


def _make_post_request(endpoint_path, payload, timeout=2.5):
    """Helper to try API URLs with quick failover."""
    for url_base in _get_url_list():
        try:
            response = requests.post(f"{url_base}{endpoint_path}", json=payload, timeout=timeout)
            if response.status_code == 200:
                return response.json()
        except Exception:
            continue
    return None


def _make_get_request(endpoint_path, timeout=2.5):
    """Helper to try API URLs with quick failover."""
    for url_base in _get_url_list():
        try:
            response = requests.get(f"{url_base}{endpoint_path}", timeout=timeout)
            if response.status_code == 200:
                return response.json()
        except Exception:
            continue
    return None


# ============================================================
# SUBMIT COMPLAINT
# ============================================================

def submit_complaint(text, state="Karnataka", district="Bengaluru Urban"):
    """
    Send a citizen complaint to FastAPI with location details or fallback to local processing.
    """
    payload = {
        "text": text,
        "state": state,
        "district": district
    }
    
    api_res = _make_post_request("/predict", payload, timeout=3)
    if api_res and "error" not in api_res:
        return api_res

    # Direct local execution fallback if API is unreachable
    try:
        from app.backend.predict import process_complaint
        from app.database.database import save_complaint

        result = process_complaint(text)
        saved = save_complaint(
            complaint_text=text,
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