import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go


# ============================================================
# BACKEND CONFIGURATION
# ============================================================

API_URL = "https://government-ai-api.onrender.com"

ANOMALY_THRESHOLD = 100.0


# ============================================================
# GET CURRENT ANOMALY DATA FROM FASTAPI
# ============================================================

def get_anomaly_data():

    try:

        response = requests.get(
            f"{API_URL}/government/anomalies/current",
            timeout=20
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            f"❌ Unable to connect to Government Backend:\n\n{e}"
        )

        return None


# ============================================================
# PREPARE CURRENT DAILY DATA
# ============================================================

def prepare_daily_data(data):

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["complaints"] = pd.to_numeric(
        df["complaints"],
        errors="coerce"
    )

    if "previous_day_complaints" not in df.columns:
        df["previous_day_complaints"] = None

    df["previous_day_complaints"] = pd.to_numeric(
        df["previous_day_complaints"],
        errors="coerce"
    )

    if "percentage_change" not in df.columns:
        df["percentage_change"] = None

    df["percentage_change"] = pd.to_numeric(
        df["percentage_change"],
        errors="coerce"
    )

    if "is_anomaly" not in df.columns:
        df["is_anomaly"] = False

    df["is_anomaly"] = (
        df["is_anomaly"]
        .astype(str)
        .str.lower()
        .isin(["true", "1", "yes"])
    )

    if "anomaly_type" not in df.columns:
        df["anomaly_type"] = "Normal"

    df = df.dropna(
        subset=["date", "complaints"]
    )

    df = df.sort_values("date")

    return df


# ============================================================
# CREATE DAILY ANOMALY GRAPH
# ============================================================

def create_anomaly_graph(
    daily_data,
    threshold=ANOMALY_THRESHOLD
):

    df = prepare_daily_data(daily_data)

    if df.empty:
        return None

    fig = go.Figure()

    # ========================================================
    # DAILY COMPLAINT LINE
    # ========================================================

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["complaints"],
            mode="lines+markers",
            name="Daily Complaints",
            line=dict(width=3),
            marker=dict(size=7),

            customdata=df[
                [
                    "previous_day_complaints",
                    "percentage_change",
                    "is_anomaly",
                    "anomaly_type"
                ]
            ].fillna("—").values,

            hovertemplate=(
                "<b>%{x|%d %b %Y}</b>"
                "<br>Complaints: %{y}"
                "<br>Previous day: %{customdata[0]}"
                "<br>Change: %{customdata[1]}%"
                "<br>Anomaly: %{customdata[2]}"
                "<br>Type: %{customdata[3]}"
                "<extra></extra>"
            )
        )
    )

    # ========================================================
    # ANOMALY POINTS
    # ========================================================

    anomaly_df = df[
        df["is_anomaly"]
    ].copy()

    if not anomaly_df.empty:

        fig.add_trace(
            go.Scatter(
                x=anomaly_df["date"],
                y=anomaly_df["complaints"],
                mode="markers",
                name="Detected Anomaly",

                marker=dict(
                    size=15,
                    symbol="circle"
                ),

                customdata=anomaly_df[
                    [
                        "previous_day_complaints",
                        "percentage_change",
                        "anomaly_type"
                    ]
                ].fillna("—").values,

                hovertemplate=(
                    "<b>⚠️ ANOMALY</b>"
                    "<br>%{x|%d %b %Y}"
                    "<br>Complaints: %{y}"
                    "<br>Previous day: %{customdata[0]}"
                    "<br>Change: %{customdata[1]}%"
                    "<br>Type: %{customdata[2]}"
                    "<extra></extra>"
                )
            )
        )

    # ========================================================
    # GRAPH LAYOUT
    # ========================================================

    fig.update_layout(

        title=(
            "Daily Complaint Trend "
            "with Day-to-Day Anomaly Detection"
        ),

        template="plotly_dark",

        height=560,

        hovermode="closest",

        xaxis=dict(
            title="Date",
            showgrid=True,
            zeroline=False,
            tickformat="%d %b"
        ),

        yaxis=dict(
            title="Complaint Count",
            rangemode="tozero",
            showgrid=True,
            zeroline=False
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),

        margin=dict(
            l=70,
            r=30,
            t=100,
            b=70
        )
    )

    return fig


# ============================================================
# CREATE PERCENTAGE CHANGE GRAPH
# ============================================================

def create_percentage_graph(
    daily_data,
    threshold=ANOMALY_THRESHOLD
):

    df = prepare_daily_data(daily_data)

    if df.empty:
        return None

    change_df = df[
        df["percentage_change"].notna()
    ].copy()

    if change_df.empty:
        return None

    fig = go.Figure()

    # ========================================================
    # DAILY CHANGE %
    # ========================================================

    fig.add_trace(
        go.Scatter(
            x=change_df["date"],
            y=change_df["percentage_change"],
            mode="lines+markers",
            name="Daily Change %",
            line=dict(width=2),
            marker=dict(size=7),

            hovertemplate=(
                "<b>%{x|%d %b %Y}</b>"
                "<br>Change: %{y:.2f}%"
                "<extra></extra>"
            )
        )
    )

    # ========================================================
    # 100%
    # ========================================================

    fig.add_hline(
        y=threshold,
        line_dash="dash",
        annotation_text="+100% Anomaly Limit",
        annotation_position="top right"
    )

    # ========================================================
    # -100%
    # ========================================================

    fig.add_hline(
        y=-threshold,
        line_dash="dash",
        annotation_text="-100% Anomaly Limit",
        annotation_position="bottom right"
    )

    # ========================================================
    # ZERO
    # ========================================================

    fig.add_hline(
        y=0,
        line_dash="dot"
    )

    fig.update_layout(

        title="Daily Complaint Percentage Change",

        template="plotly_dark",

        height=430,

        hovermode="closest",

        xaxis=dict(
            title="Date",
            showgrid=True,
            zeroline=False,
            tickformat="%d %b"
        ),

        yaxis=dict(
            title="Change from Previous Day (%)",
            showgrid=True,
            zeroline=False
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),

        margin=dict(
            l=70,
            r=30,
            t=100,
            b=70
        )
    )

    return fig


# ============================================================
# MAIN ANOMALY DETECTION PAGE
# ============================================================

def show():

    st.title(
        "🚨 Current Complaint Anomaly Detection"
    )

    st.write(
        "Monitor the current daily complaint trend and "
        "identify unusual changes compared with the "
        "immediately previous day."
    )

    st.caption(
        "No future anomaly prediction is performed. "
        "Each day is compared only with the previous day."
    )

    # ========================================================
    # GET DATA
    # ========================================================

    result = get_anomaly_data()

    if result is None:
        return

    if result.get("status") != "success":

        st.warning(
            result.get(
                "message",
                "Insufficient complaint data."
            )
        )

        return

    # ========================================================
    # VALUES
    # ========================================================

    latest_date = result.get(
        "latest_date",
        "—"
    )

    latest_complaints = result.get(
        "latest_complaints",
        0
    )

    previous_day = result.get(
        "previous_day_complaints"
    )

    latest_change = result.get(
        "latest_percentage_change"
    )

    latest_is_anomaly = result.get(
        "latest_is_anomaly",
        False
    )

    latest_anomaly_type = result.get(
        "latest_anomaly_type",
        "Normal"
    )

    anomaly_count = result.get(
        "detected_anomaly_count",
        0
    )

    # ALWAYS USE 100% ANOMALY THRESHOLD
    threshold = ANOMALY_THRESHOLD
    

    daily_data = result.get(
        "historical_data",
        []
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    st.divider()

    st.subheader(
        "📊 Current Complaint Analysis"
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.metric(
            "Latest Date",
            latest_date
        )

    with col2:

        st.metric(
            "Today's Complaints",
            latest_complaints
        )

    with col3:

        st.metric(
            "Previous Day",
            (
                previous_day
                if previous_day is not None
                else "—"
            )
        )

    with col4:

        if latest_change is None:
            change_text = "N/A"
        else:
            change_text = (
                f"{latest_change:+.2f}%"
            )

        st.metric(
            "Day-to-Day Change",
            change_text
        )

    with col5:

        st.metric(
            "Detected Anomalies",
            anomaly_count
        )

    # ========================================================
    # CURRENT STATUS
    # ========================================================

    st.divider()

    if latest_is_anomaly:

        if latest_anomaly_type == "High":

            st.error(
                f"🚨 HIGH ANOMALY — Today's complaint count "
                f"changed by {change_text} compared with "
                f"the previous day."
            )

        else:

            st.error(
                f"🚨 LOW ANOMALY — Today's complaint count "
                f"changed by {change_text} compared with "
                f"the previous day."
            )

    else:

        st.success(
            f"🟢 Complaint activity is within the normal "
            f"day-to-day range ({threshold:.0f}% threshold)."
        )

    # ========================================================
    # DAILY COMPLAINT GRAPH
    # ========================================================

    st.divider()

    st.subheader(
        "📈 Daily Complaint Trend & Anomalies"
    )

    st.caption(
        f"Each day is compared with the immediately "
        f"previous day. A change greater than +{threshold:.0f}% "
        f"or less than -{threshold:.0f}% is marked as an anomaly."
    )

    if daily_data:

        fig = create_anomaly_graph(
            daily_data,
            threshold
        )

        if fig is not None:

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "Unable to generate the complaint trend chart."
            )

    else:

        st.info(
            "No daily complaint data is available."
        )

    # ========================================================
    # PERCENTAGE GRAPH
    # ========================================================

    st.divider()

    st.subheader(
        "📊 Day-to-Day Percentage Change"
    )

    st.caption(
        "The dashed limits show the +100% and -100% "
        "anomaly boundaries."
    )

    if daily_data:

        percentage_fig = create_percentage_graph(
            daily_data,
            threshold
        )

        if percentage_fig is not None:

            st.plotly_chart(
                percentage_fig,
                use_container_width=True
            )

        else:

            st.info(
                "At least two days of complaint data are "
                "required for percentage comparison."
            )

    # ========================================================
    # ANOMALY TABLE
    # ========================================================

    st.divider()

    st.subheader(
        "🚨 Detected Anomalies"
    )

    anomalies = result.get(
        "detected_anomalies",
        []
    )

    if anomalies:

        anomaly_df = pd.DataFrame(
            anomalies
        )

        anomaly_df = anomaly_df.rename(
            columns={
                "date":
                    "Date",

                "complaints":
                    "Complaints",

                "previous_day_complaints":
                    "Previous Day",

                "percentage_change":
                    "Change (%)",

                "anomaly_type":
                    "Type",

                "severity":
                    "Severity",

                "threshold_percent":
                    "Threshold (%)"
            }
        )

        st.dataframe(
            anomaly_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "🟢 No anomalies have been detected in "
            "the available current data."
        )

    # ========================================================
    # DAILY DATA
    # ========================================================

    st.divider()

    st.subheader(
        "📋 Daily Complaint Data"
    )

    if daily_data:

        daily_df = pd.DataFrame(
            daily_data
        )

        daily_df = daily_df.rename(
            columns={
                "date":
                    "Date",

                "complaints":
                    "Complaints",

                "previous_day_complaints":
                    "Previous Day",

                "percentage_change":
                    "Change (%)",

                "is_anomaly":
                    "Anomaly",

                "anomaly_type":
                    "Anomaly Type",

                "severity":
                    "Severity"
            }
        )

        st.dataframe(
            daily_df,
            use_container_width=True,
            hide_index=True
        )

     # ========================================================
    # HOW IT WORKS
    # ========================================================

    st.divider()

    st.subheader(
        "🔍 How Module 9 Works"
    )

    st.markdown(
        f"""
### Day-to-Day Anomaly Detection

The system does **not** predict future anomalies.

Every new day becomes the baseline for the following day.

### Example

**Day 1**
- Complaints = 10
- This is the starting baseline.

**Day 2**
- Complaints = 15
- Previous day = 10
- Change = **+100%**
- Result = 🟢 **Normal**

**Day 3**
- Complaints = 30
- Previous day = 15
- Change = **+100%**
- Result = 🔴 **High Anomaly**

**Day 4**
- Complaints = 12
- Previous day = 30
- Change = **-60%**
- Result = 🔴 **Low Anomaly**

**Day 5**
- Complaints = 15
- Previous day = 12
- Change = **+25%**
- Result = 🟢 **Normal**

### Current Rule

- More than **+{threshold:.0f}%** → 🔴 High Anomaly
- Less than **-{threshold:.0f}%** → 🔴 Low Anomaly
- Between **-{threshold:.0f}% and +{threshold:.0f}%** → 🟢 Normal
- Exactly **+{threshold:.0f}% or -{threshold:.0f}%** → 🟢 Normal

### Important

The system always compares:

**Today's complaints → Previous day's complaints → Percentage change → Anomaly / Normal**

There is **no future prediction**.

The anomaly decision is made only after the new day's complaint count is available.
"""
    )


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    show()
