import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal, Base, engine
from app.models import Consumer, Feeder, Transformer

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Ensure dummy setup exists
    feeder = db.query(Feeder).filter(Feeder.id == "F1").first()
    if not feeder:
        feeder = Feeder(id="F1", name="Feeder 1")
        db.add(feeder)
    transformer = db.query(Transformer).filter(Transformer.id == "T1").first()
    if not transformer:
        transformer = Transformer(id="T1", feeder_id="F1")
        db.add(transformer)
    consumer = db.query(Consumer).filter(Consumer.id == "C1").first()
    if not consumer:
        consumer = Consumer(id="C1", category="Residential", feeder_id="F1", transformer_id="T1")
        db.add(consumer)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def test_1_valid_reading():
    response = client.post("/readings", json={
        "consumer_id": "C1",
        "ts": "2026-10-01T12:00:00Z",
        "kwh": 15.2,
        "voltage": 230.1,
        "current": 10.0,
        "power_kw": 2.3,
        "meter_status": "OK",
        "comm_status": "UP"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["stored"] is True
    assert data["queued"] is True
    # Response matches ReadingAck

def test_2_unknown_consumer():
    response = client.post("/readings", json={
        "consumer_id": "UNKNOWN_CONSUMER",
        "ts": "2026-10-01T12:00:00Z",
        "kwh": 10.0
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown consumer"

def test_3_duplicate_reading():
    # Insert first
    client.post("/readings", json={
        "consumer_id": "C1",
        "ts": "2026-10-01T13:00:00Z",
        "kwh": 10.0
    })
    # Duplicate request
    response = client.post("/readings", json={
        "consumer_id": "C1",
        "ts": "2026-10-01T13:00:00Z",
        "kwh": 10.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["stored"] is False
    assert data["queued"] is False

def test_4_nullable_numeric_fields():
    response = client.post("/readings", json={
        "consumer_id": "C1",
        "ts": "2026-10-01T14:00:00Z",
        "kwh": None,
        "voltage": None,
        "current": None
    })
    assert response.status_code == 200
    data = response.json()
    assert data["stored"] is True
    assert data["queued"] is True

def test_5_invalid_request():
    response = client.post("/readings", json={
        "consumer_id": "C1",
        # missing ts
        "kwh": "NOT_A_NUMBER"
    })
    assert response.status_code == 422 # FastAPI validation error
