# --------------------------------------------------
# Import Supabase Client
# --------------------------------------------------

from supabase import create_client
from app.database.config import get_credentials

# --------------------------------------------------
# Create Supabase Connection (Lazy & Resilient)
# --------------------------------------------------

supabase = None

def get_client():
    """
    Returns an active Supabase client. Lazily initializes if
    secrets become available after initial module import.
    """
    global supabase
    if supabase is not None:
        return supabase

    url, key = get_credentials()
    if url and key:
        try:
            supabase = create_client(url, key)
            print("[OK] Supabase Connected Successfully!")
        except Exception as e:
            print(f"[WARN] Supabase Connection Failed: {e}")
            supabase = None
    return supabase

# Initial connection attempt on module import
supabase = get_client()


def save_complaint(
    complaint_text,
    sentiment,
    feedback_category,
    complaint_reason,
    department,
    harmful,
    emergency,
    priority=None,
    recommended_schemes=None,
    state=None,
    district=None
):
    client = get_client()
    if client is None:
        raise RuntimeError("Database connection not configured.")

    data = {
        "complaint_text": complaint_text,
        "sentiment": sentiment,
        "feedback_category": feedback_category,
        "complaint_reason": complaint_reason,
        "department": department,
        "harmful": harmful,
        "emergency": emergency,
        "priority": priority,
        "recommended_schemes": recommended_schemes,
        "state": state,
        "district": district,
        "status": "Submitted"
    }

    response = client.table("complaints").insert(data).execute()

    return response.data[0]


def get_complaint_by_number(complaint_number):
    client = get_client()
    if client is None:
        return None

    response = (
        client
        .table("complaints")
        .select("*")
        .eq("complaint_number", complaint_number)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def get_all_complaints():
    client = get_client()
    if client is None:
        return []

    response = (
        client
        .table("complaints")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def update_complaint_status(complaint_number, status, assigned_officer=None, officer_remarks=None, department=None, priority=None):
    client = get_client()
    if client is None:
        return None

    from datetime import datetime, timezone

    update_data = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if assigned_officer is not None:
        update_data["assigned_officer"] = assigned_officer
    if officer_remarks is not None:
        update_data["officer_remarks"] = officer_remarks
    if department is not None:
        update_data["department"] = department
    if priority is not None:
        update_data["priority"] = priority

    response = (
        client
        .table("complaints")
        .update(update_data)
        .eq("complaint_number", complaint_number)
        .execute()
    )

    if response.data:
        return response.data[0]
    return None
