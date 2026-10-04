import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.db import Base, engine, SessionLocal
from app.models import Consumer, Reading, Baseline, Case, Feeder, FeederSummary, Alert

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Seed data
    db.add(Feeder(id="F1", name="Feeder 1"))
    db.add(Consumer(id="C1", category="Residential", feeder_id="F1", transformer_id="TX1"))
    db.add(Case(consumer_id="C1", status="New", risk_level="High", cause="Bypass", anomaly_score=0.9, confidence=0.8, first_flagged_at=datetime.utcnow(), last_updated_at=datetime.utcnow()))
    db.add(Reading(consumer_id="C1", ts=datetime(2024,1,1), kwh=10.0))
    db.add(Baseline(consumer_id="C1", ts=datetime(2024,1,1), expected_kwh=5.0))
    db.add(FeederSummary(feeder_id="F1", ts=datetime.utcnow(), total_consumers=10, high_risk_consumers=2, total_consumption=500.0, avg_loss_pct=10.5))
    db.add(Alert(consumer_id="C1", risk_level="High", cause="Bypass", message="Alert msg", is_read=False))
    
    db.commit()
    yield
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_get_consumers(setup_db):
    response = client.get("/consumers")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["consumer_id"] == "C1"

def test_get_consumer_consumption(setup_db):
    response = client.get("/consumers/C1/consumption")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["kwh"] == 10.0

def test_get_consumer_consumption_not_found(setup_db):
    response = client.get("/consumers/INVALID/consumption")
    assert response.status_code == 404

def test_get_consumer_baseline(setup_db):
    response = client.get("/consumers/C1/baseline")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["expected_kwh"] == 5.0

def test_get_case(setup_db):
    response = client.get("/cases/C1")
    assert response.status_code == 200
    assert response.json()["status"] == "New"

def test_update_case_status(setup_db):
    payload = {"status": "Closed", "note": "All good"}
    response = client.patch("/cases/C1/status", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "Closed"
    assert response.json()["note"] == "All good"

def test_update_case_status_invalid(setup_db):
    payload = {"status": "INVALID_STATUS", "note": "Bad"}
    response = client.patch("/cases/C1/status", json=payload)
    assert response.status_code == 422

def test_get_feeders(setup_db):
    response = client.get("/feeders")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["id"] == "F1"

def test_get_feeder_summary(setup_db):
    response = client.get("/feeders/summary")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["feeder_id"] == "F1"

def test_get_alerts(setup_db):
    response = client.get("/alerts")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["consumer_id"] == "C1"

def test_export_cases(setup_db):
    response = client.get("/export/cases")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["consumer_id"] == "C1"

def test_export_case_pdf(setup_db):
    response = client.get("/export/cases/C1/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert b"TraceWatt Investigation Report" in response.content

def test_export_case_pdf_not_found(setup_db):
    response = client.get("/export/cases/INVALID/pdf")
    assert response.status_code == 404

def test_export_case_report(setup_db):
    response = client.get("/export/cases/C1/report")
    assert response.status_code == 200
    data = response.json()
    assert "consumer_details" in data
    assert "consumption_comparison" in data
    assert "anomaly_assessment" in data
    assert "behavioural_pattern" in data
    assert "supporting_features" in data
    assert "explainability" in data
    assert "recommended_inspection" in data
    assert data["consumer_details"]["consumer_id"] == "C1"

def test_dashboard_evaluation():
    response = client.get("/dashboard/evaluation")
    assert response.status_code == 200
    data = response.json()
    assert "model_performance" in data
    assert "latency_and_throughput" in data
    assert "robustness_and_resilience" in data
    assert "dataset_config" in data
    assert data["model_performance"]["accuracy"] >= 0.85
    assert data["model_performance"]["roc_auc"] >= 0.70


