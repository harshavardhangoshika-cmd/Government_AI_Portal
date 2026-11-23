"""
app/database package
Provides database models, connection utilities, and independent diagnostics.
"""

from app.database.config import get_credentials, PROJECT_EXPECTED_HOST, PROJECT_DEFAULT_URL
from app.database.connection_test import test_supabase_connection
from app.database.database import (
    get_client,
    get_all_complaints,
    fetch_complaints_state,
    save_complaint,
    get_complaint_by_number,
    update_complaint_status,
    get_last_db_error,
    last_db_error,
    DatabaseError,
    DatabaseNotConfiguredError,
    DatabaseConnectionError,
    DatabaseAuthError,
    DatabasePermissionError,
)

__all__ = [
    "get_credentials",
    "PROJECT_EXPECTED_HOST",
    "PROJECT_DEFAULT_URL",
    "test_supabase_connection",
    "get_client",
    "get_all_complaints",
    "fetch_complaints_state",
    "save_complaint",
    "get_complaint_by_number",
    "update_complaint_status",
    "get_last_db_error",
    "last_db_error",
    "DatabaseError",
    "DatabaseNotConfiguredError",
    "DatabaseConnectionError",
    "DatabaseAuthError",
    "DatabasePermissionError",
]
