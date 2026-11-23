import streamlit as st
import pandas as pd
import sys
from pathlib import Path


# ============================================================
# FIX IMPORT PATH
# ============================================================

# Project structure:
#
# ML_project/
# │
# └── app/
#     ├── database/
#     │   ├── database.py
#     │   └── config.py
#     │
#     └── frontend/
#         ├── citizen_portal.py
#         └── views/
#
# Current file:
#
# ML_project/app/frontend/citizen_portal.py
#
# parents[0] = frontend
# parents[1] = app
# parents[2] = ML_project
#
# We need ML_project in sys.path so that:
#
# from app.database.database import supabase
#
# works correctly.


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FRONTEND_DIR = Path(__file__).resolve().parent


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


if "user_role" not in st.session_state:
    st.session_state.user_role = None


if "user_email" not in st.session_state:
    st.session_state.user_email = None


# ============================================================
# DATABASE
# ============================================================
# DATABASE & DIAGNOSTICS
# ============================================================

import logging
logger = logging.getLogger(__name__)

try:
    from app.database.database import (
        get_client,
        get_all_complaints,
        fetch_complaints_state,
        get_last_db_error
    )
except ImportError:
    try:
        from database.database import (
            get_client,
            get_all_complaints,
            fetch_complaints_state,
            get_last_db_error
        )
    except ImportError as _e:
        logger.exception("Failed to import app.database.database")
        get_client = None
        get_all_complaints = lambda: []
        fetch_complaints_state = lambda: {
            "status": "ERROR",
            "data": [],
            "count": 0,
            "is_empty": False,
            "error_type": "IMPORT_ERROR",
            "error_message": str(_e)
        }
        get_last_db_error = lambda: str(_e)

try:
    from app.database.connection_test import test_supabase_connection
except ImportError:
    try:
        from database.connection_test import test_supabase_connection
    except ImportError as _e2:
        logger.exception("Failed to import test_supabase_connection")
        test_supabase_connection = None


def render_supabase_diagnostic_panel(diag=None):
    """
    Safely render comprehensive 6-step Supabase connection diagnostics
    without exposing credentials.
    """
    if diag is None:
        if test_supabase_connection:
            try:
                diag = test_supabase_connection()
            except Exception as e:
                logger.exception("Diagnostic execution failed")
                st.error(f"❌ Diagnostic execution error: {e}")
                return
        else:
            st.error("❌ Diagnostic engine could not be loaded (Module import failure).")
            return

    is_healthy = (diag.get("status") == "HEALTHY")
    classification = diag.get("classification", "UNKNOWN")
    guidance = diag.get("actionable_guidance", "")
    steps = diag.get("steps", {})

    if is_healthy:
        st.success(
            f"✅ **Supabase Cloud Connected & Operational** — "
            f"Verified in {diag.get('latency_ms', 0)}ms."
        )
    else:
        st.error(
            f"❌ **Supabase Connection Issue: {classification}** "
            f"(Failed at Step {diag.get('failed_step', '?')})"
        )
        if guidance:
            st.info(f"💡 **Action Required:** {guidance}")

    # Configuration summary columns
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**URL Configured:** {'✅ Yes' if diag.get('url_masked') != 'Not Configured' else '❌ Missing'}")
        st.markdown(f"**Masked URL:** `{diag.get('url_masked', 'Not Configured')}`")
        st.markdown(f"**Parsed Hostname:** `{diag.get('hostname_parsed', 'None')}`")
        st.markdown(f"**Expected Hostname:** `{diag.get('hostname_expected', 'Unknown')}`")
    with col_b:
        key_meta = diag.get("key_meta", {})
        st.markdown(f"**Key Configured:** {'✅ Yes' if key_meta.get('present') else '❌ Missing'}")
        st.markdown(f"**Key Type:** `{key_meta.get('type', 'None')}` ({key_meta.get('length', 0)} chars)")
        st.markdown(f"**Key Preview:** `{key_meta.get('preview', 'None')}`")
        dns_ips = diag.get("dns_ips", [])
        dns_status = f"✅ Resolved ({', '.join(dns_ips)})" if dns_ips else "❌ Unresolved"
        st.markdown(f"**DNS Resolution:** {dns_status}")

    st.markdown("---")
    st.markdown("##### 🔍 6-Step Verification Protocol")

    step_labels = [
        ("step1_secrets", "Step 1: Secrets Presence (st.secrets / os.environ)"),
        ("step2_url_validation", "Step 2: URL & Hostname Validation"),
        ("step3_dns_resolution", "Step 3: DNS Resolution (IPv4 socket.getaddrinfo)"),
        ("step4_https_probe", "Step 4: HTTPS Probe (/rest/v1/complaints)"),
        ("step5_client_init", "Step 5: Supabase Python Client Init"),
        ("step6_read_query", "Step 6: Read-only Query (complaints table)")
    ]

    for step_key, step_title in step_labels:
        step_info = steps.get(step_key, {})
        passed = step_info.get("passed", False)
        details = step_info.get("details", "Not evaluated")
        icon = "✅" if passed else "❌"
        st.markdown(f"{icon} **{step_title}**: {details}")

    if st.button("🔄 Retry Connection Check", key="retry_db_diag_btn"):
        try:
            get_client(force_refresh=True)
        except Exception:
            pass
        st.cache_data.clear()
        st.rerun()


def get_supabase():
    try:
        return get_client()
    except Exception as e:
        st.error("Unable to connect to database.")
        st.code(str(e))
        return None


# ============================================================
# COMPLAINT HISTORY
# ============================================================

def show_complaint_history():

    st.markdown("---")

    st.subheader(
        "📋 My Complaint History"
    )

    st.caption(
        "View all complaints submitted by your account."
    )

    # --------------------------------------------------------
    # DATABASE FETCH (STRUCTURED STATE - NEVER CONFUSES ERROR WITH 0 RECORDS)
    # --------------------------------------------------------

    try:
        state = fetch_complaints_state()
    except Exception as e:
        logger.exception("Unexpected error calling fetch_complaints_state")
        state = {
            "status": "ERROR",
            "data": [],
            "count": 0,
            "is_empty": False,
            "error_type": "FETCH_EXCEPTION",
            "error_message": str(e)
        }

    # Case 1: Database Error -> NEVER show "You have not submitted any complaints yet"
    if state.get("status") == "ERROR":
        st.error(f"⚠️ **Unable to Load Complaint History: {state.get('error_type', 'Database Error')}**")
        st.write(
            "The application was unable to retrieve your complaint records from Supabase. "
            "Below is a live 6-step diagnostic of your database configuration and cloud connectivity:"
        )
        if state.get("error_message"):
            st.code(f"Error Details: {state['error_message']}", language="text")
        render_supabase_diagnostic_panel()
        return

    # Case 2: Database Success but 0 records
    complaints = state.get("data", [])
    if state.get("is_empty") or len(complaints) == 0:
        st.info("ℹ️ You have not submitted any complaints yet.")
        with st.expander("🔍 Supabase Cloud Diagnostics (Status: Healthy)", expanded=False):
            render_supabase_diagnostic_panel()
        return

    try:
        # ----------------------------------------------------
        # CREATE HISTORY
        # ----------------------------------------------------

        history = []


        for complaint in complaints:

            # ------------------------------------------------
            # DATE / TIME
            # ------------------------------------------------

            created_at = complaint.get(
                "created_at"
            )

            date = "-"
            time = "-"


            if created_at:

                try:

                    timestamp = pd.to_datetime(
                        created_at
                    )

                    date = timestamp.strftime(
                        "%d-%m-%Y"
                    )

                    time = timestamp.strftime(
                        "%I:%M %p"
                    )

                except Exception:

                    pass


            # ------------------------------------------------
            # COMPLAINT ID
            # ------------------------------------------------

            complaint_id = (
                complaint.get("complaint_number")
                or complaint.get("complaint_id")
                or "-"
            )


            # ------------------------------------------------
            # COMPLAINT TEXT
            # ------------------------------------------------

            complaint_text = (
                complaint.get("complaint_text")
                or complaint.get("description")
                or complaint.get("complaint")
                or complaint.get("details")
                or complaint.get("message")
                or "-"
            )


            # ------------------------------------------------
            # DEPARTMENT
            # ------------------------------------------------

            department = (
                complaint.get("department")
                or "-"
            )


            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            status = (
                complaint.get("status")
                or "-"
            )


            # ------------------------------------------------
            # ADD ROW
            # ------------------------------------------------

            history.append(
                {
                    "Complaint ID": complaint_id,
                    "Date": date,
                    "Time": time,
                    "Department": department,
                    "Complaint": complaint_text,
                    "Status": status
                }
            )


        # ----------------------------------------------------
        # DATAFRAME
        # ----------------------------------------------------

        df = pd.DataFrame(
            history
        )


        # ----------------------------------------------------
        # DISPLAY TABLE
        # ----------------------------------------------------

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=500
        )

        with st.expander("🔍 Live Supabase & Database Diagnostics", expanded=False):
            render_supabase_diagnostic_panel()

    except Exception as e:

        st.error(
            "Unable to load complaint history due to an unexpected processing error."
        )

        st.code(
            str(e)
        )
        render_supabase_diagnostic_panel()


# ============================================================
# CITIZEN PORTAL
# ============================================================

def show_citizen_portal():

    # ========================================================
    # SIDEBAR
    # ========================================================

    st.sidebar.title(
        "🏛 Citizen Portal"
    )

    st.sidebar.caption(
        "Citizen Services"
    )


    # ========================================================
    # USER
    # ========================================================

    user_email = st.session_state.get(
        "user_email",
        "citizen@gov.in"
    )


    st.sidebar.write(
        f"👤 {user_email}"
    )


    st.sidebar.caption(
        "Citizen"
    )


    st.sidebar.divider()


    # ========================================================
    # NAVIGATION
    # ========================================================

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Home",
            "📝 Submit Complaint",
            "🔍 Track Complaint",
            "🤖 AI Help",
            "📞 Contact Support",
            "ℹ️ About"
        ]
    )


    # ========================================================
    # HOME
    # ========================================================

    if page == "🏠 Home":

        from views import home

        home.show()


    # ========================================================
    # SUBMIT COMPLAINT
    # ========================================================

    elif page == "📝 Submit Complaint":

        from views import submit

        submit.show()


    # ========================================================
    # TRACK COMPLAINT
    # ========================================================

    elif page == "🔍 Track Complaint":

        from views import track

        track.show()

        show_complaint_history()


    # ========================================================
    # AI HELP
    # ========================================================

    elif page == "🤖 AI Help":

        from views import ai_help

        ai_help.show()


    # ========================================================
    # CONTACT SUPPORT
    # ========================================================

    elif page == "📞 Contact Support":

        st.title(
            "📞 Contact Support"
        )

        st.write(
            "Coming Soon..."
        )


    # ========================================================
    # ABOUT
    # ========================================================

    elif page == "ℹ️ About":

        from views import about

        about.show()


    # ========================================================
    # LOGOUT & DIAGNOSTICS
    # ========================================================

    st.sidebar.divider()
    with st.sidebar.expander("🔍 Database Status", expanded=False):
        render_supabase_diagnostic_panel()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False

        st.session_state.user_role = None

        st.session_state.user_email = None

        st.rerun()


# ============================================================
# DIRECT RUN
# ============================================================

if __name__ == "__main__":

    # Default values when this file is run directly

    if "logged_in" not in st.session_state:

        st.session_state.logged_in = True


    if "user_role" not in st.session_state:

        st.session_state.user_role = "Citizen"


    if "user_email" not in st.session_state:

        st.session_state.user_email = "citizen@gov.in"


    show_citizen_portal()