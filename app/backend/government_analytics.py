import os
import glob
import pickle

import pandas as pd


from app.database.database import supabase, get_all_complaints

# ============================================================
# DASHBOARD SUMMARY
# ============================================================

def get_dashboard_summary():

    complaints = get_all_complaints()

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
            "priority": {
                "low": 0,
                "medium": 0,
                "high": 0
            },
            "departments": {}
        }

    df = pd.DataFrame(complaints)

    # ========================================================
    # TOTAL
    # ========================================================

    total = len(df)

    # ========================================================
    # STATUS
    # ========================================================

    if "status" in df.columns:

        status = (
            df["status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

    else:

        status = pd.Series(
            [""] * len(df)
        )

    submitted = int(
        (status == "submitted").sum()
    )

    assigned = int(
        (status == "assigned").sum()
    )

    under_review = int(
        (status == "under review").sum()
    )

    field_inspection = int(
        (status == "field inspection").sum()
    )

    resolved = int(
        (status == "resolved").sum()
    )

    pending = total - resolved

    # ========================================================
    # EMERGENCY
    # ========================================================

    emergency = 0

    if "emergency" in df.columns:

        emergency_values = (
            df["emergency"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        emergency = int(
            emergency_values.isin(
                [
                    "1",
                    "true",
                    "yes",
                    "emergency"
                ]
            ).sum()
        )

    # ========================================================
    # PRIORITY
    # ========================================================

    priority = {
        "low": 0,
        "medium": 0,
        "high": 0
    }

    if "priority" in df.columns:

        priority_values = (
            df["priority"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        priority["low"] = int(
            (priority_values == "low").sum()
        )

        priority["medium"] = int(
            (priority_values == "medium").sum()
        )

        priority["high"] = int(
            (priority_values == "high").sum()
        )

    # ========================================================
    # DEPARTMENTS
    # ========================================================

    departments = {}

    if "department" in df.columns:

        department_values = (
            df["department"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        department_values = department_values[
            department_values != ""
        ]

        departments = (
            department_values
            .value_counts()
            .to_dict()
        )

        departments = {
            str(department): int(count)
            for department, count
            in departments.items()
        }

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "total_complaints": int(total),

        "pending": int(pending),

        "resolved": int(resolved),

        "emergency": int(emergency),

        "submitted": submitted,

        "assigned": assigned,

        "under_review": under_review,

        "field_inspection": field_inspection,

        "priority": priority,

        "departments": departments
    }


# ============================================================
# COMPLAINT HISTORY
# ============================================================

def get_complaint_history():

    complaints = get_all_complaints()

    if not complaints:

        return pd.DataFrame(
            columns=[
                "date",
                "complaints"
            ]
        )

    df = pd.DataFrame(
        complaints
    )

    if "created_at" not in df.columns:

        return pd.DataFrame(
            columns=[
                "date",
                "complaints"
            ]
        )

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "created_at"
        ]
    )

    df["date"] = (
        df["created_at"]
        .dt.date
    )

    daily_counts = (
        df
        .groupby("date")
        .size()
        .reset_index(
            name="complaints"
        )
    )

    daily_counts = daily_counts.sort_values(
        "date"
    )

    return daily_counts


# ============================================================
# TREND DATA
# ============================================================

def get_trend_data():

    history = get_complaint_history()

    if history.empty:

        return history

    history["date"] = pd.to_datetime(
        history["date"]
    )

    history = history.set_index(
        "date"
    )

    return history


# ============================================================
# LOAD TREND MODEL
# ============================================================

def load_trend_model():

    base_dir = os.path.dirname(
        os.path.dirname(__file__)
    )

    pickle_dir = os.path.join(
        base_dir,
        "pickles"
    )

    model_path = os.path.join(
        pickle_dir,
        "trend_ets_model.pkl"
    )

    if not os.path.exists(
        model_path
    ):

        raise FileNotFoundError(
            f"Trend model not found: "
            f"{model_path}"
        )

    with open(
        model_path,
        "rb"
    ) as file:

        model = pickle.load(
            file
        )

    return model


# ============================================================
# FORECAST
# ============================================================

def get_forecast(
    months=12
):

    model = load_trend_model()

    forecast = model.forecast(
        months
    )

    forecast = forecast.clip(
        lower=0
    )

    return forecast


# ============================================================
# FORECASTING MODEL DEMONSTRATION
# ============================================================

def get_forecast_demonstration():

    """
    Loads the historical dataset and forecast output
    generated by the Module 8 forecasting model.

    This is a model demonstration and is NOT the
    live current complaint forecast.
    """

    # --------------------------------------------------------
    # PROJECT ROOT
    # --------------------------------------------------------

    base_dir = os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    )

    data_dir = os.path.join(
        base_dir,
        "data"
    )

    # --------------------------------------------------------
    # FIND HISTORICAL DATASET
    # --------------------------------------------------------

    csv_files = glob.glob(
        os.path.join(
            data_dir,
            "*.csv"
        )
    )

    historical_candidates = [
        file
        for file in csv_files
        if (
            "trend" in
            os.path.basename(file).lower()
            and
            "historical" in
            os.path.basename(file).lower()
        )
    ]

    if not historical_candidates:

        raise FileNotFoundError(
            "Historical trend dataset was not found "
            "inside the data folder."
        )

    historical_path = (
        historical_candidates[0]
    )

    # --------------------------------------------------------
    # FIND FORECAST OUTPUT
    # --------------------------------------------------------

    forecast_candidates = [
        file
        for file in csv_files
        if (
            "module_08" in
            os.path.basename(file).lower()
            and
            "trend" in
            os.path.basename(file).lower()
        )
    ]

    if not forecast_candidates:

        raise FileNotFoundError(
            "Module 8 trend forecast output was not found "
            "inside the data folder."
        )

    forecast_path = (
        forecast_candidates[0]
    )

    # --------------------------------------------------------
    # LOAD HISTORICAL
    # --------------------------------------------------------

    historical_df = pd.read_csv(
        historical_path
    )

    # Try to identify date column

    historical_date_column = None

    for column in [
        "date",
        "Date",
        "month",
        "Month",
        "created_at"
    ]:

        if column in historical_df.columns:

            historical_date_column = column
            break

    if historical_date_column is None:

        raise ValueError(
            "Could not find date column in historical "
            f"dataset. Columns: "
            f"{historical_df.columns.tolist()}"
        )

    # Try to identify complaint column

    historical_value_column = None

    for column in [
        "complaints",
        "Complaint_Count",
        "complaint_count",
        "count",
        "Count"
    ]:

        if column in historical_df.columns:

            historical_value_column = column
            break

    if historical_value_column is None:

        raise ValueError(
            "Could not find complaint count column in "
            f"historical dataset. Columns: "
            f"{historical_df.columns.tolist()}"
        )

    historical_df["date"] = pd.to_datetime(
        historical_df[
            historical_date_column
        ],
        errors="coerce"
    )

    historical_df["complaints"] = pd.to_numeric(
        historical_df[
            historical_value_column
        ],
        errors="coerce"
    )

    historical_df = historical_df.dropna(
        subset=[
            "date",
            "complaints"
        ]
    )

    historical_df = historical_df.sort_values(
        "date"
    )

    # --------------------------------------------------------
    # LOAD FORECAST
    # --------------------------------------------------------

    forecast_df = pd.read_csv(
        forecast_path
    )

    forecast_date_column = None

    for column in [
        "Date",
        "date",
        "month",
        "Month"
    ]:

        if column in forecast_df.columns:

            forecast_date_column = column
            break

    if forecast_date_column is None:

        raise ValueError(
            "Could not find date column in forecast "
            f"dataset. Columns: "
            f"{forecast_df.columns.tolist()}"
        )

    forecast_value_column = None

    for column in [
        "Forecasted_Complaints",
        "forecasted_complaints",
        "Forecast",
        "forecast",
        "prediction",
        "Predicted"
    ]:

        if column in forecast_df.columns:

            forecast_value_column = column
            break

    if forecast_value_column is None:

        raise ValueError(
            "Could not find forecast value column. "
            f"Columns: "
            f"{forecast_df.columns.tolist()}"
        )

    forecast_df["date"] = pd.to_datetime(
        forecast_df[
            forecast_date_column
        ],
        errors="coerce"
    )

    forecast_df[
        "forecasted_complaints"
    ] = pd.to_numeric(
        forecast_df[
            forecast_value_column
        ],
        errors="coerce"
    )

    forecast_df = forecast_df.dropna(
        subset=[
            "date",
            "forecasted_complaints"
        ]
    )

    forecast_df = forecast_df.sort_values(
        "date"
    )

    # --------------------------------------------------------
    # CONVERT HISTORICAL
    # --------------------------------------------------------

    historical = []

    for _, row in historical_df.iterrows():

        historical.append({

            "date": row[
                "date"
            ].strftime(
                "%Y-%m-%d"
            ),

            "complaints": round(
                float(
                    row["complaints"]
                ),
                2
            )

        })

    # --------------------------------------------------------
    # CONVERT FORECAST
    # --------------------------------------------------------

    forecast = []

    for _, row in forecast_df.iterrows():

        forecast.append({

            "date": row[
                "date"
            ].strftime(
                "%Y-%m-%d"
            ),

            "forecasted_complaints": round(
                float(
                    row[
                        "forecasted_complaints"
                    ]
                ),
                2
            )

        })

    # --------------------------------------------------------
    # FORECAST START
    # --------------------------------------------------------

    forecast_start = None

    if forecast:

        forecast_start = forecast[0]["date"]

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "historical": historical,

        "forecast": forecast,

        "forecast_start": forecast_start
    }


# ============================================================
# ANOMALY DETECTION
# ============================================================

def get_anomaly_detection():

    """
    Government-level anomaly detection.

    This analyzes complaint activity across the dataset
    instead of analyzing one individual complaint.

    Isolation Forest is used to identify unusual
    complaint-volume patterns.
    """

    from sklearn.ensemble import IsolationForest

    # --------------------------------------------------------
    # PROJECT ROOT
    # --------------------------------------------------------

    base_dir = os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    )

    data_dir = os.path.join(
        base_dir,
        "data"
    )

    # --------------------------------------------------------
    # FIND BENGALURU CIVIC DATASET
    # --------------------------------------------------------

    csv_files = glob.glob(
        os.path.join(
            data_dir,
            "*.csv"
        )
    )

    anomaly_files = [
        file
        for file in csv_files
        if (
            "bengaluru" in
            os.path.basename(file).lower()
            and
            "civic" in
            os.path.basename(file).lower()
            and
            "complaint" in
            os.path.basename(file).lower()
        )
    ]

    if not anomaly_files:

        raise FileNotFoundError(
            "Bengaluru civic complaints dataset "
            "was not found inside the data folder."
        )

    dataset_path = anomaly_files[0]

    print(
        "ANOMALY DATASET:",
        dataset_path
    )

    # --------------------------------------------------------
    # LOAD DATASET
    # --------------------------------------------------------

    df = pd.read_csv(
        dataset_path
    )

    print(
        "ANOMALY DATASET COLUMNS:"
    )

    print(
        df.columns.tolist()
    )

    print(
        "NUMBER OF ROWS:",
        len(df)
    )

    # --------------------------------------------------------
    # FIND DATE COLUMN
    # --------------------------------------------------------

    possible_date_columns = [

        "created_at",

        "created_date",

        "date",

        "Date",

        "timestamp",

        "Timestamp",

        "created",

        "Created At",

        "Created_Date",

        "complaint_date",

        "Complaint_Date"

    ]

    date_column = None

    for column in possible_date_columns:

        if column in df.columns:

            date_column = column

            break

    # --------------------------------------------------------
    # IF EXACT COLUMN NOT FOUND,
    # SEARCH COLUMN NAMES
    # --------------------------------------------------------

    if date_column is None:

        for column in df.columns:

            column_lower = (
                str(column)
                .strip()
                .lower()
            )

            if (
                "date" in column_lower
                or
                "time" in column_lower
                or
                "timestamp" in column_lower
            ):

                date_column = column

                break

    # --------------------------------------------------------
    # NO DATE COLUMN
    # --------------------------------------------------------

    if date_column is None:

        raise ValueError(

            "No date column found in anomaly dataset. "

            f"Available columns: "
            f"{df.columns.tolist()}"

        )

    print(
        "ANOMALY DATE COLUMN:",
        date_column
    )

    # --------------------------------------------------------
    # CONVERT DATE
    # --------------------------------------------------------

    df["created_at"] = pd.to_datetime(

        df[date_column],

        format="mixed",

        dayfirst=True,

        errors="coerce"

    )

    # --------------------------------------------------------
    # REMOVE INVALID DATES
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "created_at"
        ]
    )

    print(
        "VALID ANOMALY RECORDS:",
        len(df)
    )

    # --------------------------------------------------------
    # CHECK DATA
    # --------------------------------------------------------

    if df.empty:

        raise ValueError(
            "No valid dates were found in "
            "the anomaly dataset."
        )

    # --------------------------------------------------------
    # DAILY COMPLAINT VOLUME
    # --------------------------------------------------------

    daily = (

        df

        .set_index(
            "created_at"
        )

        .resample("D")

        .size()

        .reset_index(
            name="complaints"
        )

    )

    # --------------------------------------------------------
    # DAY OF WEEK
    # --------------------------------------------------------

    daily["day_of_week"] = (

        daily["created_at"]

        .dt.dayofweek

    )

    # --------------------------------------------------------
    # 7-DAY ROLLING BASELINE
    # --------------------------------------------------------

    daily["rolling_mean"] = (

        daily["complaints"]

        .rolling(

            window=7,

            min_periods=3

        )

        .mean()

    )

    daily["rolling_std"] = (

        daily["complaints"]

        .rolling(

            window=7,

            min_periods=3

        )

        .std()

    )

    # --------------------------------------------------------
    # FILL INITIAL VALUES
    # --------------------------------------------------------

    daily["rolling_mean"] = (

        daily["rolling_mean"]

        .bfill()

    )

    daily["rolling_std"] = (

        daily["rolling_std"]

        .fillna(0)

    )

    # --------------------------------------------------------
    # DEVIATION
    # --------------------------------------------------------

    daily["deviation"] = (

        daily["complaints"]

        - daily["rolling_mean"]

    )

    # --------------------------------------------------------
    # MODEL FEATURES
    # --------------------------------------------------------

    features = daily[

        [

            "complaints",

            "rolling_mean",

            "rolling_std",

            "deviation"

        ]

    ].fillna(0)

    # --------------------------------------------------------
    # ISOLATION FOREST
    # --------------------------------------------------------

    model = IsolationForest(

        n_estimators=200,

        contamination=0.05,

        random_state=42

    )

    daily["model_prediction"] = (

        model.fit_predict(
            features
        )

    )

    # --------------------------------------------------------
    # ANOMALY SCORE
    # --------------------------------------------------------

    daily["anomaly_score"] = (

        -model.score_samples(
            features
        )

    )

    # --------------------------------------------------------
    # ANOMALY FLAG
    # --------------------------------------------------------

    daily["is_anomaly"] = (

        daily["model_prediction"] == -1

    )

    # --------------------------------------------------------
    # SEVERITY
    # --------------------------------------------------------

    daily["severity"] = "Normal"

    daily.loc[
        daily["is_anomaly"],
        "severity"
    ] = "Unusual"

    # Top 5% strongest anomalies

    if daily["is_anomaly"].any():

        threshold = (

            daily.loc[
                daily["is_anomaly"],
                "anomaly_score"
            ]

            .quantile(0.95)

        )

        strong_anomaly = (

            daily["is_anomaly"]

            &

            (
                daily["anomaly_score"]
                >= threshold
            )

        )

        daily.loc[
            strong_anomaly,
            "severity"
        ] = "High"

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_periods = len(
        daily
    )

    anomaly_count = int(
        daily["is_anomaly"].sum()
    )

    normal_count = (

        total_periods

        - anomaly_count

    )

    # --------------------------------------------------------
    # ANOMALY LIST
    # --------------------------------------------------------

    anomaly_rows = daily[
        daily["is_anomaly"]
    ].copy()

    anomaly_rows = anomaly_rows.sort_values(
        "anomaly_score",
        ascending=False
    )

    anomalies = []

    for _, row in anomaly_rows.iterrows():

        anomalies.append({

            "date": row[
                "created_at"
            ].strftime(
                "%Y-%m-%d"
            ),

            "complaints": int(
                row["complaints"]
            ),

            "normal_average": round(

                float(
                    row[
                        "rolling_mean"
                    ]
                ),

                2

            ),

            "anomaly_score": round(

                float(
                    row[
                        "anomaly_score"
                    ]
                ),

                4

            ),

            "severity": row[
                "severity"
            ]

        })

    # --------------------------------------------------------
    # GRAPH DATA
    # --------------------------------------------------------

    graph_data = []

    for _, row in daily.iterrows():

        graph_data.append({

            "date": row[
                "created_at"
            ].strftime(
                "%Y-%m-%d"
            ),

            "complaints": int(
                row["complaints"]
            ),

            "normal_average": round(

                float(
                    row[
                        "rolling_mean"
                    ]
                ),

                2

            ),

            "is_anomaly": bool(
                row["is_anomaly"]
            ),

            "severity": row[
                "severity"
            ]

        })

    # --------------------------------------------------------
    # LATEST STATUS
    # --------------------------------------------------------

    latest = daily.iloc[-1]

    latest_anomaly = bool(
        latest[
            "is_anomaly"
        ]
    )

    if latest_anomaly:

        status = (
            "Anomalous Activity"
        )

    else:

        status = (
            "Normal Activity"
        )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "status": status,

        "latest_date": latest[
            "created_at"
        ].strftime(
            "%Y-%m-%d"
        ),

        "latest_complaints": int(
            latest[
                "complaints"
            ]
        ),

        "total_periods": int(
            total_periods
        ),

        "normal_periods": int(
            normal_count
        ),

        "anomalous_periods": int(
            anomaly_count
        ),

        "graph": graph_data,

        "anomalies": anomalies

    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n=============================="
    )

    print(
        "Government Analytics Test"
    )

    print(
        "=============================="
    )

    print(
        "\nDashboard Summary:"
    )

    print(
        get_dashboard_summary()
    )

    print(
        "\nComplaint History:"
    )

    print(
        get_complaint_history()
    )

    print(
        "\nTesting Forecast:"
    )

    try:

        print(
            get_forecast(12)
        )

    except Exception as e:

        print(
            "Forecast test skipped:",
            e
        )

    print(
        "\nTesting Anomaly Detection:"
    )

    try:

        anomaly_result = (
            get_anomaly_detection()
        )

        print(
            "Anomaly detection loaded successfully!"
        )

        print(
            "Status:",
            anomaly_result[
                "status"
            ]
        )

        print(
            "Periods:",
            anomaly_result[
                "total_periods"
            ]
        )

        print(
            "Anomalies:",
            anomaly_result[
                "anomalous_periods"
            ]
        )

    except Exception as e:

        print(
            "Anomaly detection error:",
            e
        )

    # ============================================================
# SOCIAL MEDIA ANALYSIS
# ============================================================

def get_social_media_analysis():

    import pandas as pd
    from pathlib import Path

    # --------------------------------------------------------
    # DATASET PATHS
    # --------------------------------------------------------

    project_root = Path(__file__).resolve().parents[2]

    sentiment_path = (
        project_root
        / "data"
        / "government_sentiment.csv"
    )

    harmful_path = (
        project_root
        / "data"
        / "harmful_content.csv"
    )

    # --------------------------------------------------------
    # CHECK FILES
    # --------------------------------------------------------

    if not sentiment_path.exists():

        raise FileNotFoundError(
            f"Social media sentiment dataset not found: "
            f"{sentiment_path}"
        )

    if not harmful_path.exists():

        raise FileNotFoundError(
            f"Harmful content dataset not found: "
            f"{harmful_path}"
        )

    # --------------------------------------------------------
    # LOAD SENTIMENT DATA
    # --------------------------------------------------------

    df = pd.read_csv(
        sentiment_path
    )

    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = [
        "sentiment",
        "timestamp",
        "likes",
        "retweets"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in government_sentiment.csv: "
            + ", ".join(missing_columns)
        )

    # --------------------------------------------------------
    # CLEAN SENTIMENT
    # --------------------------------------------------------

    df["sentiment"] = (
        df["sentiment"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp"]
    )

    # --------------------------------------------------------
    # ENGAGEMENT
    # --------------------------------------------------------

    df["likes"] = pd.to_numeric(
        df["likes"],
        errors="coerce"
    ).fillna(0)

    df["retweets"] = pd.to_numeric(
        df["retweets"],
        errors="coerce"
    ).fillna(0)

    df["engagement"] = (
        df["likes"] +
        df["retweets"]
    )

    # ========================================================
    # SENTIMENT SUMMARY
    # ========================================================

    total_posts = len(df)

    sentiment_counts = (
        df["sentiment"]
        .value_counts()
        .to_dict()
    )

    positive_count = int(
        sentiment_counts.get(
            "Positive",
            0
        )
    )

    negative_count = int(
        sentiment_counts.get(
            "Negative",
            0
        )
    )

    neutral_count = int(
        sentiment_counts.get(
            "Neutral",
            0
        )
    )

    def percentage(value):

        if total_posts == 0:
            return 0

        return round(
            (value / total_posts) * 100,
            2
        )

    # ========================================================
    # MONTHLY SENTIMENT TREND
    # ========================================================

    df["month"] = (
        df["timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly_sentiment = (
        df.groupby(
            ["month", "sentiment"]
        )
        .size()
        .reset_index(
            name="count"
        )
    )

    monthly_sentiment_data = []

    for month in sorted(
        df["month"].unique()
    ):

        month_data = (
            monthly_sentiment[
                monthly_sentiment["month"]
                == month
            ]
        )

        counts = {
            "Positive": 0,
            "Negative": 0,
            "Neutral": 0
        }

        for _, row in month_data.iterrows():

            sentiment_name = row["sentiment"]

            if sentiment_name in counts:

                counts[sentiment_name] = int(
                    row["count"]
                )

        monthly_sentiment_data.append(
            {
                "month": month,
                "positive": counts["Positive"],
                "negative": counts["Negative"],
                "neutral": counts["Neutral"]
            }
        )

    # ========================================================
    # MONTHLY ENGAGEMENT TREND
    # ========================================================

    monthly_engagement = (
        df.groupby("month")
        .agg(
            posts=("sentiment", "count"),
            likes=("likes", "sum"),
            retweets=("retweets", "sum"),
            engagement=("engagement", "sum")
        )
        .reset_index()
    )

    monthly_engagement_data = []

    for _, row in monthly_engagement.iterrows():

        monthly_engagement_data.append(
            {
                "month": row["month"],
                "posts": int(row["posts"]),
                "likes": int(row["likes"]),
                "retweets": int(row["retweets"]),
                "engagement": int(row["engagement"])
            }
        )

    # ========================================================
    # ORGANIZATION ANALYSIS
    # ========================================================

    organization_data = []

    if "organization" in df.columns:

        organization_summary = (
            df.groupby("organization")
            .agg(
                posts=("sentiment", "count"),
                engagement=("engagement", "sum")
            )
            .reset_index()
            .sort_values(
                "engagement",
                ascending=False
            )
            .head(20)
        )

        for _, row in organization_summary.iterrows():

            organization_data.append(
                {
                    "organization": str(
                        row["organization"]
                    ),
                    "posts": int(
                        row["posts"]
                    ),
                    "engagement": int(
                        row["engagement"]
                    )
                }
            )

    # ========================================================
    # HARMFUL CONTENT
    # ========================================================

    harmful_df = pd.read_csv(
        harmful_path
    )

    harmful_total = len(
        harmful_df
    )

    harmful_count = 0
    hate_count = 0
    offensive_count = 0

    # --------------------------------------------------------
    # TASK 1 - HARMFUL / OFFENSIVE
    # --------------------------------------------------------

    if "task_1" in harmful_df.columns:

        task_1 = (
            harmful_df["task_1"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        harmful_count = int(
            task_1.isin(
                ["HOF", "HARMFUL", "OFFENSIVE"]
            ).sum()
        )

    # --------------------------------------------------------
    # TASK 2 - HATE
    # --------------------------------------------------------

    if "task_2" in harmful_df.columns:

        task_2 = (
            harmful_df["task_2"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        hate_count = int(
            task_2.isin(
                ["HATE", "HATEFUL"]
            ).sum()
        )

    # --------------------------------------------------------
    # TASK 3 - TARGETED INSULT
    # --------------------------------------------------------

    if "task_3" in harmful_df.columns:

        task_3 = (
            harmful_df["task_3"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        offensive_count = int(
            task_3.isin(
                [
                    "TIN",
                    "TARGETED_INSULT",
                    "OFFENSIVE"
                ]
            ).sum()
        )

    harmful_percentage = 0

    if harmful_total > 0:

        harmful_percentage = round(
            (
                harmful_count
                / harmful_total
            ) * 100,
            2
        )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "status": "success",

        "total_posts": total_posts,

        "sentiment": {

            "positive": positive_count,

            "negative": negative_count,

            "neutral": neutral_count,

            "positive_percentage": percentage(
                positive_count
            ),

            "negative_percentage": percentage(
                negative_count
            ),

            "neutral_percentage": percentage(
                neutral_count
            )
        },

        "engagement": {

            "total_likes": int(
                df["likes"].sum()
            ),

            "total_retweets": int(
                df["retweets"].sum()
            ),

            "total_engagement": int(
                df["engagement"].sum()
            )
        },

        "sentiment_trend":
            monthly_sentiment_data,

        "engagement_trend":
            monthly_engagement_data,

        "organization_analysis":
            organization_data,

        "harmful_content": {

            "total_analyzed":
                harmful_total,

            "harmful_count":
                harmful_count,

            "harmful_percentage":
                harmful_percentage,

            "hate_count":
                hate_count,

            "offensive_count":
                offensive_count
        },

        "note": (
            "Sentiment and harmful-content results "
            "are based on the historical datasets "
            "used by this module. The system does not "
            "determine the exact reason for a sentiment "
            "classification unless supported by the "
            "underlying trained model and dataset."
        )
    }

# ============================================================
# SOCIAL MEDIA ENGAGEMENT FORECASTING
# ============================================================

def get_social_media_forecast(months=6):

    import pandas as pd
    import numpy as np
    from pathlib import Path
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    # ========================================================
    # FORECAST HORIZON
    # ========================================================

    try:
        months = int(months)
    except:
        months = 6

    # Only allow 1 month or 6 months
    if months not in [1, 6]:
        months = 6

    # ========================================================
    # DATASET
    # ========================================================

    project_root = Path(
        __file__
    ).resolve().parents[2]

    dataset_path = (
        project_root
        / "data"
        / "government_sentiment.csv"
    )

    if not dataset_path.exists():

        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    # ========================================================
    # READ DATA
    # ========================================================

    df = pd.read_csv(
        dataset_path
    )

    # ========================================================
    # CHECK COLUMNS
    # ========================================================

    required_columns = [
        "timestamp",
        "likes",
        "retweets"
    ]

    for column in required_columns:

        if column not in df.columns:

            raise ValueError(
                f"Missing column: {column}"
            )

    # ========================================================
    # CLEAN DATE
    # ========================================================

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp"]
    )

    # ========================================================
    # CLEAN LIKES
    # ========================================================

    df["likes"] = pd.to_numeric(
        df["likes"],
        errors="coerce"
    ).fillna(0)

    # ========================================================
    # CLEAN RETWEETS
    # ========================================================

    df["retweets"] = pd.to_numeric(
        df["retweets"],
        errors="coerce"
    ).fillna(0)

    # ========================================================
    # TOTAL ENGAGEMENT
    # ========================================================

    df["engagement"] = (
        df["likes"]
        + df["retweets"]
    )

    # ========================================================
    # MONTH
    # ========================================================

    df["month"] = (
        df["timestamp"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    # ========================================================
    # MONTHLY DATA
    # ========================================================

    monthly_df = (

        df.groupby(
            "month",
            as_index=False
        )

        .agg(
            engagement=(
                "engagement",
                "sum"
            ),

            posts=(
                "engagement",
                "count"
            )
        )

        .sort_values(
            "month"
        )

        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # CHECK DATA
    # ========================================================

    if len(monthly_df) < 6:

        raise ValueError(
            "Not enough historical data "
            "for forecasting."
        )

    # ========================================================
    # LAST HISTORICAL MONTH
    # ========================================================

    last_historical_month = (
        monthly_df["month"].max()
    )

    # ========================================================
    # HISTORICAL DATA
    # ========================================================

    historical_data = []

    for _, row in monthly_df.iterrows():

        historical_data.append({

            "date":
                row["month"].strftime(
                    "%Y-%m-%d"
                ),

            "engagement":
                round(
                    float(
                        row["engagement"]
                    ),
                    2
                ),

            "type":
                "historical"
        })

    # ========================================================
    # FORECAST START
    # ========================================================

    forecast_start = (
        last_historical_month
        + pd.offsets.MonthBegin(1)
    )

    # ========================================================
    # FORECAST DATES
    #
    # If history ends May 2023:
    #
    # June 2023
    # July 2023
    # August 2023
    # September 2023
    # October 2023
    # November 2023
    #
    # ========================================================

    future_dates = pd.date_range(

        start=forecast_start,

        periods=months,

        freq="MS"
    )

    # ========================================================
    # TRAINING DATA
    #
    # Ignore zero engagement months when training.
    #
    # They remain visible in the historical graph.
    # ========================================================

    training = monthly_df.loc[
        monthly_df["engagement"] > 0,
        "engagement"
    ]

    training = (
        training
        .astype(float)
        .reset_index(
            drop=True
        )
    )

    if len(training) < 3:

        raise ValueError(
            "Not enough positive engagement "
            "months for forecasting."
        )

    # ========================================================
    # HOLT DAMPED TREND MODEL
    # ========================================================

    model = ExponentialSmoothing(

        training,

        trend="add",

        damped_trend=True,

        seasonal=None,

        initialization_method="estimated"

    ).fit(
        optimized=True
    )

    # ========================================================
    # PREDICTION
    # ========================================================

    predictions = model.forecast(
        months
    )

    predictions = np.asarray(
        predictions,
        dtype=float
    )

    # Prevent negative predictions

    predictions = np.maximum(
        predictions,
        0
    )

    # ========================================================
    # FORECAST DATA
    # ========================================================

    forecast_data = []

    for date, prediction in zip(
        future_dates,
        predictions
    ):

        forecast_data.append({

            "date":
                date.strftime(
                    "%Y-%m-%d"
                ),

            "engagement":
                round(
                    float(
                        prediction
                    ),
                    2
                ),

            "type":
                "forecast"
        })

    # ========================================================
    # COMBINED DATA
    # ========================================================

    combined_data = (
        historical_data
        + forecast_data
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    average_forecast = float(
        np.mean(
            predictions
        )
    )

    peak_forecast = float(
        np.max(
            predictions
        )
    )

    lowest_forecast = float(
        np.min(
            predictions
        )
    )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "status":
            "success",

        "forecast_type":
            "Monthly Social Media Engagement",

        "forecast_months":
            months,

        "forecast_period":
            f"{months}-month forecast",

        "historical_start":
            monthly_df["month"]
            .min()
            .strftime(
                "%Y-%m-%d"
            ),

        "historical_end":
            last_historical_month
            .strftime(
                "%Y-%m-%d"
            ),

        "forecast_start":
            future_dates[0]
            .strftime(
                "%Y-%m-%d"
            ),

        "forecast_end":
            future_dates[-1]
            .strftime(
                "%Y-%m-%d"
            ),

        "forecast_summary": {

            "average":
                round(
                    average_forecast,
                    2
                ),

            "peak":
                round(
                    peak_forecast,
                    2
                ),

            "lowest":
                round(
                    lowest_forecast,
                    2
                )
        },

        "historical_data":
            historical_data,

        "forecast_data":
            forecast_data,

        "combined_data":
            combined_data,

        "note":
            (
                "Historical engagement is "
                "calculated from likes and "
                "retweets. Forecast uses a "
                "short-term damped trend model."
            )
    }

# ============================================================
# CURRENT DAILY ANOMALY DETECTION
# ============================================================

def get_current_anomaly_detection():
    """
    Module 9 - Current Daily Complaint Anomaly Detection.

    Each day is compared ONLY with the immediately previous day.

    Anomaly rule:
        More than +50%  -> High anomaly
        Less than -50%  -> Low anomaly
        Exactly +/-50%  -> Normal
        Between +/-50%  -> Normal

    No forecasting, 3-day baseline, or Isolation Forest is used here.
    """

    import pandas as pd

    ANOMALY_THRESHOLD = 100.0
    RECENT_DAYS = 30

    complaints = get_all_complaints()

    empty_result = {
        "status": "insufficient_data",
        "analysis_type": "Current Daily Complaint Anomaly Detection",
        "anomaly_rule": "More than +50% or less than -50% change from the previous day",
        "threshold_percent": ANOMALY_THRESHOLD,
        "latest_date": None,
        "latest_complaints": 0,
        "previous_day_complaints": None,
        "latest_percentage_change": None,
        "latest_is_anomaly": False,
        "latest_anomaly_type": "No Data",
        "latest_severity": "Normal",
        "detected_anomaly_count": 0,
        "detection_status": "No Data",
        "historical_data": [],
        "detected_anomalies": []
    }

    if not complaints:
        empty_result["message"] = "No complaints are available."
        return empty_result

    df = pd.DataFrame(complaints)

    if "created_at" not in df.columns:
        empty_result["message"] = "Complaint records do not contain created_at."
        return empty_result

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.dropna(subset=["created_at"])

    if df.empty:
        empty_result["message"] = "No valid complaint dates were found."
        return empty_result

    daily = (
        df.set_index("created_at")
        .resample("D")
        .size()
        .reset_index(name="complaints")
        .sort_values("created_at")
    )

    if len(daily) > RECENT_DAYS:
        daily = daily.tail(RECENT_DAYS).copy()

    # Add missing calendar days as zero-complaint days.
    daily = daily.set_index("created_at")
    full_range = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = (
        daily.reindex(full_range, fill_value=0)
        .rename_axis("created_at")
        .reset_index()
    )

    historical_data = []
    detected_anomalies = []

    for index in range(len(daily)):
        current_date = daily.iloc[index]["created_at"]
        current_count = int(daily.iloc[index]["complaints"])

        if index == 0:
            historical_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "complaints": current_count,
                "previous_day_complaints": None,
                "percentage_change": None,
                "is_anomaly": False,
                "anomaly_type": "Baseline",
                "severity": "Normal"
            })
            continue

        previous_count = int(daily.iloc[index - 1]["complaints"])
        percentage_change = None
        is_anomaly = False
        anomaly_type = "Normal"
        severity = "Normal"

        if previous_count == 0:
            if current_count > 0:
                # Percentage change from zero is mathematically undefined.
                # A new positive complaint count after zero is treated as a high anomaly.
                is_anomaly = True
                anomaly_type = "High"
                severity = "High"
            else:
                percentage_change = 0.0
        else:
            percentage_change = ((current_count - previous_count) / previous_count) * 100

            if percentage_change > ANOMALY_THRESHOLD:
                is_anomaly = True
                anomaly_type = "High"
                severity = "High"
            elif percentage_change < -ANOMALY_THRESHOLD:
                is_anomaly = True
                anomaly_type = "Low"
                severity = "High"

        change_value = round(percentage_change, 2) if percentage_change is not None else None

        record = {
            "date": current_date.strftime("%Y-%m-%d"),
            "complaints": current_count,
            "previous_day_complaints": previous_count,
            "percentage_change": change_value,
            "is_anomaly": bool(is_anomaly),
            "anomaly_type": anomaly_type,
            "severity": severity
        }
        historical_data.append(record)

        if is_anomaly:
            detected_anomalies.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "complaints": current_count,
                "previous_day_complaints": previous_count,
                "percentage_change": change_value,
                "anomaly_type": anomaly_type,
                "severity": severity,
                "threshold_percent": ANOMALY_THRESHOLD
            })

    latest = daily.iloc[-1]
    latest_date = latest["created_at"].strftime("%Y-%m-%d")
    latest_complaints = int(latest["complaints"])

    previous_day_complaints = None
    latest_percentage_change = None
    latest_is_anomaly = False
    latest_anomaly_type = "Baseline"
    latest_severity = "Normal"

    if len(daily) > 1:
        previous_day_complaints = int(daily.iloc[-2]["complaints"])

        if previous_day_complaints == 0:
            if latest_complaints > 0:
                latest_is_anomaly = True
                latest_anomaly_type = "High"
                latest_severity = "High"
            else:
                latest_percentage_change = 0.0
                latest_anomaly_type = "Normal"
        else:
            latest_percentage_change = (
                (latest_complaints - previous_day_complaints)
                / previous_day_complaints
            ) * 100

            if latest_percentage_change > ANOMALY_THRESHOLD:
                latest_is_anomaly = True
                latest_anomaly_type = "High"
                latest_severity = "High"
            elif latest_percentage_change < -ANOMALY_THRESHOLD:
                latest_is_anomaly = True
                latest_anomaly_type = "Low"
                latest_severity = "High"
            else:
                latest_anomaly_type = "Normal"

    if latest_percentage_change is not None:
        latest_percentage_change = round(latest_percentage_change, 2)

    return {
        "status": "success",
        "analysis_type": "Current Daily Complaint Anomaly Detection",
        "anomaly_rule": "More than +50% or less than -50% change from the previous day",
        "threshold_percent": ANOMALY_THRESHOLD,
        "latest_date": latest_date,
        "latest_complaints": latest_complaints,
        "previous_day_complaints": previous_day_complaints,
        "latest_percentage_change": latest_percentage_change,
        "latest_is_anomaly": bool(latest_is_anomaly),
        "latest_anomaly_type": latest_anomaly_type,
        "latest_severity": latest_severity,
        "detected_anomaly_count": len(detected_anomalies),
        "detection_status": "Anomaly Detected" if latest_is_anomaly else "Normal",
        "historical_data": historical_data,
        "detected_anomalies": detected_anomalies
    }
