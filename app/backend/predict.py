import os
import joblib
import pandas as pd
from datetime import datetime


# ============================================================
# PICKLE FOLDER PATH
# ============================================================

# __file__ = app/backend/predict.py
# dirname(dirname(__file__)) = app/
#
# Therefore:
# PICKLE_DIR = app/pickles/

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PICKLE_DIR = os.path.join(
    BASE_DIR,
    "pickles"
)


# ============================================================
# MODULE 1 : SENTIMENT
# ============================================================

sentiment_model = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "01_sentiment_model.pkl"
    )
)


# ============================================================
# MODULE 2 : FEEDBACK CATEGORY
# ============================================================

feedback_model = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "feedback_category_model.pkl"
    )
)

feedback_vectorizer = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "feedback_tfidf_vectorizer.pkl"
    )
)

feedback_encoder = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "feedback_label_encoder.pkl"
    )
)


# ============================================================
# MODULE 3 : COMPLAINT REASON
# ============================================================

complaint_model = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "complaint_reason_model.pkl"
    )
)

complaint_vectorizer = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "complaint_tfidf_vectorizer.pkl"
    )
)


# ============================================================
# MODULE 4 : DEPARTMENT PREDICTION
# ============================================================
#
# department_model.pkl is a complete Pipeline:
#
# Raw Complaint
#       ↓
#      TF-IDF
#       ↓
# Tuned Classifier
#       ↓
#   Department
#
# Therefore, raw complaint text can be passed directly.
# ============================================================

department_model = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "department_model.pkl"
    )
)


# ============================================================
# MODULE 5 : DEPARTMENT PRIORITY PREDICTION
# ============================================================
#
# department_priority_model.pkl is a complete Pipeline.
#
# It expects a pandas DataFrame containing the same
# feature columns that were used during training.
# ============================================================

department_priority_model = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "department_priority_model.pkl"
    )
)


# ============================================================
# MODULE 6 : EMERGENCY
# ============================================================

emergency_model = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "emergency_model.pkl"
    )
)

emergency_vectorizer = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "emergency_vectorizer.pkl"
    )
)


# ============================================================
# MODULE 7 : HARMFUL CONTENT
# ============================================================

harmful_model = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "harmful_content_model.pkl"
    )
)

harmful_encoder = joblib.load(
    os.path.join(
        PICKLE_DIR,
        "harmful_label_encoder.pkl"
    )
)


# ============================================================
# MODEL LOADING CONFIRMATION
# ============================================================

print("=" * 60)
print("ALL ML MODELS LOADED SUCCESSFULLY")
print("=" * 60)

print(
    "Module 1 - Sentiment       :",
    type(sentiment_model)
)

print(
    "Module 2 - Feedback        :",
    type(feedback_model)
)

print(
    "Module 3 - Complaint Reason:",
    type(complaint_model)
)

print(
    "Module 4 - Department      :",
    type(department_model)
)

print(
    "Module 5 - Priority        :",
    type(department_priority_model)
)

print(
    "Module 6 - Emergency       :",
    type(emergency_model)
)

print(
    "Module 7 - Harmful Content :",
    type(harmful_model)
)

print("=" * 60)


# ============================================================
# MODULE 1 : SENTIMENT PREDICTION FUNCTION
# ============================================================

def predict_sentiment(text: str):
    """
    Predict complaint sentiment and confidence.
    """

    prediction = sentiment_model.predict(
        [text]
    )[0]

    probabilities = sentiment_model.predict_proba(
        [text]
    )[0]

    confidence = round(
        float(max(probabilities)) * 100,
        2
    )

    return {
        "sentiment": prediction,
        "confidence": confidence
    }


# ============================================================
# HYBRID EXPERT RULES REFINEMENT ENGINE FOR HIGH ACCURACY
# ============================================================

def refine_predictions_with_expert_rules(text: str, result: dict) -> dict:
    t_lower = text.lower()

    # 1. HEALTH & HOSPITALS
    health_keywords = ["hospital", "hospitals", "clinic", "doctor", "doctors", "medicine", "medicines", "medical", "ambulance", "phc", "patient", "nurse", "ward", "health"]
    if any(kw in t_lower for kw in health_keywords):
        result["department"] = "Health & Family Welfare"
        result["complaint_reason"] = "Health & Medical Services"
        if any(neg in t_lower for neg in ["not in good", "bad", "dirty", "poor", "no doctor", "corrupt", "unclean", "condition"]):
            result["sentiment"] = "Negative"
            result["priority"] = "High"

    # 2. SANITATION, DRAINAGE & WATER SUPPLY
    water_keywords = ["drainage", "sewer", "sewerage", "leakage", "water supply", "pipe", "pipeline", "tap water", "dirty water", "no water", "overflow", "stagnant"]
    if any(kw in t_lower for kw in water_keywords):
        result["department"] = "BWSSB / Sanitation & Water"
        result["complaint_reason"] = "Water Supply & Sanitation"
        result["sentiment"] = "Negative"
        if any(h_kw in t_lower for h_kw in ["leakage", "no water", "overflow", "days"]):
            result["priority"] = "High"

    # 3. ROADS & FOOTPATHS
    road_keywords = ["pothole", "potholes", "road", "roads", "footpath", "asphalt", "tar road", "street", "street light", "streetlight"]
    if any(kw in t_lower for kw in road_keywords):
        result["department"] = "BBMP / Municipal Works"
        result["complaint_reason"] = "Mobility - Roads & Infrastructure"
        result["sentiment"] = "Negative"

    # 4. POWER & ELECTRICITY
    power_keywords = ["electricity", "power cut", "powercut", "transformer", "voltage", "blackout", "electric wire", "bescom"]
    if any(kw in t_lower for kw in power_keywords):
        result["department"] = "BESCOM / Power & Electricity"
        result["complaint_reason"] = "Electricity & Power Supply"
        result["sentiment"] = "Negative"
        if any(h_kw in t_lower for h_kw in ["power cut", "wire", "spark", "blackout"]):
            result["priority"] = "High"

    # 5. EDUCATION & SCHOOLS / UNIVERSITIES
    education_keywords = [
        "school", "schools", "college", "colleges", "university", "education",
        "teacher", "teachers", "student", "students", "classroom", "midday meal",
        "mid day meal", "fees", "scholarship", "exam", "examination", "syllabus",
        "board exam", "pu college", "principal", "blackboard", "bdeo", "ddpi", "tuition"
    ]
    if any(kw in t_lower for kw in education_keywords):
        result["department"] = "Department of Education"
        result["complaint_reason"] = "Education & Academic Services"
        if any(neg in t_lower for neg in ["not in good", "bad", "poor", "no teacher", "corrupt", "unclean", "no facilities", "delay", "high fees"]):
            result["sentiment"] = "Negative"
            result["priority"] = "Medium"

    # 6. EMERGENCY DETECTION OVERRIDE
    emergency_keywords = ["fire", "gas leak", "building collapse", "explosion", "drowning", "electrocution", "severe accident"]
    if any(kw in t_lower for kw in emergency_keywords):
        result["emergency"] = 1
        result["priority"] = "Urgent"
        result["sentiment"] = "Negative"

    # 7. GENERAL COMPLAINT NEGATIVE PHRASE MARKERS
    negative_markers = ["not in good", "not good", "bad", "terrible", "worst", "broken", "damaged", "no response", "delay", "useless", "fail"]
    if any(nm in t_lower for nm in negative_markers):
        result["sentiment"] = "Negative"

    return result


# ============================================================
# MAIN COMPLAINT PROCESSING FUNCTION
# ============================================================

def process_complaint(text):

    # ========================================================
    # BASIC INPUT VALIDATION
    # ========================================================

    if not isinstance(text, str):
        raise TypeError(
            "Complaint text must be a string."
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "Complaint text cannot be empty."
        )

    result = {}


    # ========================================================
    # MODULE 1 : SENTIMENT
    # ========================================================

    sentiment = sentiment_model.predict(
        [text]
    )[0]

    sentiment_prob = (
        sentiment_model
        .predict_proba([text])
        .max()
        * 100
    )

    result["sentiment"] = sentiment

    result["sentiment_confidence"] = round(
        float(sentiment_prob),
        2
    )


    # ========================================================
    # MODULE 2 : FEEDBACK CATEGORY
    # ========================================================

    feedback_features = (
        feedback_vectorizer.transform(
            [text]
        )
    )

    feedback_prediction = (
        feedback_model.predict(
            feedback_features
        )
    )

    feedback_prediction = (
        feedback_encoder.inverse_transform(
            feedback_prediction
        )[0]
    )

    result["feedback_category"] = (
        feedback_prediction
    )


    # ========================================================
    # MODULE 3 : COMPLAINT REASON
    # ========================================================

    complaint_features = (
        complaint_vectorizer.transform(
            [text]
        )
    )

    complaint_reason = (
        complaint_model.predict(
            complaint_features
        )[0]
    )

    result["complaint_reason"] = (
        complaint_reason
    )


    # ========================================================
    # MODULE 4 : DEPARTMENT PREDICTION
    # ========================================================
    #
    # Complete ML Pipeline:
    #
    # Complaint
    #     ↓
    # TF-IDF
    #     ↓
    # Tuned Classifier
    #     ↓
    # Department
    #
    # ========================================================

    department_prediction = (
        department_model.predict(
            [text]
        )[0]
    )

    result["department"] = (
        department_prediction
    )

    print(
        "\nMODULE 4 DEPARTMENT:",
        department_prediction
    )


    # ========================================================
    # MODULE 5 : DEPARTMENT PRIORITY PREDICTION
    # ========================================================
    #
    # Module 5 receives:
    #
    # - Complaint text
    # - Channel
    # - Department
    # - Scheme
    # - State
    # - Language
    # - Sentiment
    # - Sentiment score
    # - Date/time information
    # - Summary length
    #
    # ========================================================

    now = datetime.now()


    # --------------------------------------------------------
    # CREATE MODULE 5 INPUT DATAFRAME
    # --------------------------------------------------------

    priority_input = pd.DataFrame({

        # ----------------------------------------------------
        # TEXT FEATURE
        # ----------------------------------------------------

        "interaction_summary": [
            text
        ],


        # ----------------------------------------------------
        # CATEGORICAL FEATURES
        # ----------------------------------------------------

        "channel": [
            "Public Grievance Portal (CPGRAMS)"
        ],

        "department": [
            department_prediction
        ],

        "scheme_name": [
            "Unknown"
        ],

        "state": [
            "Telangana"
        ],

        "language": [
            "English"
        ],

        "sentiment_label": [
            sentiment
        ],


        # ----------------------------------------------------
        # NUMERICAL FEATURES
        # ----------------------------------------------------

        # The current portal does not calculate the original
        # training sentiment score, so the deployment default
        # is retained.
        "sentiment_score": [
            0.0
        ],


        # ----------------------------------------------------
        # DATE / TIME FEATURES
        # ----------------------------------------------------

        "Year": [
            now.year
        ],

        "Month": [
            now.month
        ],

        "Day": [
            now.day
        ],

        "Hour": [
            now.hour
        ],

        "Weekday": [
            now.strftime("%A")
        ],


        # ----------------------------------------------------
        # TEXT LENGTH
        # ----------------------------------------------------

        "Summary_Length": [
            len(text)
        ]
    })


    # --------------------------------------------------------
    # DISPLAY INPUT USED BY MODULE 5
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("MODULE 5 INPUT")
    print("=" * 60)

    print(
        priority_input.to_string(
            index=False
        )
    )


    # --------------------------------------------------------
    # RUN MODULE 5
    # --------------------------------------------------------

    priority_prediction = (
        department_priority_model.predict(
            priority_input
        )[0]
    )


    # --------------------------------------------------------
    # STORE PRIORITY
    # --------------------------------------------------------

    result["priority"] = str(
        priority_prediction
    )


    # --------------------------------------------------------
    # IMPORTANT DEBUG OUTPUT
    # --------------------------------------------------------

    print(
        "\nMODULE 5 PRIORITY PREDICTION:",
        repr(result["priority"])
    )


    # ========================================================
    # MODULE 6 : EMERGENCY
    # ========================================================

    emergency_features = (
        emergency_vectorizer.transform(
            [text]
        )
    )

    emergency_prediction = (
        emergency_model.predict(
            emergency_features
        )[0]
    )

    result["emergency"] = int(
        emergency_prediction
    )


    # ========================================================
    # MODULE 7 : HARMFUL CONTENT
    # ========================================================

    harmful_prediction = (
        harmful_model.predict(
            [text]
        )
    )

    harmful_prediction = (
        harmful_encoder.inverse_transform(
            harmful_prediction
        )[0]
    )


    if harmful_prediction == "HOF":

        result["harmful_content"] = (
            "Harmful"
        )

    else:

        result["harmful_content"] = (
            "Not Harmful"
        )


    # ========================================================
    # FINAL RESULT & HYBRID ACCURACY REFINEMENT
    # ========================================================

    result = refine_predictions_with_expert_rules(text, result)

    # --------------------------------------------------------
    # HARMFUL CONTENT FALSE-POSITIVE ACCURACY GUARD
    # --------------------------------------------------------
    # Prevent benign civic/educational complaints from being
    # incorrectly flagged as harmful unless abusive keywords exist.
    harmful_triggers = ["kill", "murder", "threat", "bomb", "abuse", "attack", "terror", "shoot", "bribe", "assault"]
    if not any(ht in text.lower() for ht in harmful_triggers):
        result["harmful_content"] = "Not Harmful"

    print("\n" + "=" * 60)
    print("RETURNED PREDICTION RESULTS (ACCURACY REFINED)")
    print("=" * 60)

    print(
        "Sentiment        :",
        result["sentiment"]
    )

    print(
        "Sentiment Conf.  :",
        result["sentiment_confidence"]
    )

    print(
        "Feedback Category:",
        result["feedback_category"]
    )

    print(
        "Complaint Reason :",
        result["complaint_reason"]
    )

    print(
        "Department       :",
        result["department"]
    )

    print(
        "Priority         :",
        result["priority"]
    )

    print(
        "Emergency        :",
        result["emergency"]
    )

    print(
        "Harmful Content  :",
        result["harmful_content"]
    )

    print("=" * 60)


    return result


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    test_cases = [
        "The road is full of potholes and people are having difficulty travelling.",
        "The primary school classroom roof is leaking and teachers are not coming on time."
    ]

    for idx, complaint in enumerate(test_cases, 1):
        print(f"\n--- TEST CASE {idx} ---")
        output = process_complaint(complaint)
        for key, value in output.items():
            print(f"  {key} : {value}")