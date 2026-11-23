import streamlit as st
import requests
import pandas as pd


# ============================================================
# FASTAPI BACKEND & DATA FETCHING
# ============================================================

try:
    from app.frontend.utils.api import api_get
except ImportError:
    from utils.api import api_get

try:
    from app.database.diagnostics import run_supabase_diagnostic
except ImportError:
    try:
        from database.diagnostics import run_supabase_diagnostic
    except ImportError:
        run_supabase_diagnostic = None


# ============================================================
# SAFE SUPABASE DIAGNOSTIC CARD
# ============================================================

def render_supabase_diagnostic_card(diag=None):
    """Safely render Supabase connection diagnostics without exposing credentials."""
    if diag is None and run_supabase_diagnostic:
        diag = run_supabase_diagnostic()
    if not diag:
        st.warning("Diagnostic engine unavailable.")
        return

    is_healthy = (diag.get("status") == "HEALTHY")
    
    if is_healthy:
        st.success(f"✅ **Supabase Database Connected & Operational** — {diag.get('complaint_count', 0)} records accessible in `complaints` table.")
    else:
        st.error(f"❌ **Supabase Connection Issue: {diag.get('classification', 'ERROR')}**")
        if diag.get("actionable_guidance"):
            st.info(f"💡 **Recommended Action:** {diag['actionable_guidance']}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**URL Configured:** {'✅ Yes' if diag.get('url_present') else '❌ Missing'}")
        st.markdown(f"**Host / Endpoint:** `{diag.get('url_masked', 'Not configured')}`")
        dns_status = f"✅ Resolved ({diag.get('dns_ip')})" if diag.get("dns_resolved") else f"❌ Failed ({diag.get('dns_error', 'N/A')})"
        st.markdown(f"**DNS Resolution:** {dns_status}")
    with col_b:
        key_meta = diag.get("key_meta", {})
        st.markdown(f"**Key Configured:** {'✅ Yes' if key_meta.get('present') else '❌ Missing'}")
        st.markdown(f"**Key Type:** `{key_meta.get('type', 'None')}` ({key_meta.get('length', 0)} chars)")
        https_status = f"✅ Reachable (HTTP {diag.get('https_status')})" if diag.get("https_ok") else f"❌ {diag.get('https_error', 'Unavailable')}"
        st.markdown(f"**HTTPS Reachability:** {https_status}")

    st.markdown(f"**Read Query Test (`complaints` table):** {'✅ Passed' if diag.get('query_ok') else '❌ Failed'}")
    if diag.get("error_message") and not is_healthy:
        st.code(f"Diagnostic Details: {diag['error_message']}", language="text")

# ============================================================
# GET DASHBOARD DATA
# ============================================================

@st.cache_data(ttl=30)
def get_dashboard_data():
    """Fetch government dashboard statistics from FastAPI or local analytics fallback."""
    res = api_get("/government/dashboard", timeout=3)
    if res and isinstance(res, dict) and "total_complaints" in res:
        return res

    # Direct local calculation fallback
    try:
        from app.backend.government_analytics import get_dashboard_summary
        return get_dashboard_summary()
    except Exception:
        return None


# ============================================================
# GET TREND DATA
# ============================================================

@st.cache_data(ttl=30)
def get_trend_data():
    """Fetch complaint trend information from FastAPI or local analytics fallback."""
    res = api_get("/government/trends", timeout=3)
    if res and isinstance(res, dict) and "data" in res:
        return res

    # Direct local calculation fallback
    try:
        from app.backend.government_analytics import get_complaint_history
        history = get_complaint_history()
        if not history.empty:
            history["date"] = pd.to_datetime(history["date"]).dt.strftime("%Y-%m-%d")
            return {"data": history.to_dict(orient="records")}
    except Exception:
        pass
    return None


# ============================================================
# GOVERNMENT DASHBOARD
# ============================================================

def show():

    st.title(
        "🏛️ Government Official Portal"
    )

    st.subheader(
        "Government Intelligence Dashboard"
    )

    st.write(
        "Monitor citizen complaints, departments, "
        "priorities, emergencies, and overall complaint activity."
    )


    # ========================================================
    # GET DASHBOARD DATA
    # ========================================================

    dashboard = get_dashboard_data()

    if dashboard is None:

        st.error("⚠️ **Analytics Data Unavailable**")
        st.write(
            "The official dashboard could not retrieve complaint analytics. "
            "A safe automated diagnostic of your database configuration was executed below:"
        )
        render_supabase_diagnostic_card()

        return


    # ========================================================
    # COMPLAINT SUMMARY
    # ========================================================

    st.divider()

    st.subheader(
        "📌 Complaint Summary"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Complaints",
            dashboard.get(
                "total_complaints",
                0
            )
        )

    with col2:

        st.metric(
            "Pending",
            dashboard.get(
                "pending",
                0
            )
        )

    with col3:

        st.metric(
            "Resolved",
            dashboard.get(
                "resolved",
                0
            )
        )

    with col4:

        st.metric(
            "Emergency",
            dashboard.get(
                "emergency",
                0
            )
        )


    # ========================================================
    # COMPLAINT STATUS
    # ========================================================

    st.divider()

    st.subheader(
        "📋 Complaint Status"
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.metric(
            "Submitted",
            dashboard.get(
                "submitted",
                0
            )
        )

    with col2:

        st.metric(
            "Assigned",
            dashboard.get(
                "assigned",
                0
            )
        )

    with col3:

        st.metric(
            "Under Review",
            dashboard.get(
                "under_review",
                0
            )
        )

    with col4:

        st.metric(
            "Field Inspection",
            dashboard.get(
                "field_inspection",
                0
            )
        )

    with col5:

        st.metric(
            "Resolved",
            dashboard.get(
                "resolved",
                0
            )
        )


    # ========================================================
    # PRIORITY ANALYSIS
    # ========================================================
    #
    # Module 5 classes:
    #
    #     Low
    #     Medium
    #     High
    #     Urgent
    #
    # ========================================================

    st.divider()

    st.subheader(
        "⚠️ Priority Analysis"
    )


    priority = dashboard.get(
        "priority",
        {}
    )


    # --------------------------------------------------------
    # READ PRIORITY COUNTS
    # --------------------------------------------------------

    low_count = priority.get(
        "low",
        0
    )

    medium_count = priority.get(
        "medium",
        0
    )

    high_count = priority.get(
        "high",
        0
    )

    # New Module 5 terminology
    urgent_count = priority.get(
        "urgent",
        0
    )


    # --------------------------------------------------------
    # MODULE 5 : URGENT PRIORITY
    # --------------------------------------------------------
    #
    # The backend now returns the final Module 5 label:
    # "urgent"
    #
    # No "critical" fallback is required.
    # --------------------------------------------------------

    urgent_count = priority.get(
        "urgent",
        0
    )


    # --------------------------------------------------------
    # DISPLAY FOUR PRIORITY LEVELS
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)


    # LOW
    with col1:

        st.info(
            f"🔵 Low Priority\n\n"
            f"{low_count} complaints"
        )


    # MEDIUM
    with col2:

        st.warning(
            f"🟡 Medium Priority\n\n"
            f"{medium_count} complaints"
        )


    # HIGH
    with col3:

        st.error(
            f"🔴 High Priority\n\n"
            f"{high_count} complaints"
        )


    # URGENT
    with col4:

        st.error(
            f"🚨 Urgent Priority\n\n"
            f"{urgent_count} complaints"
        )


    # ========================================================
    # PRIORITY SUMMARY TABLE
    # ========================================================

    st.markdown(
        "### 📊 Priority Distribution"
    )

    priority_table = pd.DataFrame({

        "Priority": [
            "Low",
            "Medium",
            "High",
            "Urgent"
        ],

        "Complaints": [
            low_count,
            medium_count,
            high_count,
            urgent_count
        ]
    })


    st.dataframe(
        priority_table,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # DEPARTMENT ANALYSIS
    # ========================================================

    st.divider()

    st.subheader(
        "🏢 Complaints by Department"
    )


    departments = dashboard.get(
        "departments",
        {}
    )


    if departments:

        for department, count in sorted(
            departments.items(),
            key=lambda x: x[1],
            reverse=True
        ):

            st.write(
                f"**{department}** — "
                f"{count} complaints"
            )

    else:

        st.info(
            "No department data available."
        )


    # ========================================================
    # TREND ANALYSIS
    # ========================================================

    st.divider()

    st.subheader(
        "📈 Complaint Trend"
    )


    trend_response = get_trend_data()


    if trend_response is None:

        st.warning(
            "Unable to load complaint trend data."
        )

    else:

        trend_data = trend_response.get(
            "data",
            []
        )


        if trend_data:

            trend_df = pd.DataFrame(
                trend_data
            )


            # ------------------------------------------------
            # CONVERT DATE COLUMN
            # ------------------------------------------------

            trend_df["date"] = pd.to_datetime(
                trend_df["date"]
            )


            # ------------------------------------------------
            # SET DATE AS INDEX
            # ------------------------------------------------

            trend_df = trend_df.set_index(
                "date"
            )


            # ------------------------------------------------
            # DISPLAY TREND CHART
            # ------------------------------------------------

            st.line_chart(
                trend_df["complaints"],
                use_container_width=True
            )


            # ------------------------------------------------
            # DISPLAY UNDERLYING DATA
            # ------------------------------------------------

            with st.expander(
                "📊 View Trend Data"
            ):

                st.dataframe(
                    trend_df,
                    use_container_width=True
                )


        else:

            st.info(
                "Not enough complaint history available "
                "to display a trend."
            )


    # ========================================================
    # BACKEND & DATABASE DIAGNOSTICS
    # ========================================================

    st.divider()

    with st.expander("🔍 Live Supabase & Analytics Diagnostic", expanded=False):
        render_supabase_diagnostic_card()

    st.success(
        "🟢 Government Intelligence Backend Connected"
    )
