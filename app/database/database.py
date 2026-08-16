# --------------------------------------------------
# Import Supabase Client
# --------------------------------------------------

from supabase import create_client
from app.database.config import SUPABASE_URL, SUPABASE_KEY

# --------------------------------------------------
# Create Supabase Connection
# --------------------------------------------------

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("[OK] Supabase Connected Successfully!")

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

    response = supabase.table("complaints").insert(data).execute()

    return response.data[0]

def get_complaint_by_number(complaint_number):

    response = (
        supabase
        .table("complaints")
        .select("*")
        .eq("complaint_number", complaint_number)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None

def get_all_complaints():

    response = (
        supabase
        .table("complaints")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data

def update_complaint_status(complaint_number, status, assigned_officer=None, officer_remarks=None, department=None, priority=None):
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
        supabase
        .table("complaints")
        .update(update_data)
        .eq("complaint_number", complaint_number)
        .execute()
    )

    if response.data:
        return response.data[0]
    return None