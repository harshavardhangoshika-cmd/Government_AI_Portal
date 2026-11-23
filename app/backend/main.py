from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os

from typing import Optional, List
from datetime import datetime, timezone, timedelta

from app.backend.predict import process_complaint

try:
    from app.dl.image_classification.predict_image import classify_image
except ImportError:
    classify_image = None

from app.backend.government_analytics import (
    get_dashboard_summary,
    get_complaint_history,
    get_forecast,
    get_forecast_demonstration,
    get_anomaly_detection
)

from app.database.database import (
    save_complaint,
    get_complaint_by_number,
    get_all_complaints,
    update_complaint_status
)

from app.utils.sla_engine import compute_sla

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Government Complaint AI",
    version="1.0"
)

# Enable CORS for Streamlit Cloud and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_probe():
    return {
        "status": "healthy",
        "service": "Government Complaint AI Backend",
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================================
# PYDANTIC MODELS
# ============================================================

class Complaint(BaseModel):
    text: str
    state: Optional[str] = "Karnataka"
    district: Optional[str] = "Bengaluru Urban"


class StatusUpdateRequest(BaseModel):
    complaint_number: str
    status: str
    assigned_officer: Optional[str] = None
    officer_remarks: Optional[str] = None
    department: Optional[str] = None
    priority: Optional[str] = None


class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3


# ============================================================
# HELPER: SLA ENGINE
# ============================================================
# Imported from app.utils.sla_engine


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Government Complaint AI API is Running"
    }


# ============================================================
# DL CIVIC IMAGE CLASSIFICATION (7 CLASSES)
# ============================================================

@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...)):
    """
    Classifies an uploaded civic issue photo into one of 7 municipal categories:
    1. road_damage
    2. garbage
    3. streetlights
    4. water_supply
    5. electricity
    6. traffic_safety
    7. sewerage

    Returns predicted class, confidence, suggested department, SLA, and priority.
    """
    if classify_image is None:
        return {"error": "Image classification model not loaded."}

    try:
        contents = await file.read()
        res = classify_image(contents)
        return res
    except Exception as e:
        return {"error": f"Image classification failed: {str(e)}"}


# ============================================================
# CIVIC RAG KNOWLEDGE BASE QUERY
# ============================================================

@app.post("/rag/query")
def rag_query(request: RAGQueryRequest):
    """
    Retrieval-Augmented Generation endpoint providing authoritative answers
    to citizen queries on municipal bylaws, SLAs, schemes, and rights.
    """
    try:
        from app.rag.rag_service import ask_civic_rag
        res = ask_civic_rag(request.query, top_k=request.top_k or 3)
        return res
    except Exception as e:
        return {"error": f"RAG query processing failed: {str(e)}"}


# ============================================================
# AI PREDICTION + SAVE COMPLAINT
# ============================================================

@app.post("/predict")
def predict(data: Complaint):

    # --------------------------------------------------------
    # Run existing AI models
    # --------------------------------------------------------

    result = process_complaint(
        data.text
    )


    # --------------------------------------------------------
    # Save complaint + AI predictions (with offline resilience)
    # --------------------------------------------------------

    try:
        saved_complaint = save_complaint(
            complaint_text=data.text,
            sentiment=result.get("sentiment"),
            feedback_category=result.get("feedback_category"),
            complaint_reason=result.get("complaint_reason"),
            department=result.get("department"),
            harmful=(result.get("harmful_content") == "Harmful"),
            emergency=result.get("emergency"),
            priority=result.get("priority"),
            recommended_schemes=result.get("recommended_schemes"),
            state=data.state,
            district=data.district
        )

        result["complaint_id"] = saved_complaint.get("id")
        result["complaint_number"] = saved_complaint.get("complaint_number")
        result["storage_status"] = "persisted_in_database"
        result["storage_error"] = None

    except Exception as db_err:
        # Gracefully handle database or network connectivity failures
        # without crashing the ML prediction response
        offline_num = f"OFFLINE-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        result["complaint_id"] = None
        result["complaint_number"] = offline_num
        result["storage_status"] = "offline_database_unavailable"
        result["storage_error"] = str(db_err)

    return result


# ============================================================
# TRACK COMPLAINT
# ============================================================

@app.get(
    "/track/{complaint_number}"
)
def track_complaint(
    complaint_number: str
):

    complaint = get_complaint_by_number(
        complaint_number
    )


    if complaint is None:

        return {
            "error": "Complaint not found"
        }


    return {

        "complaint_number":
            complaint.get(
                "complaint_number"
            ),

        "status":
            complaint.get(
                "status"
            ),

        "department":
            complaint.get(
                "department"
            ),

        "complaint_reason":
            complaint.get(
                "complaint_reason"
            ),

        "assigned_officer":
            complaint.get(
                "assigned_officer"
            ),

        "officer_remarks":
            complaint.get(
                "officer_remarks"
            ),

        "created_at":
            complaint.get(
                "created_at"
            ),

        "updated_at":
            complaint.get(
                "updated_at"
            )
    }


# ============================================================
# GOVERNMENT DASHBOARD
# ============================================================

@app.get(
    "/government/dashboard"
)
def government_dashboard():

    return get_dashboard_summary()


# ============================================================
# GOVERNMENT COMPLAINT HISTORY / TREND
# ============================================================

@app.get(
    "/government/trends"
)
def government_trends():

    history = get_complaint_history()


    return {
        "data": history.to_dict(
            orient="records"
        )
    }


# ============================================================
# GOVERNMENT DEPARTMENT TRENDS
# ============================================================

@app.get(
    "/government/department-trends"
)
def government_department_trends():

    raw = get_all_complaints() or []
    if not raw:
        return {"data": []}

    df = pd.DataFrame(raw)
    if "created_at" not in df.columns:
        return {"data": []}

    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.dropna(subset=["created_at_dt"])
    df["date"] = df["created_at_dt"].dt.strftime("%Y-%m-%d")
    df["department"] = df["department"].fillna("General / Unassigned").astype(str).str.strip()

    dept_counts = df.groupby(["date", "department"]).size().reset_index(name="complaints")
    dept_counts = dept_counts.sort_values(["date", "department"])

    return {"data": dept_counts.to_dict(orient="records")}


# ============================================================
# GOVERNMENT COMPLAINT LIST (ENRICHED WITH SLA)
# ============================================================

@app.get(
    "/government/complaints"
)
def government_complaints():

    raw_complaints = get_all_complaints() or []
    enriched_complaints = [compute_sla(c) for c in raw_complaints]

    return {
        "data": enriched_complaints
    }


# ============================================================
# GOVERNMENT UPDATE COMPLAINT STATUS
# ============================================================

@app.post(
    "/government/update-status"
)
def government_update_status(req: StatusUpdateRequest):

    updated = update_complaint_status(
        complaint_number=req.complaint_number,
        status=req.status,
        assigned_officer=req.assigned_officer,
        officer_remarks=req.officer_remarks,
        department=req.department,
        priority=req.priority
    )

    if updated is None:
        return {
            "error": "Failed to update complaint status or complaint not found."
        }

    return {
        "message": "Complaint status updated successfully.",
        "complaint": compute_sla(updated)
    }


# ============================================================
# GOVERNMENT FORECAST
# ============================================================

@app.get(
    "/government/forecast"
)
def government_forecast():

    forecast = get_forecast(
        12
    )


    data = []


    for date, value in forecast.items():

        data.append({

            "date":
                str(
                    date.date()
                ),

            "forecasted_complaints":
                round(
                    float(value),
                    2
                )
        })


    return {
        "data": data
    }


# ============================================================
# GOVERNMENT AI PREDICTIONS
# ============================================================
#
# IMPORTANT:
#
# This is NOT for entering a complaint.
#
# It analyzes ALL complaints already stored
# in the complaints database.
#
# ============================================================

@app.get(
    "/government/predictions"
)
def government_predictions():

    # --------------------------------------------------------
    # Get all complaints from Supabase
    # --------------------------------------------------------

    complaints = get_all_complaints()


    # --------------------------------------------------------
    # No complaints
    # --------------------------------------------------------

    if not complaints:

        return {

            "total_analyzed": 0,

            "sentiment": {},

            "feedback_category": {},

            "complaint_reason": {},

            "departments": {},

            "priority": {

                "low": 0,

                "medium": 0,

                "high": 0,

                "urgent": 0
            },

            "emergency": {

                "emergency": 0,

                "normal": 0
            },

            "harmful": {

                "safe": 0,

                "harmful": 0
            },

            "department_analysis": []
        }


    # --------------------------------------------------------
    # Total complaints
    # --------------------------------------------------------

    total = len(
        complaints
    )


    # ========================================================
    # HELPER FUNCTION
    # ========================================================

    def count_values(
        field_name
    ):

        result = {}


        for complaint in complaints:

            value = complaint.get(
                field_name
            )


            if value is None:

                value = "Unknown"


            value = str(
                value
            ).strip()


            if not value:

                value = "Unknown"


            result[value] = (
                result.get(
                    value,
                    0
                ) + 1
            )


        return result


    # ========================================================
    # SENTIMENT
    # ========================================================

    sentiment = count_values(
        "sentiment"
    )


    # ========================================================
    # FEEDBACK CATEGORY
    # ========================================================

    feedback_category = count_values(
        "feedback_category"
    )


    # ========================================================
    # COMPLAINT REASON
    # ========================================================

    complaint_reason = count_values(
        "complaint_reason"
    )


    # ========================================================
    # DEPARTMENTS
    # ========================================================

    departments = count_values(
        "department"
    )


    # ========================================================
    # PRIORITY
    # ========================================================

    priority = {

        "low": 0,

        "medium": 0,

        "high": 0,

        "urgent": 0
    }


    for complaint in complaints:

        value = complaint.get(
            "priority"
        )


        if value is None:
            continue


        value = str(
            value
        ).strip().lower()


        if value in priority:

            priority[value] += 1


    # ========================================================
    # EMERGENCY
    # ========================================================

    emergency_count = 0


    for complaint in complaints:

        value = complaint.get(
            "emergency"
        )


        if isinstance(
            value,
            bool
        ):

            if value:
                emergency_count += 1

        else:

            value = str(
                value
            ).strip().lower()


            if value in [
                "true",
                "1",
                "yes",
                "emergency"
            ]:

                emergency_count += 1


    emergency = {

        "emergency":
            emergency_count,

        "normal":
            total - emergency_count
    }


    # ========================================================
    # HARMFUL CONTENT
    # ========================================================

    harmful_count = 0


    for complaint in complaints:

        value = complaint.get(
            "harmful"
        )


        if isinstance(
            value,
            bool
        ):

            if value:
                harmful_count += 1

        else:

            value = str(
                value
            ).strip().lower()


            if value in [
                "true",
                "1",
                "yes",
                "harmful"
            ]:

                harmful_count += 1


    harmful = {

        "safe":
            total - harmful_count,

        "harmful":
            harmful_count
    }


    # ========================================================
    # DEPARTMENT INTELLIGENCE
    # ========================================================

    department_analysis = []


    for department in departments:

        department_complaints = [

            complaint

            for complaint in complaints

            if str(
                complaint.get(
                    "department"
                )
                or "Unknown"
            ).strip()
            == department

        ]


        # ----------------------------------------------------
        # High/Critical
        # ----------------------------------------------------

        high_priority_count = 0


        for complaint in (
            department_complaints
        ):

            priority_value = str(
                complaint.get(
                    "priority"
                )
                or ""
            ).strip().lower()


            if priority_value in [
                "high",
                "urgent"
            ]:

                high_priority_count += 1


        # ----------------------------------------------------
        # Emergency
        # ----------------------------------------------------

        department_emergency_count = 0


        for complaint in (
            department_complaints
        ):

            value = complaint.get(
                "emergency"
            )


            if isinstance(
                value,
                bool
            ):

                if value:

                    department_emergency_count += 1

            else:

                value = str(
                    value
                ).strip().lower()


                if value in [
                    "true",
                    "1",
                    "yes",
                    "emergency"
                ]:

                    department_emergency_count += 1


        # ----------------------------------------------------
        # Negative sentiment
        # ----------------------------------------------------

        negative_sentiment_count = 0


        for complaint in (
            department_complaints
        ):

            sentiment_value = str(
                complaint.get(
                    "sentiment"
                )
                or ""
            ).strip().lower()


            if sentiment_value in [
                "negative",
                "very negative"
            ]:

                negative_sentiment_count += 1


        # ----------------------------------------------------
        # Add department result
        # ----------------------------------------------------

        department_analysis.append({

            "department":
                department,

            "complaints":
                len(
                    department_complaints
                ),

            "high_priority":
                high_priority_count,

            "emergency":
                department_emergency_count,

            "negative_sentiment":
                negative_sentiment_count
        })


    # ========================================================
    # SORT DEPARTMENTS
    # ========================================================

    department_analysis.sort(

        key=lambda item:
            item["complaints"],

        reverse=True
    )


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "total_analyzed":
            total,

        "sentiment":
            sentiment,

        "feedback_category":
            feedback_category,

        "complaint_reason":
            complaint_reason,

        "departments":
            departments,

        "priority":
            priority,

        "emergency":
            emergency,

        "harmful":
            harmful,

        "department_analysis":
            department_analysis
    }

# ============================================================
# FORECASTING MODEL DEMONSTRATION
# ============================================================

@app.get("/government/forecast-demo")
def government_forecast_demo():

    return get_forecast_demonstration()

# ============================================================
# GOVERNMENT ANOMALY DETECTION
# ============================================================

@app.get("/government/anomalies")
def government_anomalies():

    return get_anomaly_detection()

@app.get(
    "/government/social-media",
    tags=["Government Social Media"]
)
def government_social_media():

    from app.backend.government_analytics import (
        get_social_media_analysis
    )

    return get_social_media_analysis()

# ============================================================
# SOCIAL MEDIA FORECAST
# ============================================================

@app.get(
    "/government/social-media/forecast",
    tags=["Government Social Media"]
)
def government_social_media_forecast(
    months: int = 6
):

    from app.backend.government_analytics import (
        get_social_media_forecast
    )

    return get_social_media_forecast(
        months=months
    )

# ============================================================
# CURRENT DAILY ANOMALY PREDICTION
# ============================================================

@app.get(
    "/government/anomalies/current"
)
def government_current_anomalies():

    from app.backend.government_analytics import (
        get_current_anomaly_detection
    )

    return get_current_anomaly_detection()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.backend.main:app", host="0.0.0.0", port=port, reload=False)
