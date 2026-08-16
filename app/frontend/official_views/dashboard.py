import streamlit as st
import requests
import pandas as pd


# ============================================================
# FASTAPI BACKEND
# ============================================================

API_URL = "http://127.0.0.1:8000"


# ============================================================
# GET DASHBOARD DATA
# ============================================================

def get_dashboard_data():
    """
    Fetch government dashboard statistics from FastAPI.
    """

    try:

        response = requests.get(
            f"{API_URL}/government/dashboard",
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            f"❌ Unable to connect to Government Backend: {e}"
        )

        return None


# ============================================================
# GET TREND DATA
# ============================================================

def get_trend_data():
    """
    Fetch complaint trend information from FastAPI.
    """

    try:

        response = requests.get(
            f"{API_URL}/government/trends",
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            f"❌ Unable to load complaint trends: {e}"
        )

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

        st.warning(
            "Please make sure the FastAPI backend is running "
            "on port 8000."
        )

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
    # BACKEND STATUS
    # ========================================================

    st.divider()

    st.success(
        "🟢 Government Intelligence Backend Connected"
    )