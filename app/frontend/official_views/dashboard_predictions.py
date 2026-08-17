import streamlit as st
import requests
import pandas as pd


# ============================================================
# FASTAPI BACKEND
# ============================================================

API_URL = "https://government-ai-api.onrender.com"


# ============================================================
# GET GOVERNMENT PREDICTIONS
# ============================================================

def get_predictions():

    try:

        response = requests.get(
            f"{API_URL}/government/predictions",
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
# DASHBOARD PREDICTIONS PAGE
# ============================================================

def show():

    st.title("🤖 Government AI Predictions")

    st.write(
        "AI-powered analysis of complaint patterns across "
        "all complaints received by the government."
    )

    st.divider()


    # ========================================================
    # LOAD DATA
    # ========================================================

    predictions = get_predictions()

    if predictions is None:

        st.warning(
            "Please make sure the FastAPI backend is running "
            "on port 8000."
        )

        return


    # ========================================================
    # EXTRACT DATA
    # ========================================================

    total = predictions.get(
        "total_analyzed",
        0
    )

    sentiment = predictions.get(
        "sentiment",
        {}
    )

    feedback = predictions.get(
        "feedback_category",
        {}
    )

    reasons = predictions.get(
        "complaint_reason",
        {}
    )

    priority = predictions.get(
        "priority",
        {}
    )

    emergency = predictions.get(
        "emergency",
        {}
    )

    department_analysis = predictions.get(
        "department_analysis",
        []
    )


    # ========================================================
    # PREDICTION OVERVIEW
    # ========================================================

    st.subheader("📊 Prediction Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Complaints Analyzed",
            total
        )

    with col2:

        st.metric(
            "Negative Complaints",
            sentiment.get(
                "Negative",
                0
            )
        )

    with col3:

        st.metric(
            "Emergency Complaints",
            emergency.get(
                "emergency",
                0
            )
        )

    with col4:

        st.metric(
            "High Priority",
            priority.get(
                "high",
                0
            )
        )


    # ========================================================
    # SENTIMENT
    # ========================================================

    st.divider()

    st.subheader("😊 Complaint Sentiment")

    if sentiment:

        sentiment_df = pd.DataFrame(
            {
                "Sentiment": list(
                    sentiment.keys()
                ),
                "Complaints": list(
                    sentiment.values()
                )
            }
        )

        st.bar_chart(
            sentiment_df.set_index(
                "Sentiment"
            )
        )

    else:

        st.info(
            "No sentiment data available."
        )


    # ========================================================
    # FEEDBACK CATEGORY
    # ========================================================

    st.divider()

    st.subheader("📂 Complaint Categories")

    if feedback:

        feedback_df = pd.DataFrame(
            {
                "Category": list(
                    feedback.keys()
                ),
                "Complaints": list(
                    feedback.values()
                )
            }
        )

        feedback_df = feedback_df.sort_values(
            "Complaints",
            ascending=False
        )

        st.bar_chart(
            feedback_df.set_index(
                "Category"
            )
        )

    else:

        st.info(
            "No complaint category data available."
        )


    # ========================================================
    # DEPARTMENT ANALYSIS GRAPH
    # ========================================================

    st.divider()

    st.subheader(
        "🏢 Department-wise Complaint Analysis"
    )

    if department_analysis:

        department_df = pd.DataFrame(
            department_analysis
        )

        # ----------------------------------------------------
        # Check required columns
        # ----------------------------------------------------

        if (
            "department" in department_df.columns
            and "complaints" in department_df.columns
        ):

            graph_df = department_df[
                [
                    "department",
                    "complaints"
                ]
            ].copy()

            # Sort departments by complaint count
            graph_df = graph_df.sort_values(
                "complaints",
                ascending=False
            )

            # Rename columns for display
            graph_df = graph_df.rename(
                columns={
                    "department": "Department",
                    "complaints": "Complaints"
                }
            )

            # Department graph
            st.bar_chart(
                graph_df.set_index(
                    "Department"
                )
            )

        else:

            st.info(
                "Department complaint data is not available."
            )

    else:

        st.info(
            "No department analysis data available."
        )


    # ========================================================
    # DEPARTMENT INTELLIGENCE TABLE
    # ========================================================

    st.divider()

    st.subheader(
        "🏢 Department Intelligence"
    )

    if department_analysis:

        department_table_df = pd.DataFrame(
            department_analysis
        )

        display_columns = [
            "department",
            "complaints",
            "high_priority",
            "emergency",
            "negative_sentiment"
        ]

        available_columns = [
            column
            for column in display_columns
            if column in department_table_df.columns
        ]

        if available_columns:

            department_table_df = (
                department_table_df[
                    available_columns
                ]
            )

            department_table_df = (
                department_table_df.rename(
                    columns={
                        "department":
                            "Department",

                        "complaints":
                            "Complaints",

                        "high_priority":
                            "High Priority",

                        "emergency":
                            "Emergency",

                        "negative_sentiment":
                            "Negative Sentiment"
                    }
                )
            )

            st.dataframe(
                department_table_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Department intelligence columns are not available."
            )

    else:

        st.info(
            "No department intelligence available."
        )


    # ========================================================
    # COMPLAINT REASONS
    # ========================================================

    st.divider()

    st.subheader(
        "🔎 Complaint Reasons"
    )

    if reasons:

        reasons_df = pd.DataFrame(
            {
                "Reason": list(
                    reasons.keys()
                ),
                "Complaints": list(
                    reasons.values()
                )
            }
        )

        reasons_df = reasons_df.sort_values(
            "Complaints",
            ascending=False
        )

        st.bar_chart(
            reasons_df.set_index(
                "Reason"
            )
        )

    else:

        st.info(
            "No complaint reason data available."
        )


    # ========================================================
    # PRIORITY
    # ========================================================

    st.divider()

    st.subheader(
        "⚠️ Priority Analysis"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.info(
            f"🔵 Low Priority\n\n"
            f"{priority.get('low', 0)} complaints"
        )

    with col2:

        st.warning(
            f"🟡 Medium Priority\n\n"
            f"{priority.get('medium', 0)} complaints"
        )

    with col3:

        st.error(
            f"🔴 High Priority\n\n"
            f"{priority.get('high', 0)} complaints"
        )

    with col4:

        st.error(
            f"🚨 Urgent Priority\n\n"
            f"{priority.get('Urgent', 0)} complaints"
        )


    # ========================================================
    # EMERGENCY
    # ========================================================

    st.divider()

    st.subheader(
        "🚨 Emergency Analysis"
    )

    emergency_df = pd.DataFrame(
        {
            "Type": [
                "Emergency",
                "Normal"
            ],
            "Complaints": [
                emergency.get(
                    "emergency",
                    0
                ),
                emergency.get(
                    "normal",
                    0
                )
            ]
        }
    )

    st.bar_chart(
        emergency_df.set_index(
            "Type"
        )
    )


    # ========================================================
    # GOVERNMENT INTELLIGENCE
    # ========================================================

    st.divider()

    st.subheader(
        "🧠 Government Intelligence"
    )

    if department_analysis:

        # Find department with highest complaint volume
        top_department = max(
            department_analysis,
            key=lambda x: x.get(
                "complaints",
                0
            )
        )

        st.info(
            f"🏢 **Highest Complaint Volume:** "
            f"{top_department.get('department', 'Unknown')} "
            f"— "
            f"{top_department.get('complaints', 0)} complaints"
        )

        st.info(
            f"🚨 **Emergency Complaints:** "
            f"{emergency.get('emergency', 0)}"
        )

        st.info(
            f"🔴 **High Priority Complaints:** "
            f"{priority.get('high', 0)}"
        )

        st.info(
            f"😟 **Negative Sentiment Complaints:** "
            f"{sentiment.get('Negative', 0)}"
        )

    else:

        st.info(
            "AI insights will appear when complaint "
            "data becomes available."
        )


    # ========================================================
    # BACKEND STATUS
    # ========================================================

    st.divider()

    st.success(
        "🟢 Government AI Prediction Engine Connected"
    )
