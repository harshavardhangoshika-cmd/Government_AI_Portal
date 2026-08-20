import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


# ============================================================
# FASTAPI BACKEND
# ============================================================

import os

PRIMARY_API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
FALLBACK_API_URL = "https://government-ai-api.onrender.com"

def _fetch_api(path, timeout=2):
    for base in [PRIMARY_API_URL, FALLBACK_API_URL]:
        try:
            res = requests.get(f"{base}{path}", timeout=timeout)
            if res.status_code == 200:
                return res.json()
        except Exception:
            continue
    return None

# ============================================================
# DEPARTMENT TRENDS DATA
# ============================================================

@st.cache_data(ttl=30)
def get_department_trends():
    """Fetch complaint trends aggregated by department."""
    res = _fetch_api("/government/department-trends", timeout=2)
    if res and "data" in res and res["data"]:
        return res["data"]

    # Direct database fallback if backend API is unreachable
    try:
        from app.database.database import get_all_complaints
        raw = get_all_complaints() or []
        if not raw:
            return []
        df = pd.DataFrame(raw)
        if "created_at" not in df.columns:
            return []
        df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
        df = df.dropna(subset=["created_at_dt"])
        df["date"] = df["created_at_dt"].dt.strftime("%Y-%m-%d")
        df["department"] = df["department"].fillna("General / Unassigned").astype(str).str.strip()
        dept_counts = df.groupby(["date", "department"]).size().reset_index(name="complaints")
        return dept_counts.to_dict(orient="records")
    except Exception:
        return []


# ============================================================
# CURRENT TREND
# ============================================================

@st.cache_data(ttl=30)
def get_current_trend():
    res = _fetch_api("/government/trends", timeout=2)
    if res and "data" in res and res["data"]:
        return res["data"]

    # Direct local fallback
    try:
        from app.backend.government_analytics import get_complaint_history
        history = get_complaint_history()
        if not history.empty:
            history["date"] = pd.to_datetime(history["date"]).dt.strftime("%Y-%m-%d")
            return history.to_dict(orient="records")
    except Exception:
        pass
    return []


# ============================================================
# FORECAST DEMONSTRATION
# ============================================================

@st.cache_data(ttl=30)
def get_forecast_demo():
    res = _fetch_api("/government/forecast-demo", timeout=2)
    if res:
        return res

    # Direct local fallback
    try:
        from app.backend.government_analytics import get_forecast_demonstration
        return get_forecast_demonstration()
    except Exception:
        return None


# ============================================================
# CURRENT TREND GRAPH
# ============================================================

def create_current_trend_graph(df):

    fig = go.Figure()


    fig.add_trace(

        go.Scatter(

            x=df["date"],

            y=df["complaints"],

            mode="lines+markers",

            name="Current Complaints",

            line=dict(
                width=2.5
            ),

            marker=dict(
                size=6
            )

        )

    )


    fig.update_layout(

        title="Current Complaint Trend",

        xaxis_title="Date",

        yaxis_title="Complaint Count",

        template="plotly_dark",

        height=500,

        hovermode="x unified"

    )


    return fig


# ============================================================
# DEPARTMENT TREND GRAPH
# ============================================================

def create_department_trend_graph(dept_df, selected_depts=None, view_type="Line Chart"):
    filtered_df = dept_df.copy()
    if selected_depts and len(selected_depts) > 0:
        filtered_df = filtered_df[filtered_df["department"].isin(selected_depts)]

    if view_type == "Stacked Area Chart":
        fig = px.area(
            filtered_df,
            x="date",
            y="complaints",
            color="department",
            title="Departmental Complaint Volume Distribution (Stacked)",
            labels={"date": "Date", "complaints": "Complaint Count", "department": "Department"},
            template="plotly_dark"
        )
    else:
        fig = px.line(
            filtered_df,
            x="date",
            y="complaints",
            color="department",
            markers=True,
            title="Departmental Complaint Trends Over Time",
            labels={"date": "Date", "complaints": "Complaint Count", "department": "Department"},
            template="plotly_dark"
        )

    fig.update_layout(
        height=520,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )
    return fig


# ============================================================
# HISTORICAL + FORECAST GRAPH
# ============================================================

def create_forecast_graph(
    historical_df,
    forecast_df
):

    fig = go.Figure()


    # ========================================================
    # HISTORICAL DATA
    # ========================================================

    fig.add_trace(

        go.Scatter(

            x=historical_df["date"],

            y=historical_df["complaints"],

            mode="lines+markers",

            name="Historical",

            line=dict(
                width=2.5
            ),

            marker=dict(
                size=5
            )

        )

    )


    # ========================================================
    # FORECAST DATA
    # ========================================================

    fig.add_trace(

        go.Scatter(

            x=forecast_df["date"],

            y=forecast_df[
                "forecasted_complaints"
            ],

            mode="lines+markers",

            name="Forecast",

            line=dict(
                width=2.5,
                dash="dash"
            ),

            marker=dict(
                size=7
            )

        )

    )


    # ========================================================
    # FORECAST START
    # ========================================================

    forecast_start = forecast_df[
        "date"
    ].min()


    fig.add_vline(

        x=forecast_start,

        line_width=2,

        line_dash="dash",

        annotation_text="Forecast Start",

        annotation_position="top"

    )


    # ========================================================
    # GRAPH LAYOUT
    # ========================================================

    fig.update_layout(

        title=(
            "Historical and Forecasted "
            "Complaint Counts"
        ),

        xaxis_title="Year",

        yaxis_title="Complaint Count",

        template="plotly_dark",

        height=600,

        hovermode="x unified",

        legend=dict(

            orientation="h",

            yanchor="bottom",

            y=1.02,

            xanchor="left",

            x=0

        )

    )


    return fig


# ============================================================
# MAIN PAGE
# ============================================================

def show():

    st.title(
        "📈 Trend Analysis"
    )

    st.write(
        "Analyze current complaint activity and "
        "demonstrate the trained complaint forecasting model."
    )


    # ========================================================
    # SECTION 1
    # CURRENT COMPLAINT TREND
    # ========================================================

    st.divider()

    st.subheader(
        "📊 Current Complaint Trend"
    )

    st.write(
        "This graph represents complaint activity currently "
        "available in the Government Complaint System."
    )


    current_data = get_current_trend()


    if current_data:

        current_df = pd.DataFrame(
            current_data
        )


        current_df["date"] = pd.to_datetime(
            current_df["date"],
            errors="coerce"
        )


        current_df["complaints"] = pd.to_numeric(
            current_df["complaints"],
            errors="coerce"
        )


        current_df = current_df.dropna(
            subset=[
                "date",
                "complaints"
            ]
        )


        current_df = current_df.sort_values(
            "date"
        )


        st.plotly_chart(

            create_current_trend_graph(
                current_df
            ),

            use_container_width=True

        )

    else:

        st.info(
            "No current complaint trend data available."
        )


    # ========================================================
    # SECTION 2
    # COMPLAINT TREND BY DEPARTMENT
    # ========================================================

    st.divider()

    st.subheader("🏢 Complaint Trend by Department")
    st.write("Analyze daily complaint progression broken down by specific government departments.")

    dept_trend_data = get_department_trends()

    if dept_trend_data:
        dept_df = pd.DataFrame(dept_trend_data)
        dept_df["date"] = pd.to_datetime(dept_df["date"], errors="coerce")
        dept_df["complaints"] = pd.to_numeric(dept_df["complaints"], errors="coerce")
        dept_df = dept_df.dropna(subset=["date", "complaints"]).sort_values("date")

        dept_list = sorted(list(dept_df["department"].unique()))

        c1, c2 = st.columns([3, 1])
        with c1:
            selected_depts = st.multiselect(
                "Filter Departments",
                dept_list,
                default=dept_list,
                help="Select one or more departments to compare their trend curves."
            )
        with c2:
            chart_type = st.radio(
                "Chart Type",
                ["Line Chart", "Stacked Area Chart"],
                index=0
            )

        if not selected_depts:
            st.warning("Please select at least one department to display the trend graph.")
        else:
            st.plotly_chart(
                create_department_trend_graph(dept_df, selected_depts, chart_type),
                use_container_width=True
            )

            # Department Key Metrics Summary
            filtered_dept_df = dept_df[dept_df["department"].isin(selected_depts)]
            top_dept_name = filtered_dept_df.groupby("department")["complaints"].sum().idxmax() if not filtered_dept_df.empty else "N/A"
            peak_single_day = int(filtered_dept_df["complaints"].max()) if not filtered_dept_df.empty else 0

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("🏢 Active Departments Selected", len(selected_depts))
            with m2:
                st.metric("🏆 Most Active Department", top_dept_name)
            with m3:
                st.metric("📊 Peak Daily Dept Volume", peak_single_day)
    else:
        st.info("No department trend data available.")


    # ========================================================
    # SECTION 3
    # FORECASTING MODEL DEMONSTRATION
    # ========================================================

    st.divider()

    st.subheader(
        "🔮 Forecasting Model Demonstration"
    )

    st.write(
        "Historical complaint data used by the forecasting "
        "module is shown below together with its forecast output."
    )


    demo = get_forecast_demo()


    if demo is None:

        return


    historical_data = demo.get(
        "historical",
        []
    )


    forecast_data = demo.get(
        "forecast",
        []
    )


    # ========================================================
    # CHECK DATA
    # ========================================================

    if not historical_data:

        st.warning(
            "Historical forecasting data is not available."
        )

        return


    if not forecast_data:

        st.warning(
            "Forecast data is not available."
        )

        return


    # ========================================================
    # DATAFRAMES
    # ========================================================

    historical_df = pd.DataFrame(
        historical_data
    )


    forecast_df = pd.DataFrame(
        forecast_data
    )


    historical_df["date"] = pd.to_datetime(
        historical_df["date"]
    )


    forecast_df["date"] = pd.to_datetime(
        forecast_df["date"]
    )


    historical_df["complaints"] = pd.to_numeric(
        historical_df["complaints"]
    )


    forecast_df[
        "forecasted_complaints"
    ] = pd.to_numeric(
        forecast_df[
            "forecasted_complaints"
        ]
    )


    # ========================================================
    # FORECAST GRAPH
    # ========================================================

    st.plotly_chart(

        create_forecast_graph(

            historical_df,

            forecast_df

        ),

        use_container_width=True

    )


    # ========================================================
    # FORECAST SUMMARY
    # ========================================================

    st.subheader(
        "📊 Future Forecast Summary"
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(

            "Historical Period",

            (
                f"{historical_df['date'].min().year}"
                " – "
                f"{historical_df['date'].max().year}"
            )

        )


    with col2:

        st.metric(

            "Forecast Period",

            (
                f"{forecast_df['date'].min().year}"
                " – "
                f"{forecast_df['date'].max().year}"
            )

        )


    with col3:

        st.metric(

            "Forecast Points",

            len(forecast_df)

        )


    # ========================================================
    # IMPORTANT NOTE
    # ========================================================

    st.divider()

    st.subheader(
        "ℹ️ Forecasting Model Note"
    )


    st.info(
        """
**Forecasting Model Demonstration**

The historical portion of this graph represents the
historical complaint dataset used to train and demonstrate
the forecasting model.

The forecast portion demonstrates the format in which
future complaint volumes will be projected.

This forecast is based on the historical training dataset
and is **not a live forecast of the current complaints**.

Once sufficient current complaint history becomes
available, the latest complaint data can be used to
generate a short-term forecast.

For the planned live system:

**Approximately 30 days of current complaint history**
→ **forecast the following 7 days**

This allows the future forecast to reflect the current
complaint situation.
"""
    )
