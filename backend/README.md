# TraceWatt Backend

This repository contains the backend components for the TraceWatt project, specifically focusing on the database, routing, and pipeline integrations.

## Completed Modules
- **`app/db.py`**: SQLite database interactions, CRUD operations, and SQLAlchemy sessions.
- **`app/models.py`**: SQLAlchemy ORM models (Feeders, Transformers, Consumers, Readings, Cases, Alerts, etc.).
- **`app/schemas.py`**: Pydantic models for API request/response validation (ReadingIn, Detection, CaseOut, etc.).
- **`app/config.py`**: Environment variables and configurations.
- **`app/routers/readings.py`**: API endpoints for ingestion.
- **`app/services/pipeline.py`**: Asynchronous processing pipeline linking ingestion to ML analysis.
- **`app/services/alerts.py`**: Logic for transitioning case risks and generating alerts.
- **`app/services/report_pdf.py`**: Dummy PDF generation for investigation cases.
- **`scripts/load_data.py`**: Script to seed the database with initial CSV data.

## Model Training & Evaluation Benchmark
To train the LightGBM classifier, Isolation Forest, and Isotonic Calibrator on the standardized 35,000 consumer cohort (28,000 train / 7,000 held-out test) with fixed reproducibility (`random_state=42`):

```bash
cd backend
python engine/train.py --data-dir data/processed --sample-size 35000 --train-size 28000 --test-size 7000 --random-state 42
```

Artifacts generated:
* `backend/engine/models/lgbm_model.pkl`: Calibrated LightGBM tree ensemble
* `backend/engine/models/iso_forest.pkl`: Unsupervised zero-day anomaly detector
* `backend/engine/models/calibrator.pkl`: Isotonic probability calibration layer
* `backend/engine/models/scaler.pkl`: StandardScaler fit strictly on train split
* `backend/engine/models/eval_metrics.json`: Structured evaluation metrics JSON for the mission dashboard

## Running Tests
Run backend test suite:
```bash
pytest backend/tests
```

## Running the Application
```bash
uvicorn app.main:app --reload --port 8000
```

