"""
app/database/database.py
========================
Supabase database connection and complaint management module.
Provides:
- Resilient client initialization with lazy loading and force refresh
- Structured complaint state fetching (fetch_complaints_state) that cleanly separates
  0 complaints (valid empty state) from database connection/query failures
- Backward-compatible get_all_complaints, save_complaint, get_complaint_by_number, update_complaint_status
- Safe connection testing via test_supabase_connection
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from supabase import create_client
from app.database.config import get_credentials

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Custom Database Exceptions
# --------------------------------------------------

class DatabaseError(Exception):
    """Base exception for all database operations."""
    pass

class DatabaseNotConfiguredError(DatabaseError):
    """Raised when Supabase URL or Key is missing."""
    pass

class DatabaseConnectionError(DatabaseError):
    """Raised when network, DNS, or HTTPS connection fails."""
    pass

class DatabaseAuthError(DatabaseError):
    """Raised when Supabase rejects API key or token."""
    pass

class DatabasePermissionError(DatabaseError):
    """Raised when RLS or table permissions deny access."""
    pass


# --------------------------------------------------
# Supabase Connection State (Lazy & Resilient)
# --------------------------------------------------

_supabase_client = None
last_db_error: Optional[str] = None


def get_last_db_error() -> Optional[str]:
    """Return the last recorded database error message."""
    global last_db_error
    return last_db_error


def get_client(force_refresh: bool = False):
    """
    Returns an active Supabase client. Lazily initializes if
    secrets become available after initial module import.
    Pass force_refresh=True to re-read credentials and recreate client.
    """
    global _supabase_client, last_db_error
    if _supabase_client is not None and not force_refresh:
        return _supabase_client

    url, key = get_credentials()
    if url and key:
        try:
            _supabase_client = create_client(url, key)
            last_db_error = None
            logger.info("[OK] Supabase Connected Successfully!")
        except Exception as e:
            last_db_error = str(e)
            logger.warning(f"[WARN] Supabase Connection Failed: {e}")
            _supabase_client = None
    else:
        last_db_error = "SUPABASE_URL or SUPABASE_KEY not configured."
        _supabase_client = None

    return _supabase_client


# Module-level alias for backward compatibility
supabase = get_client()


# --------------------------------------------------
# Structured Complaints Fetching
# --------------------------------------------------

def fetch_complaints_state() -> Dict[str, Any]:
    """
    Fetch all complaints and return an explicit state dictionary.
    CRITICAL: Never confuses a database failure with an empty complaint list.
    
    Returns:
        {
            "status": "SUCCESS" | "ERROR",
            "data": list of dicts,
            "count": int,
            "is_empty": bool,  # True ONLY if status == "SUCCESS" and count == 0
            "error_type": str | None,
            "error_message": str | None,
            "exception": Exception | None
        }
    """
    global last_db_error
    client = get_client()
    if client is None:
        last_db_error = "Database client not initialized (missing or invalid credentials)."
        return {
            "status": "ERROR",
            "data": [],
            "count": 0,
            "is_empty": False,
            "error_type": "NOT_CONFIGURED",
            "error_message": last_db_error,
            "exception": DatabaseNotConfiguredError(last_db_error)
        }

    try:
        response = (
            client
            .table("complaints")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        data = response.data or []
        last_db_error = None
        return {
            "status": "SUCCESS",
            "data": data,
            "count": len(data),
            "is_empty": (len(data) == 0),
            "error_type": None,
            "error_message": None,
            "exception": None
        }
    except Exception as e:
        logger.warning(f"[WARN] Ordered query failed: {e}. Trying unordered fallback...")
        try:
            response = client.table("complaints").select("*").execute()
            data = response.data or []
            last_db_error = None
            return {
                "status": "SUCCESS",
                "data": data,
                "count": len(data),
                "is_empty": (len(data) == 0),
                "error_type": None,
                "error_message": None,
                "exception": None
            }
        except Exception as e2:
            last_db_error = str(e2)
            logger.error(f"[ERROR] fetch_complaints_state failed: {e2}", exc_info=True)
            
            # Classify error type
            err_str = str(e2).lower()
            if "name or service not known" in err_str or "getaddrinfo" in err_str:
                err_type = "DNS_RESOLUTION_FAILURE"
            elif "401" in err_str or "jwt" in err_str or "unauthorized" in err_str:
                err_type = "AUTH_ERROR"
            elif "403" in err_str or "policy" in err_str or "permission" in err_str:
                err_type = "PERMISSION_ERROR"
            elif "timeout" in err_str:
                err_type = "TIMEOUT"
            else:
                err_type = "QUERY_ERROR"

            return {
                "status": "ERROR",
                "data": [],
                "count": 0,
                "is_empty": False,
                "error_type": err_type,
                "error_message": str(e2),
                "exception": e2
            }


__all__ = [
    "get_client",
    "get_all_complaints",
    "fetch_complaints_state",
    "save_complaint",
    "get_complaint_by_number",
    "update_complaint_status",
    "get_last_db_error",
    "last_db_error",
    "supabase",
    "DatabaseError",
    "DatabaseNotConfiguredError",
    "DatabaseConnectionError",
    "DatabaseAuthError",
    "DatabasePermissionError",
]


def get_all_complaints(raise_on_error: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieve all complaints.
    If raise_on_error=True, raises DatabaseError when a failure occurs.
    If raise_on_error=False, returns data if SUCCESS, or [] on error (updating last_db_error).
    """
    state = fetch_complaints_state()
    if state["status"] == "SUCCESS":
        return state["data"]

    if raise_on_error:
        exc = state.get("exception")
        raise DatabaseError(state.get("error_message") or "Failed to retrieve complaints") from exc

    return []


# --------------------------------------------------
# Save & Update Complaints
# --------------------------------------------------

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
        raise DatabaseNotConfiguredError("Database connection not configured. Check Streamlit Secrets.")

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

    try:
        response = client.table("complaints").insert(data).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return data
    except Exception as e:
        logger.error(f"[ERROR] Failed to insert complaint: {e}", exc_info=True)
        raise DatabaseError(f"Database insertion failed: {e}") from e


def get_complaint_by_number(complaint_number):
    client = get_client()
    if client is None:
        return None

    try:
        response = (
            client
            .table("complaints")
            .select("*")
            .eq("complaint_number", complaint_number)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.warning(f"get_complaint_by_number error: {e}")
    return None


def update_complaint_status(complaint_number, status, assigned_officer=None, officer_remarks=None, department=None, priority=None):
    client = get_client()
    if client is None:
        return None

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

    try:
        response = (
            client
            .table("complaints")
            .update(update_data)
            .eq("complaint_number", complaint_number)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.error(f"[ERROR] update_complaint_status error: {e}", exc_info=True)
    return None
