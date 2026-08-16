# 🏛️ Government AI Portal - Citizen & Government Intelligence Platform

An AI-powered public grievance management, analytics, and data-driven governance platform designed for citizen complaint resolution, priority detection, emergency routing, and executive analytics.

---

## 🌟 Key Features

- **🤖 AI Multi-Module Prediction Engine**:
  - **Sentiment Analysis**: Predicts complaint sentiment (Negative/Neutral/Positive) with confidence scores.
  - **Feedback Categorization**: Classifies feedback type into structured grievance categories.
  - **Complaint Reason Detection**: Identifies underlying issues across civic domains.
  - **Automated Department Routing**: Routes complaints to **BBMP / Municipal Works**, **BESCOM / Power & Electricity**, **BWSSB / Sanitation & Water**, **Health & Family Welfare**, **Department of Education**, etc.
  - **Department Priority Classifier**: Assigns resolution priority (Urgent / High / Medium / Low).
  - **Emergency Override**: Detects urgent life-safety emergencies (fires, explosions, building collapses) for immediate response.
  - **Harmful Content Guard**: Filters abusive content while preventing false positives.

- **🏛️ Government Official Portal**:
  - **Action Queue**: Actionable complaint review with status updates and SLA resolution tracking.
  - **Hotspot Map**: Interactive district geographical heatmaps with district location filtering across 7 states.
  - **Executive Analytics & Reports**: Departmental resolution metrics, overdue complaint tracking, and SLA performance reports.
  - **Trend Analysis**: Interactive multi-department time-series trends (Line Charts & Stacked Area Charts).

- **👤 Citizen Portal**:
  - **Dynamic Complaint Submission**: Dynamic multi-state & district dropdown selector.
  - **Complaint Tracking**: Real-time status lookup and resolution verification.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher
- Git ([Download Git](https://git-scm.com/downloads))

### 2. Installation & Setup
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ML_project.git
cd ML_project

# Activate Virtual Environment (Windows)
venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 3. Running the Application
```bash
# Start FastAPI Backend Server
venv\Scripts\python.exe -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000

# Start Streamlit Frontend Web App (In a new terminal)
venv\Scripts\python.exe -m streamlit run app/frontend/login.py --server.port 8501
```

Access the app at: `http://localhost:8501`

---

## 🔑 Demo Accounts

| Role | Email | Password |
|---|---|---|
| 🏛️ **Government Official** | `official@gov.in` | `official123` |
| 👤 **Citizen Portal** | `citizen@gov.in` | `citizen123` |

---

## 📄 License
© 2026 Government AI Portal. All rights reserved.
