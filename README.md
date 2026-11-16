# 🏛️ Government AI Portal

### AI-Powered Citizen & Government Intelligence Platform

An AI-powered platform designed to connect citizens with government services while providing government officials with intelligent analytics, predictions, complaint intelligence, anomaly detection, and decision-support capabilities.

---

## 📌 Project Overview

The **Government AI Portal** combines a citizen-facing service portal with an AI-powered government intelligence platform.

The system provides two major experiences:

### 👤 Citizen Portal
Citizens can:
- Access government services
- Submit complaints
- Track complaint status
- View complaint history
- Get AI-powered assistance
- Contact support
- Access information about the portal

### 🏛️ Government / Official Portal
Government officials can use AI-powered tools for:
- Complaint analysis
- Department prediction
- Priority prediction
- Sentiment analysis
- Emergency detection
- Anomaly detection
- Harmful-content detection
- Trend forecasting
- Government feedback analysis
- Analytics and reporting
- Hotspot analysis
- Social-media intelligence
- Action and decision support

---

# 🎯 Problem Statement

Government departments receive large volumes of citizen complaints, feedback, requests, and other information.

Manually processing this information can make it difficult to:

- Identify the correct department
- Prioritize important complaints
- Detect emergencies
- Understand citizen sentiment
- Identify unusual complaint patterns
- Analyze feedback at scale
- Forecast emerging trends
- Support data-driven decision making

The Government AI Portal addresses these challenges by combining a citizen service platform with machine-learning-based intelligence tools.

---

# 💡 Proposed Solution

The platform uses machine-learning models and analytics to transform citizen and government data into actionable information.

The system can assist with:

**Citizen Input → Data Processing → AI/ML Analysis → Prediction & Classification → Government Intelligence → Decision Support**

This allows government officials to work with structured insights instead of relying only on manual analysis.

---

# 🚀 Key Features

## 👤 Citizen Services

- Citizen login
- Complaint submission
- Complaint tracking
- Complaint history
- AI Help
- Contact Support
- About / portal information

## 🏛️ Government Intelligence

- Government dashboard
- Complaint analytics
- Prediction dashboard
- Executive reporting
- Action queue
- Anomaly detection
- Hotspot mapping
- Social-media analysis
- Trend analysis
- Government feedback analysis

## 🤖 AI / Machine Learning

The project contains trained models for:

- Sentiment Analysis
- Complaint Reason Classification
- Department Prediction (Hybrid ML + Rule Engine for Municipal and Central CPGRAMS Routing)
- Department Priority Prediction
- Government Feedback Category Classification
- Emergency Detection
- Harmful Content Detection
- Anomaly Detection
- Trend Forecasting
- **Deep Learning Civic Image Classification** (MobileNetV2, 7 classes: `road_damage`, `garbage`, `streetlights`, `water_supply`, `electricity`, `traffic_safety`, `sewerage`)
- **Civic RAG Assistant** (Hybrid TF-IDF + Dense Cosine + BM25 with 12 official statutory documents)

---

# 🧠 Machine Learning & Deep Learning Components

| Component | Architecture / Model | Purpose / Metrics |
|---|---|---|
| Sentiment Model | TF-IDF + Logistic Regression | Analyzes sentiment in text complaints |
| Complaint Reason Model | TF-IDF + LinearSVC | Classifies complaint reasons |
| Department Routing | Hybrid LinearSVC + Rule Hierarchy | Routes complaints across Municipal (BBMP, BWSSB, BESCOM, Traffic Police) & Central CPGRAMS |
| Department Priority Model | Multi-feature Pipeline Classifier | Predicts High/Medium/Low priority |
| Emergency Model | TF-IDF + Random Forest | Detects critical emergencies (fires, explosions, collapsed structures) |
| Harmful Content Model | TF-IDF Pipeline Classifier | Flags abusive/harmful content with false-positive safeguards |
| **Civic Image Classifier** | **MobileNetV2 Transfer Learning** | **94.86% Unseen Test Accuracy across 7 civic complaint categories** |
| **Civic RAG Assistant** | **Hybrid Semantic + BM25 Retriever** | **Statutory answers with citations (Sakala Act 2011, SWM Rules 2016, Central Schemes)** |

---

# 🚀 Deployment & Running the System

### 1. Prerequisites & Environment Setup
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 2. Start FastAPI Backend Service
```bash
uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at `http://localhost:8000/docs`.

Key Endpoints:
- `GET /`: Health check
- `POST /predict`: Multi-task NLP triage & persistent complaint submission
- `POST /predict/image`: Deep Learning visual evidence classification
- `POST /rag/query`: Civic RAG assistant for citizen statutory rights and scheme queries

### 3. Start Citizen Portal (Streamlit)
```bash
streamlit run app/frontend/citizen_portal.py
```
Portal features:
- **Submit Complaint**: Form with photo upload, real-time MobileNetV2 classification, automatic department and SLA matching, and offline draft failover.
- **Track Status**: Live complaint status tracking with official complaint ID.
- **🤖 AI Help**: Interactive civic assistant powered by the 12-document statutory knowledge base.
- **Complaint History**: Historical logs with filtering.

### 4. Start Government Official Dashboard
```bash
streamlit run app/frontend/app.py
```

---

# 🧠 Machine Learning Components

| ML Component | Purpose |
|---|---|
| Sentiment Model | Analyzes sentiment in text-based feedback |
| Complaint Reason Model | Classifies the reason/category of complaints |
| Department Model | Predicts the relevant government department |
| Department Priority Model | Helps determine complaint priority |
| Feedback Category Model | Categorizes government feedback |
| Emergency Model | Detects emergency-related content |
| Harmful Content Model | Identifies potentially harmful content |
| Anomaly Detection Model | Detects unusual patterns |
| Trend Forecasting Model | Forecasts trends from historical data |

The trained models and supporting vectorizers/encoders are stored in the project's `app/pickles/` directory.

---

# 📊 Government Intelligence Modules

The official portal contains several analytical views:

- Dashboard
- Predictions
- Dashboard Predictions
- Executive Report
- Action Queue
- Anomaly Detection
- Hotspot Map
- Social Media Analysis
- Trend Analysis

These modules provide different perspectives for analyzing government-related data.

---

# 🏗️ Project Architecture

```text
Government AI Portal
│
├── Citizen Portal
│   ├── Login
│   ├── Submit Complaint
│   ├── Track Complaint
│   ├── Complaint History
│   ├── AI Help
│   └── Support
│
├── Government / Official Portal
│   ├── Dashboard
│   ├── Predictions
│   ├── Executive Report
│   ├── Action Queue
│   ├── Anomaly Detection
│   ├── Hotspot Map
│   ├── Social Media Analysis
│   └── Trend Analysis
│
├── Backend
│   ├── Prediction Services
│   ├── Government Analytics
│   └── Model Inspection
│
├── Database
│   ├── Database Configuration
│   ├── Database Connection
│   └── Schemas
│
├── Machine Learning Models
│   └── Trained Models / Vectorizers / Encoders
│
└── Notebooks
    └── Data Science & Model Development