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

try:
    from app.database.database import get_client, get_all_complaints
except ImportError:
    from database.database import get_client, get_all_complaints

try:
    from app.database.diagnostics import run_supabase_diagnostic
except ImportError:
    try:
        from database.diagnostics import run_supabase_diagnostic
    except ImportError:
        run_supabase_diagnostic = None


def render_supabase_diagnostic_panel(diag=None):
    """Safely render comprehensive Supabase connection diagnostics without exposing credentials."""
    if diag is None and run_supabase_diagnostic:
        diag = run_supabase_diagnostic()
    if not diag:
        st.warning("Database diagnostic engine unavailable.")
        return

    is_healthy = (diag.get("status") == "HEALTHY")
    
    if is_healthy:
        st.success(f"✅ **Supabase Database Connected & Operational** — {diag.get('complaint_count', 0)} live records accessible.")
    else:
        st.error(f"❌ **Supabase Connection Issue: {diag.get('classification', 'ERROR')}**")
        if diag.get("actionable_guidance"):
            st.info(f"💡 **Action Required:** {diag['actionable_guidance']}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**URL Configured:** {'✅ Yes' if diag.get('url_present') else '❌ Missing'}")
        st.markdown(f"**Configured Hostname:** `{diag.get('hostname_parsed', 'None')}`")
        st.markdown(f"**Expected Hostname:** `{diag.get('hostname_expected', 'Unknown')}`")
        match_str = "✅ Matches Project" if diag.get("hostname_matches_expected") else "❌ MISMATCH (Check secrets)"
        st.markdown(f"**Hostname Match:** {match_str}")
    with col_b:
        key_meta = diag.get("key_meta", {})
        st.markdown(f"**Key Configured:** {'✅ Yes' if key_meta.get('present') else '❌ Missing'}")
        st.markdown(f"**Key Type:** `{key_meta.get('type', 'None')}` ({key_meta.get('length', 0)} chars)")
        dns_status = f"✅ Resolved ({', '.join(diag.get('dns_ipv4_ips', []))})" if diag.get("dns_resolved") else f"❌ Failed ({diag.get('dns_error', 'N/A')})"
        st.markdown(f"**DNS Resolution:** {dns_status}")
        https_status = f"✅ Reachable (HTTP {diag.get('https_status')})" if diag.get("https_ok") else f"❌ {diag.get('https_error', 'Unavailable')}"
        st.markdown(f"**HTTPS Reachability:** {https_status}")

    st.markdown(f"**Read Query Test (`complaints` table):** {'✅ Passed' if diag.get('query_ok') else '❌ Failed'}")
    if diag.get("error_message") and not is_healthy:
        st.code(f"Diagnostic Trace: {diag['error_message']}", language="text")

    if st.button("🔄 Retry Connection Check", key="retry_db_diag_btn"):
        try:
            from app.database.database import get_client
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
    # DATABASE FETCH (CENTRALIZED)
    # --------------------------------------------------------

    try:
        from app.database.database import get_all_complaints, last_db_error
        complaints = get_all_complaints()
    except Exception as e:
        complaints = []
        last_db_error = str(e)

    # If complaints could not be fetched due to database error
    if not complaints:
        try:
            from app.database.database import last_db_error
        except Exception:
            last_db_error = None

        if last_db_error:
            st.error("⚠️ **Unable to Load Complaint History: Database Connection Issue**")
            st.write(
                "The application was unable to retrieve your complaint records from Supabase. "
                "Below is a live diagnostic of your database configuration and cloud connectivity:"
            )
            render_supabase_diagnostic_panel()
            return
        else:
            # Let's run diagnostic to verify if truly empty or database unreachable
            if run_supabase_diagnostic:
                diag = run_supabase_diagnostic()
                if diag.get("status") != "HEALTHY":
                    st.error(f"⚠️ **Database Connection Issue: {diag.get('classification', 'ERROR')}**")
                    render_supabase_diagnostic_panel(diag)
                    return

            st.info("You have not submitted any complaints yet.")
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