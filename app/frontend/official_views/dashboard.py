import logging
import streamlit as st
import requests
import pandas as pd

logger = logging.getLogger(__name__)

# ============================================================
# FASTAPI BACKEND & DATA FETCHING
# ============================================================

try:
    from app.frontend.utils.api import api_get
except ImportError:
    from utils.api import api_get

_conn_test_import_error = None
try:
    from app.database.connection_test import test_supabase_connection
except Exception as exc:
    _conn_test_import_error = str(exc)
    logger.exception(f"Failed to import test_supabase_connection: {_conn_test_import_error}")
    test_supabase_connection = None

_db_import_error = None
try:
    from app.database.database import fetch_complaints_state, get_client
except Exception as exc2:
    _db_import_error = str(exc2)
    logger.exception(f"Failed to import database functions: {_db_import_error}")

    def fetch_complaints_state():
        return {
            "status": "ERROR",
            "data": [],
            "count": 0,
            "is_empty": False,
            "error_type": "IMPORT_ERROR",
            "error_message": f"Database module import failed: {_db_import_error}",
            "exception": None
        }

    def get_client(force_refresh=False):
        return None


# ============================================================
# SAFE SUPABASE DIAGNOSTIC CARD
# ============================================================

def render_supabase_diagnostic_card(diag=None):
    """Safely render comprehensive 6-step Supabase connection diagnostics without exposing credentials."""
    if diag is None:
        if test_supabase_connection is not None:
            try:
                diag = test_supabase_connection()
            except Exception as e:
                logger.exception("Diagnostic execution failed")
                st.error(f"❌ Diagnostic execution error: {e}")
                return
        else:
            err_detail = _conn_test_import_error or "test_supabase_connection could not be loaded."
            st.error(f"❌ Diagnostic engine unavailable: {err_detail}")
            return

    is_healthy = (diag.get("status") == "HEALTHY")
    classification = diag.get("classification", "UNKNOWN")
    guidance = diag.get("actionable_guidance", "")
    steps = diag.get("steps", {})

    if is_healthy:
        st.success(
            f"✅ **Supabase Cloud Database Connected & Operational** — "
            f"Verified in {diag.get('latency_ms', 0)}ms."
        )
    else:
        st.error(
            f"❌ **Supabase Connection Issue: {classification}** "
            f"(Failed at Step {diag.get('failed_step', '?')})"
        )
        if guidance:
            st.info(f"💡 **Recommended Action:** {guidance}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**URL Configured:** {'✅ Yes' if diag.get('url_masked') != 'Not Configured' else '❌ Missing'}")
        st.markdown(f"**Masked URL:** `{diag.get('url_masked', 'Not Configured')}`")
        st.markdown(f"**Configured Hostname:** `{diag.get('hostname_parsed', 'None')}`")
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

    if st.button("🔄 Retry Connection Check", key="retry_official_diag_btn"):
        try:
            if get_client:
                get_client(force_refresh=True)
        except Exception:
            pass
        st.cache_data.clear()
        st.rerun()


# ============================================================
# METRICS CALCULATION (ROBUST LOCAL FALLBACK)
# ============================================================

def _calculate_dashboard_metrics(complaints: list) -> dict:
    """Calculate all dashboard statistics from raw complaint records."""
    if not complaints:
        return {
            "total_complaints": 0,
            "pending": 0,
            "resolved": 0,
            "emergency": 0,
            "submitted": 0,
            "assigned": 0,
            "under_review": 0,
            "field_inspection": 0,
            "priority": {"low": 0, "medium": 0, "high": 0, "urgent": 0},
            "departments": {}
        }

    df = pd.DataFrame(complaints)
    total = len(df)

    # Status counts
    if "status" in df.columns:
        status_series = df["status"].fillna("").astype(str).str.strip().str.lower()
    else:
        status_series = pd.Series([""] * total)

    submitted = int((status_series == "submitted").sum())
    assigned = int((status_series == "assigned").sum())
    under_review = int((status_series == "under review").sum())
    field_inspection = int((status_series == "field inspection").sum())
    resolved = int((status_series == "resolved").sum())
    pending = total - resolved

    # Emergency counts
    emergency = 0
    if "emergency" in df.columns:
        emergency_vals = df["emergency"].astype(str).str.strip().str.lower()
        emergency = int(emergency_vals.isin(["1", "true", "yes", "emergency"]).sum())

    # Priority counts
    priority = {"low": 0, "medium": 0, "high": 0, "urgent": 0}
    if "priority" in df.columns:
        p_vals = df["priority"].fillna("").astype(str).str.strip().str.lower()
        priority["low"] = int((p_vals == "low").sum())
        priority["medium"] = int((p_vals == "medium").sum())
        priority["high"] = int((p_vals == "high").sum())
        priority["urgent"] = int((p_vals.isin(["urgent", "critical"])).sum())

    # Departments counts
    departments = {}
    if "department" in df.columns:
        d_vals = df["department"].fillna("").astype(str).str.strip()
        d_vals = d_vals[d_vals != ""]
        dept_counts = d_vals.value_counts().to_dict()
        departments = {str(k): int(v) for k, v in dept_counts.items()}

    return {
        "total_complaints": total,
        "pending": pending,
        "resolved": resolved,
        "emergency": emergency,
        "submitted": submitted,
        "assigned": assigned,
        "under_review": under_review,
        "field_inspection": field_inspection,
        "priority": priority,
        "departments": departments
    }


# ============================================================
# GET DASHBOARD DATA
# ============================================================

@st.cache_data(ttl=30)
def get_dashboard_data() -> dict:
    """Fetch government dashboard statistics from FastAPI or Supabase direct fallback."""
    # 1. Try FastAPI backend endpoint
    res = api_get("/government/dashboard", timeout=3)
    if res and isinstance(res, dict) and "total_complaints" in res:
        return {"status": "SUCCESS", "data": res}

    # 2. Direct Supabase query via fetch_complaints_state
    if fetch_complaints_state:
        try:
            state = fetch_complaints_state()
            if state.get("status") == "SUCCESS":
                summary = _calculate_dashboard_metrics(state.get("data", []))
                return {"status": "SUCCESS", "data": summary}
            else:
                return {
                    "status": "ERROR",
                    "error_type": state.get("error_type", "DATABASE_ERROR"),
                    "error_message": state.get("error_message", "Failed to retrieve complaints from Supabase")
                }
        except Exception as e:
            logger.exception("Direct fetch_complaints_state failed")
            return {
                "status": "ERROR",
                "error_type": "FETCH_EXCEPTION",
                "error_message": str(e)
            }

    # 3. Fallback to government_analytics if available
    try:
        from app.backend.government_analytics import get_dashboard_summary
        summary = get_dashboard_summary()
        if summary:
            return {"status": "SUCCESS", "data": summary}
    except Exception as e:
        logger.warning(f"government_analytics fallback failed: {e}")

    return {
        "status": "ERROR",
        "error_type": "NOT_AVAILABLE",
        "error_message": "Both FastAPI backend and direct Supabase database are unreachable."
    }


# ============================================================
# GET TREND DATA
# ============================================================

@st.cache_data(ttl=30)
def get_trend_data() -> dict:
    """Fetch complaint trend information from FastAPI or direct database fallback."""
    # 1. Try FastAPI backend
    res = api_get("/government/trends", timeout=3)
    if res and isinstance(res, dict) and "data" in res:
        return res

    # 2. Direct calculation from Supabase
    if fetch_complaints_state:
        try:
            state = fetch_complaints_state()
            if state.get("status") == "SUCCESS" and state.get("data"):
                df = pd.DataFrame(state["data"])
                if "created_at" in df.columns:
                    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
                    df = df.dropna(subset=["created_at"])
                    df["date"] = df["created_at"].dt.strftime("%Y-%m-%d")
                    daily_counts = df.groupby("date").size().reset_index(name="complaints").sort_values("date")
                    return {"data": daily_counts.to_dict(orient="records")}
        except Exception as e:
            logger.warning(f"Direct trend calculation failed: {e}")

    # 3. Legacy fallback
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

    result = get_dashboard_data()

    if result.get("status") == "ERROR":
        st.error(f"⚠️ **Analytics Data Unavailable: {result.get('error_type', 'Connection Error')}**")
        st.write(
            "The official dashboard could not retrieve complaint records from Supabase. "
            "Below is a live 6-step diagnostic of your database configuration and cloud connectivity:"
        )
        if result.get("error_message"):
            st.code(f"Error Details: {result['error_message']}", language="text")
        render_supabase_diagnostic_card()
        return

    dashboard = result.get("data", {})


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
