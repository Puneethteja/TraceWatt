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

## Running Tests
Tests are located in `tests/test_backend.py`.
Run tests via: `pytest tests/test_backend.py`

## Running the Application
`uvicorn app.main:app --reload`
