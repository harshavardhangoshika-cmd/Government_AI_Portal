import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "https://government-ai-api.onrender.com/government/social-media"

FORECAST_API_URL = (
    "https://government-ai-api.onrender.com/government/social-media/forecast"
)


# ============================================================
# LOAD SOCIAL MEDIA DATA FROM BACKEND
# ============================================================

def load_social_media_data():

    try:

        response = requests.get(
            API_URL,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            "Unable to connect to the Social Media Analysis API."
        )

        st.code(str(e))

        return None

    except Exception as e:

        st.error(
            "Unable to load Social Media Analysis."
        )

        st.code(str(e))

        return None


# ============================================================
# LOAD SOCIAL MEDIA FORECAST FROM BACKEND
# ============================================================

def load_social_media_forecast():

    try:

        response = requests.get(
            FORECAST_API_URL,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            "Unable to connect to the Social Media Forecast API."
        )

        st.code(str(e))

        return None

    except Exception as e:

        st.error(
            "Unable to load Social Media Forecast."
        )

        st.code(str(e))

        return None


# ============================================================
# MAIN PAGE
# ============================================================

def show():

    st.title(
        "📱 Social Media Analysis"
    )

    st.caption(
        "Analysis of government-related social media sentiment, "
        "engagement and harmful-content activity."
    )

    st.divider()


    # ========================================================
    # LOAD DATA
    # ========================================================

    data = load_social_media_data()

    if data is None:

        return

    if data.get("status") != "success":

        st.error(
            "Social Media Analysis data is unavailable."
        )

        return


    # ========================================================
    # EXTRACT DATA
    # ========================================================

    total_posts = data.get(
        "total_posts",
        0
    )

    sentiment = data.get(
        "sentiment",
        {}
    )

    engagement = data.get(
        "engagement",
        {}
    )

    harmful = data.get(
        "harmful_content",
        {}
    )

    sentiment_trend = data.get(
        "sentiment_trend",
        []
    )

    organization_data = data.get(
        "organization_analysis",
        []
    )


    # ========================================================
    # SUMMARY CARDS
    # ========================================================

    st.subheader(
        "📊 Social Media Overview"
    )

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Total Posts / Comments",
            f"{total_posts:,}"
        )


    with col2:

        st.metric(
            "Positive",
            f"{sentiment.get('positive_percentage', 0)}%"
        )

        st.caption(
            f"{sentiment.get('positive', 0):,} posts"
        )


    with col3:

        st.metric(
            "Negative",
            f"{sentiment.get('negative_percentage', 0)}%"
        )

        st.caption(
            f"{sentiment.get('negative', 0):,} posts"
        )


    with col4:

        st.metric(
            "Neutral",
            f"{sentiment.get('neutral_percentage', 0)}%"
        )

        st.caption(
            f"{sentiment.get('neutral', 0):,} posts"
        )


    st.divider()


    # ========================================================
    # SENTIMENT TREND
    # ========================================================

    st.subheader(
        "📈 Sentiment Trend"
    )


    if sentiment_trend:

        sentiment_df = pd.DataFrame(
            sentiment_trend
        )

        if "month" in sentiment_df.columns:

            sentiment_df["month"] = pd.to_datetime(
                sentiment_df["month"],
                errors="coerce"
            )

            sentiment_df = sentiment_df.dropna(
                subset=["month"]
            )

            sentiment_df = sentiment_df.sort_values(
                "month"
            )

            fig = go.Figure()


            # POSITIVE
            if "positive" in sentiment_df.columns:

                fig.add_trace(
                    go.Scatter(
                        x=sentiment_df["month"],
                        y=sentiment_df["positive"],
                        mode="lines+markers",
                        name="Positive"
                    )
                )


            # NEGATIVE
            if "negative" in sentiment_df.columns:

                fig.add_trace(
                    go.Scatter(
                        x=sentiment_df["month"],
                        y=sentiment_df["negative"],
                        mode="lines+markers",
                        name="Negative"
                    )
                )


            # NEUTRAL
            if "neutral" in sentiment_df.columns:

                fig.add_trace(
                    go.Scatter(
                        x=sentiment_df["month"],
                        y=sentiment_df["neutral"],
                        mode="lines+markers",
                        name="Neutral"
                    )
                )


            fig.update_layout(

                title="Monthly Social Media Sentiment",

                xaxis_title="Date",

                yaxis_title="Number of Posts / Comments",

                hovermode="x unified",

                height=450,

                margin=dict(
                    l=60,
                    r=30,
                    t=70,
                    b=60
                )
            )


            st.plotly_chart(
                fig,
                use_container_width=True
            )


    else:

        st.info(
            "No sentiment trend data available."
        )


    st.divider()


    # ========================================================
    # ENGAGEMENT SUMMARY
    # ========================================================
    #
    # NOTE: The historical engagement trend itself is not
    # charted separately here anymore. It is shown once,
    # combined with the forecast, in the "Social Media
    # Engagement Future Prediction" section below — plotting
    # the same historical series twice on this page was
    # redundant.

    st.subheader(
        "📢 Government Social Media Engagement"
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Total Likes",
            f"{engagement.get('total_likes', 0):,}"
        )


    with col2:

        st.metric(
            "Total Retweets",
            f"{engagement.get('total_retweets', 0):,}"
        )


    with col3:

        st.metric(
            "Total Engagement",
            f"{engagement.get('total_engagement', 0):,}"
        )


    st.info(
        """
        Engagement represents the available interaction data
        in the historical dataset, calculated from likes and
        retweets. It should not be interpreted as total reach
        or impressions because the dataset does not contain
        reach/impression measurements.

        The month-by-month engagement trend is shown below,
        alongside the forecast.
        """
    )


    st.divider()


    # ========================================================
    # SOCIAL MEDIA ENGAGEMENT FORECAST
    # ========================================================

    st.subheader(
        "🔮 Social Media Engagement Future Prediction"
    )

    st.caption(
        "Monthly historical engagement followed by a 6-month "
        "model-based forecast continuing after the historical period."
    )

    forecast_data = load_social_media_forecast()

    if (
        forecast_data
        and forecast_data.get("status") == "success"
    ):

        historical_data = forecast_data.get(
            "historical_data",
            []
        )

        future_data = forecast_data.get(
            "forecast_data",
            []
        )

        if historical_data and future_data:

            historical_df = pd.DataFrame(
                historical_data
            )

            forecast_df = pd.DataFrame(
                future_data
            )

            # ------------------------------------------------
            # CONVERT DATES
            # ------------------------------------------------

            historical_df["date"] = pd.to_datetime(
                historical_df["date"],
                errors="coerce"
            )

            forecast_df["date"] = pd.to_datetime(
                forecast_df["date"],
                errors="coerce"
            )

            historical_df = historical_df.dropna(
                subset=["date"]
            )

            forecast_df = forecast_df.dropna(
                subset=["date"]
            )

            # ------------------------------------------------
            # SORT DATA
            # ------------------------------------------------

            historical_df = historical_df.sort_values(
                "date"
            )

            forecast_df = forecast_df.sort_values(
                "date"
            )

            # ------------------------------------------------
            # CREATE FORECAST FIGURE
            # ------------------------------------------------

            forecast_fig = go.Figure()

            # =================================================
            # HISTORICAL MONTHLY ENGAGEMENT
            # =================================================

            forecast_fig.add_trace(
                go.Scatter(
                    x=historical_df["date"],
                    y=historical_df["engagement"],
                    mode="lines+markers",
                    name="Historical Engagement",
                    line=dict(width=2),
                    marker=dict(size=5),
                    hovertemplate=(
                        "<b>%{x|%b %Y}</b>"
                        "<br>Historical Engagement: "
                        "%{y:,.0f}"
                        "<extra></extra>"
                    )
                )
            )

            # =================================================
            # FORECAST MONTHLY ENGAGEMENT
            # =================================================

            forecast_fig.add_trace(
                go.Scatter(
                    x=forecast_df["date"],
                    y=forecast_df["engagement"],
                    mode="lines+markers",
                    name="Forecast",
                    line=dict(
                        width=3,
                        dash="dash"
                    ),
                    marker=dict(size=6),
                    hovertemplate=(
                        "<b>%{x|%b %Y}</b>"
                        "<br>Forecast Engagement: "
                        "%{y:,.0f}"
                        "<extra></extra>"
                    )
                )
            )

            # =================================================
            # FORECAST START
            # =================================================

            forecast_start = forecast_df[
                "date"
            ].iloc[0]

            forecast_fig.add_shape(
                type="line",
                x0=forecast_start,
                x1=forecast_start,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(
                    width=2,
                    dash="dash"
                )
            )

            forecast_fig.add_annotation(
                x=forecast_start,
                y=1,
                yref="paper",
                text="Forecast Start",
                showarrow=False,
                yshift=15
            )

            # =================================================
            # GRAPH LAYOUT
            # =================================================

            forecast_fig.update_layout(
                title=(
                    "Historical and Forecasted "
                    "Monthly Social Media Engagement"
                ),
                xaxis_title="Date",
                yaxis_title=(
                    "Engagement "
                    "(Likes + Retweets)"
                ),
                hovermode="x unified",
                height=520,
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
                    t=90,
                    b=70
                )
            )

            st.plotly_chart(
                forecast_fig,
                use_container_width=True
            )

            # =================================================
            # FORECAST SUMMARY
            # =================================================

            st.subheader(
                "📊 Forecast Summary"
            )

            summary = forecast_data.get(
                "forecast_summary",
                {}
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Average Forecast",
                    f"{summary.get('average', 0):,.0f}"
                )

            with col2:
                st.metric(
                    "Peak Forecast",
                    f"{summary.get('peak', 0):,.0f}"
                )

            with col3:
                st.metric(
                    "Lowest Forecast",
                    f"{summary.get('lowest', 0):,.0f}"
                )

            # =================================================
            # FORECAST PERIOD
            # =================================================

            forecast_start_text = forecast_data.get(
                "forecast_start",
                ""
            )

            forecast_end_text = forecast_data.get(
                "forecast_end",
                ""
            )

            st.info(
                f"""
                **Forecast Period:** {forecast_start_text}
                to {forecast_end_text}

                The solid line represents historical monthly
                social-media engagement. The dashed line represents
                the 6-month forecast immediately following the
                historical period.

                Engagement represents likes + retweets, not reach
                or impressions.
                """
            )

            st.warning(
                """
                **Forecasting Demonstration**

                The historical data is aggregated by month from
                likes and retweets. The forecast is generated from
                the historical monthly engagement trend and is
                intended to demonstrate the forecasting workflow.
                It should not be interpreted as live social-media
                reach or impressions.

                Because the model (damped Exponential Smoothing)
                forecasts from the overall trend rather than only
                the most recent month, the forecast can differ
                noticeably from a single low or zero-valued month
                immediately before the forecast start.
                """
            )

        else:
            st.info(
                "No sufficient data available for social-media forecasting."
            )

    else:
        st.info(
            "Social-media forecast is currently unavailable."
        )

    st.divider()


    # ========================================================
    # HARMFUL CONTENT
    # ========================================================

    st.subheader(
        "⚠️ Harmful Content Monitoring"
    )


    harmful_total = harmful.get(
        "total_analyzed",
        0
    )


    harmful_count = harmful.get(
        "harmful_count",
        0
    )


    harmful_percentage = harmful.get(
        "harmful_percentage",
        0
    )


    hate_count = harmful.get(
        "hate_count",
        0
    )


    offensive_count = harmful.get(
        "offensive_count",
        0
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Analyzed Content",
            f"{harmful_total:,}"
        )


    with col2:

        st.metric(
            "Harmful Content",
            f"{harmful_percentage}%"
        )

        st.caption(
            f"{harmful_count:,} records"
        )


    with col3:

        st.metric(
            "Hate Content",
            f"{hate_count:,}"
        )


    with col4:

        st.metric(
            "Offensive / Targeted",
            f"{offensive_count:,}"
        )


    # ========================================================
    # HARMFUL CONTENT VISUAL
    # ========================================================

    if harmful_total > 0:

        safe_count = max(
            harmful_total - harmful_count,
            0
        )


        harmful_fig = go.Figure(

            data=[

                go.Pie(

                    labels=[
                        "Non-Harmful",
                        "Harmful"
                    ],

                    values=[
                        safe_count,
                        harmful_count
                    ],

                    hole=0.55
                )
            ]
        )


        harmful_fig.update_layout(

            title=(
                "Historical Harmful Content Distribution"
            ),

            height=400
        )


        st.plotly_chart(
            harmful_fig,
            use_container_width=True
        )


    st.divider()


    # ========================================================
    # ORGANIZATION ANALYSIS
    # ========================================================

    if organization_data:

        st.subheader(
            "🏛️ Organization Engagement"
        )


        organization_df = pd.DataFrame(
            organization_data
        )


        if not organization_df.empty:

            st.dataframe(

                organization_df,

                use_container_width=True,

                hide_index=True
            )


    st.divider()


    # ========================================================
    # INTERPRETATION
    # ========================================================

    st.subheader(
        "💡 Social Media Insights"
    )


    positive_percentage = sentiment.get(
        "positive_percentage",
        0
    )


    negative_percentage = sentiment.get(
        "negative_percentage",
        0
    )


    neutral_percentage = sentiment.get(
        "neutral_percentage",
        0
    )


    # --------------------------------------------------------
    # SENTIMENT INTERPRETATION
    # --------------------------------------------------------

    if positive_percentage > negative_percentage:

        st.success(

            f"Positive sentiment currently represents "
            f"{positive_percentage}% of the analyzed content, "
            f"which is higher than negative sentiment "
            f"at {negative_percentage}%."
        )


    elif negative_percentage > positive_percentage:

        st.warning(

            f"Negative sentiment currently represents "
            f"{negative_percentage}% of the analyzed content, "
            f"which is higher than positive sentiment "
            f"at {positive_percentage}%."
        )


    else:

        st.info(
            "Positive and negative sentiment are currently "
            "at similar levels."
        )


    # --------------------------------------------------------
    # NEUTRAL SENTIMENT
    # --------------------------------------------------------

    st.write(

        f"Neutral content represents "
        f"{neutral_percentage}% of the analyzed dataset."
    )


    # --------------------------------------------------------
    # ENGAGEMENT
    # --------------------------------------------------------

    st.write(

        "Government officials can monitor the engagement "
        "trend to identify periods where social-media "
        "interaction is increasing or declining."
    )


    # --------------------------------------------------------
    # HARMFUL CONTENT
    # --------------------------------------------------------

    st.write(

        f"Approximately {harmful_percentage}% of the "
        "analyzed harmful-content dataset is classified "
        "as harmful according to the available dataset "
        "labels."
    )


    # ========================================================
    # IMPORTANT NOTE
    # ========================================================

    st.info(
        """
        **Analysis Note**

        The displayed results are generated from the
        historical social-media datasets used to train
        and demonstrate this module.

        Sentiment classification indicates whether content
        is positive, negative or neutral. It does not by
        itself determine the exact reason for that sentiment.

        Engagement is calculated from available likes and
        retweets. The dataset does not provide actual reach
        or impression measurements.

        Harmful-content results are based on the labels
        available in the harmful-content dataset.

        The engagement forecast is a demonstration based
        on the historical dataset and should not be
        interpreted as a live measurement of current
        social-media reach.
        """
    )


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    show()
