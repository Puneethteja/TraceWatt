import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from datetime import datetime
import asyncio

from app.main import app
from app.db import init_db, SessionLocal, Base, engine, insert_reading, get_recent_readings, upsert_case, get_case
from app.models import Consumer, Feeder, Transformer
from app.schemas import Detection, ReadingIn
from app.services.alerts import handle_alert_transition

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Add dummy setup
    feeder = Feeder(id="F1", name="Feeder 1")
    transformer = Transformer(id="T1", feeder_id="F1")
    consumer = Consumer(id="C1", category="Residential", feeder_id="F1", transformer_id="T1")
    db.add(feeder)
    db.add(transformer)
    db.add(consumer)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
<<<<<<< HEAD
    assert response.json()["status"] == "ok"
=======
    assert "app" in response.json()
>>>>>>> 533fc623c44f4b3e0f731bea39c6c27377d94866

def test_insert_reading_unknown_consumer():
    response = client.post("/readings", json={
        "consumer_id": "UNKNOWN",
        "ts": "2026-10-01T00:00:00Z",
        "kwh": 10.5
    })
    assert response.status_code == 404

def test_insert_reading_success():
    response = client.post("/readings", json={
        "consumer_id": "C1",
        "ts": "2026-10-01T00:00:00Z",
        "kwh": 10.5
    })
    assert response.status_code == 200
    data = response.json()
    assert data["stored"] is True
    assert data["queued"] is True

def test_insert_duplicate_reading():
    response = client.post("/readings", json={
        "consumer_id": "C1",
        "ts": "2026-10-01T00:00:00Z", # same timestamp
        "kwh": 10.5
    })
    assert response.status_code == 200
    data = response.json()
    assert data["stored"] is False # Should not be stored again
    assert data["queued"] is False

def test_recent_readings():
    readings = get_recent_readings("C1")
    assert len(readings) == 1
    assert readings[0].kwh == 10.5

def test_case_upsert():
    detection = Detection(
        consumer_id="C1",
        anomaly_score=0.9,
        risk_level="High",
        cause="Bypass",
        confidence=0.85,
        period_start=datetime.utcnow(),
        period_end=datetime.utcnow(),
        baseline_kwh=10.0,
        actual_kwh=2.0,
        deviation_pct=80.0,
        evidence="Low consumption",
        counter_evidence="",
        recommended_action="Inspect"
    )
    upsert_case(detection)
    case = get_case("C1")
    assert case is not None
    assert case.risk_level == "High"
    assert case.status == "Open"

def test_alert_transition():
    detection = Detection(
        consumer_id="C1",
        anomaly_score=0.9,
        risk_level="High",
        cause="Bypass",
        confidence=0.85,
        period_start=datetime.utcnow(),
        period_end=datetime.utcnow(),
        baseline_kwh=10.0,
        actual_kwh=2.0,
        deviation_pct=80.0,
        evidence="Low consumption",
        counter_evidence="",
        recommended_action="Inspect"
    )
    # This shouldn't crash
    handle_alert_transition(detection, old_risk="Low")
