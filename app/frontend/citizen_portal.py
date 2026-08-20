import streamlit as st
import pandas as pd
import sys
from pathlib import Path


# ============================================================
# FIX IMPORT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

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

def get_supabase():

    try:

        from database.database import supabase

        return supabase

    except Exception as e:

        st.error("Unable to connect to database.")

        st.code(str(e))

        return None


# ============================================================
# COMPLAINT HISTORY
# ============================================================

@st.cache_data(ttl=15)
def fetch_citizen_complaints():
    supabase = get_supabase()
    if supabase is None:
        return []
    try:
        response = (
            supabase
            .table("complaints")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception:
        from app.database.database import get_all_complaints
        return get_all_complaints() or []


def show_complaint_history():

    st.markdown("---")

    st.subheader("📋 My Complaint History")

    st.caption(
        "View all complaints submitted by your account."
    )

    try:
        complaints = fetch_citizen_complaints()

        # ----------------------------------------------------
        # NO COMPLAINTS
        # ----------------------------------------------------

        if not complaints:

            st.info(
                "You have not submitted any complaints yet."
            )

            return

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

        df = pd.DataFrame(history)

        # ----------------------------------------------------
        # DISPLAY TABLE
        # ----------------------------------------------------

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=500
        )

    except Exception as e:

        st.error(
            "Unable to load complaint history."
        )

        st.code(str(e))


# ============================================================
# CITIZEN PORTAL
# ============================================================

def show_citizen_portal():

    # ========================================================
    # SIDEBAR HEADER
    # ========================================================

    st.sidebar.title(
        "🏛️ Citizen Portal"
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
            "🔎 Track Complaint",
            "🤖 AI Help",
            "📞 Contact Support",
            "ℹ️ About"
        ],
        key="citizen_navigation"
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

    elif page == "🔎 Track Complaint":

        from views import track

        track.show()

        show_complaint_history()

    # ========================================================
    # AI HELP
    # ========================================================

    elif page == "🤖 AI Help":

        st.title(
            "🤖 AI Help"
        )

        st.write(
            "Coming Soon..."
        )

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
    # LOGOUT AT BOTTOM OF SIDEBAR
    # ========================================================

    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):
        logout()


# ============================================================
# DIRECT RUN
# ============================================================

if __name__ == "__main__":

    if not st.session_state.get(
        "logged_in",
        False
    ):

        st.warning(
            "Please login to access the Citizen Portal."
        )

        st.stop()

    if st.session_state.get(
        "user_role"
    ) != "Citizen":

        st.error(
            "Access denied. Citizen account required."
        )

        st.stop()

    show_citizen_portal()

# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_email = None

    # Clear login-related session values if they exist
    for key in [
        "login_email",
        "login_password",
        "user_name"
    ]:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()


# ============================================================