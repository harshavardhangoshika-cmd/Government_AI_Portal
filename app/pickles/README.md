# Final Model Files — Module 10 Ready Set

8 of 9 modules are in here, verified working. Priority is intentionally left out — see below.

## Folder structure

```
final_models/
├── sentiment/
│   └── sentiment_model.pkl            (self-contained pipeline, takes raw text)
├── feedback_category/
│   ├── feedback_tfidf_vectorizer.pkl
│   ├── feedback_category_model.pkl
│   └── feedback_label_encoder.pkl     (classes: Appreciation, Complaint, Query, Suggestion)
├── complaint_reason/
│   ├── complaint_reason_model.pkl
│   └── complaint_tfidf_vectorizer.pkl (classes: 28 civic categories, e.g. "Street lighting")
├── department/
│   ├── department_model.pkl
│   ├── department_tfidf_vectorizer.pkl
│   └── department_label_encoder.pkl   (classes: 11 real ministry names)
├── emergency_detection/
│   ├── emergency_model.pkl
│   └── emergency_vectorizer.pkl       (classes: 0 = non-emergency, 1 = emergency)
├── harmful_content/
│   ├── harmful_content_model.pkl      (self-contained pipeline, takes raw text)
│   └── harmful_label_encoder.pkl      (classes: HOF, NOT)
├── trend_forecasting/
│   └── trend_ets_model.pkl            (use .forecast(steps) — batch layer, not per-message)
├── anomaly_detection/
│   ├── anomaly_isolation_forest_model.pkl   (needs 7 engineered features, see below)
│   └── anomaly_detection_config.pkl         (IQR bounds + confidence thresholds dict)
└── priority_prediction_PENDING/
    └── (empty — do not use any of the 3 previously uploaded Priority files, all leak)
```

## Loading pattern per module

**Self-contained pipelines** (just call `.predict([text])` directly, no separate vectorizer step):
- `sentiment_model.pkl`
- `harmful_content_model.pkl`

**Model + vectorizer pairs** (must call `vectorizer.transform([text])` first, then `model.predict(...)`):
- `feedback_category/`, `complaint_reason/`, `department/`, `emergency_detection/`

**Label encoders** — only some modules need one (their model outputs a plain integer that must be decoded back to the real label): `feedback_category`, `department`, `harmful_content`. Sentiment, complaint reason, and emergency detection already return their real label directly (or an integer that's self-explanatory: emergency is 0/1).

**Anomaly Detection's 7 required input features**, in this exact order: `Actual_Complaints`, `Lag_1`, `Lag_2`, `Lag_3`, `Rolling_Mean_3`, `Rolling_STD_3`, `Pct_Change`. This isn't a per-message model — it runs on your accumulated complaint-volume history, not on a single incoming complaint.

## Deliberately excluded

- **Old Emergency Detection pipeline** (previously uploaded as `03_EmergencyDetectionModel.pkl`) — this was the untuned overwrite we deleted from the notebook; `emergency_model.pkl` in this folder is the correct GridSearch-tuned replacement.
- **RandomForest Department model** (`03_random_forest_department_model.pkl` + `03_preprocessor.pkl`) — requires `priority` as an input feature, which doesn't exist yet for a brand-new incoming complaint. Kept out until it's confirmed this is meant for a different use case (e.g. analyzing resolved tickets) rather than live routing.
- **All three Priority files** — every version uploaded so far leaks the target through `interaction_summary`/`combined_text`. Waiting on the clean re-run using the fix script provided (categorical + numeric features only, `interaction_summary` fully dropped).

## Still needed before Module 10 is complete

1. Run the Priority fix script, confirm an honest cross-validated accuracy, drop the result in as `priority_prediction/priority_model.pkl`.
2. Confirm `trend_ets_model.pkl`'s exact usage — couldn't verify object interface directly (no `statsmodels` available in this environment), but standard usage is `model.forecast(steps)`.
