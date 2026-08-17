import streamlit as st
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))


# ============================================================
# GOVERNMENT OFFICIAL VIEWS
# ============================================================

from official_views import dashboard
from app.frontend.official_views import predictions
from app.frontend.official_views import dashboard_predictions
from official_views import trend
from official_views import anomaly
from official_views import social_media
from app.frontend.official_views import action_queue
from app.frontend.official_views import hotspot_map
from app.frontend.official_views import executive_report


# ============================================================
# GOVERNMENT OFFICIAL PORTAL
# ============================================================

def show_official_portal():

    # ========================================================
    # SIDEBAR
    # ========================================================

    st.sidebar.title(
        "🏛️ Government Official Portal"
    )

    st.sidebar.caption(
        "Government Intelligence & Analytics"
    )

    st.sidebar.divider()

    # ========================================================
    # LOGGED-IN USER & JURISDICTION SCOPE
    # ========================================================

    user_email = st.session_state.get(
        "user_email",
        "official@gov.in"
    )

    st.sidebar.write(
        f"👤 {user_email}"
    )

    st.sidebar.caption(
        "Government Official"
    )

    from app.utils.locations import DISTRICT_COORDS

    jurisdictions = ["All Jurisdictions (Statewide)"] + sorted(list(DISTRICT_COORDS.keys()))

    selected_jurisdiction = st.sidebar.selectbox(
        "📍 Official Jurisdiction Scope",
        jurisdictions,
        index=0
    )

    st.session_state["official_jurisdiction"] = selected_jurisdiction

    st.sidebar.divider()

    # ========================================================
    # NAVIGATION
    # ========================================================

    page = st.sidebar.radio(
        "Navigation",
        [
            "⚡ Needs Action Queue",
            "📍 Location Hotspots",
            "📄 Executive Report",
            "🏠 Dashboard",
            "🔮 Dashboard Predictions",
            "📋 Predictions",
            "📈 Trend Analysis",
            "🚨 Anomaly Detection",
            "📱 Social Media Analysis",
            "📢 Announcements",
            "⚙️ Settings"
        ]
    )

    # ========================================================
    # ACTION QUEUE
    # ========================================================

    if page == "⚡ Needs Action Queue":

        action_queue.show()

    # ========================================================
    # LOCATION HOTSPOTS
    # ========================================================

    elif page == "📍 Location Hotspots":

        hotspot_map.show()

    # ========================================================
    # EXECUTIVE REPORT
    # ========================================================

    elif page == "📄 Executive Report":

        executive_report.show()

    # ========================================================
    # DASHBOARD
    # ========================================================

    elif page == "🏠 Dashboard":

        dashboard.show()

    # ========================================================
    # PREDICTIONS
    # ========================================================

    elif page == "🔮 Dashboard Predictions":

        dashboard_predictions.show()

    # ========================================================
    # DASHBOARD PREDICTIONS
    # ========================================================

    elif page == "📋 Predictions":

        predictions.show()

    # ========================================================
    # TREND ANALYSIS
    # ========================================================

    elif page == "📈 Trend Analysis":

        trend.show()

    # ========================================================
    # ANOMALY DETECTION
    # ========================================================

    elif page == "🚨 Anomaly Detection":

        anomaly.show()

    # ========================================================
    # SOCIAL MEDIA ANALYSIS
    # ========================================================

    elif page == "📱 Social Media Analysis":

        social_media.show()

    # ========================================================
    # ANNOUNCEMENTS
    # ========================================================

    elif page == "📢 Announcements":

        st.title(
            "📢 Government Announcements"
        )

        st.info(
            "Government announcement management "
            "will be connected here."
        )

        st.write(
            """
            This section can be used to publish and
            manage official government announcements.
            """
        )

    # ========================================================
    # SETTINGS
    # ========================================================

    elif page == "⚙️ Settings":

        st.title(
            "⚙️ Settings"
        )

        st.info(
            "Government portal settings."
        )

        st.write(
            f"Logged in as: **{user_email}**"
        )

        st.write(
            "Role: **Government Official**"
        )

    # ========================================================
    # LOGOUT
    # ========================================================

    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False

        st.session_state.user_role = None

        st.session_state.user_email = None

        st.rerun()


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    st.set_page_config(
        page_title="Government Official Portal",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Do NOT automatically log in.
    # The main app.py controls authentication.
    if not st.session_state.get("logged_in", False):
        st.stop()

    if st.session_state.get("user_role") != "Government Official":
        st.stop()

    show_official_portal()