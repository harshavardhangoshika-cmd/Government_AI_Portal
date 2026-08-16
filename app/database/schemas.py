# --------------------------------------------------
# Import Pydantic
# --------------------------------------------------

from pydantic import BaseModel


# --------------------------------------------------
# Complaint Input Schema
# --------------------------------------------------

class ComplaintRequest(BaseModel):

    complaint_text: str
    state: str
    language: str
    channel: str


# --------------------------------------------------
# Prediction Output Schema
# --------------------------------------------------

class PredictionResponse(BaseModel):

    sentiment: str
    feedback_category: str
    complaint_reason: str
    department: str
    emergency: str
    harmful_content: str
    recommended_scheme: str