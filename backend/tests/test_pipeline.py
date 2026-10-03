import pytest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import init_db, SessionLocal, Base, engine, get_case
from app.models import Consumer, Feeder, Transformer, Case, Alert, PipelineMetric, Reading
from app.schemas import Detection, ReadingIn
from app.services.pipeline import process_reading, queue_reading, reading_queue

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    feeder = Feeder(id="F1", name="Feeder 1")
    transformer = Transformer(id="T1", feeder_id="F1")
    consumer = Consumer(id="C1", category="Residential", feeder_id="F1", transformer_id="T1")
    db.add(feeder)
    db.add(transformer)
    db.add(consumer)
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def valid_detection():
    return Detection(
        consumer_id="C1",
        anomaly_score=0.9,
        risk_level="High",
        cause="Bypass",
        confidence=0.8,
        period_start=datetime.utcnow(),
        period_end=datetime.utcnow(),
        baseline_kwh=10.0,
        actual_kwh=2.0,
        deviation_pct=80.0,
        evidence="Low consumption",
        counter_evidence="",
        recommended_action="Inspect"
    )

def test_reading_enters_queue():
    reading = ReadingIn(consumer_id="C1", ts=datetime.utcnow(), kwh=10.5)
    asyncio.run(queue_reading(reading))
    assert reading_queue.qsize() > 0
    # Cleanup queue
    reading_queue.get_nowait()
    reading_queue.task_done()

@patch('app.services.pipeline.analyze')
def test_pipeline_success(mock_analyze, db_session, valid_detection):
    mock_analyze.return_value = valid_detection
    
    reading = ReadingIn(consumer_id="C1", ts=datetime.utcnow(), kwh=2.0)
    
    # 2. Pipeline retrieves recent readings (we'll add one to DB first)
    db_reading = Reading(consumer_id="C1", ts=datetime.utcnow(), kwh=2.0)
    db_session.add(db_reading)
    db_session.commit()
    
    asyncio.run(process_reading(reading))
    
    # 3. Pipeline calls analyze with correct contract
    mock_analyze.assert_called_once()
    kwargs = mock_analyze.call_args.kwargs
    assert kwargs['consumer_id'] == "C1"
    assert 'readings_df' in kwargs
    assert 'consumer_row' in kwargs
    assert 'baseline_df' in kwargs

    # 4. Returned Detection is persisted
    case = db_session.query(Case).filter(Case.consumer_id == "C1").first()
    assert case is not None
    assert case.risk_level == "High"
    assert case.cause == "Bypass"
    
    # 5. Estimated loss = max(10.0 - 2.0, 0) * 0.15 = 8.0 * 0.15 = 1.2
    assert case.estimated_loss == 1.2
    
    # 6. Priority = 0.9 * 0.8 * 1.2 = 0.864
    assert abs(case.priority - 0.864) < 0.001
    
    # 10. New case gets first_flagged_at
    assert case.first_flagged_at is not None
    
    # 11. High-risk transition creates an alert
    alerts = db_session.query(Alert).filter(Alert.consumer_id == "C1").all()
    assert len(alerts) == 1
    
    # 14. Pipeline metrics are recorded
    metrics = db_session.query(PipelineMetric).filter(PipelineMetric.consumer_id == "C1").all()
    assert len(metrics) == 1

@patch('app.services.pipeline.analyze')
def test_case_preservation_and_duplicate_alerts(mock_analyze, db_session, valid_detection):
    mock_analyze.return_value = valid_detection
    
    # Insert existing case
    first_flagged = datetime(2025, 1, 1)
    existing_case = Case(
        consumer_id="C1", risk_level="High", cause="Bypass", anomaly_score=0.9, confidence=0.8,
        status="Investigating", note="Looking into it", first_flagged_at=first_flagged
    )
    db_session.add(existing_case)
    db_session.commit()
    
    # Need to add reading to DB
    db_reading = Reading(consumer_id="C1", ts=datetime.utcnow(), kwh=2.0)
    db_session.add(db_reading)
    db_session.commit()
    
    reading = ReadingIn(consumer_id="C1", ts=datetime.utcnow(), kwh=2.0)
    asyncio.run(process_reading(reading))
    
    case = db_session.query(Case).filter(Case.consumer_id == "C1").first()
    # 7. Existing case status is preserved
    assert case.status == "Investigating"
    # 8. Existing case note is preserved
    assert case.note == "Looking into it"
    # 9. first_flagged_at is preserved
    assert case.first_flagged_at == first_flagged
    
    # 12. Repeated High-risk readings do not create duplicate alerts
    alerts = db_session.query(Alert).filter(Alert.consumer_id == "C1").all()
    assert len(alerts) == 0

@patch('app.services.pipeline.analyze')
def test_cause_change_alert(mock_analyze, db_session, valid_detection):
    # 13. Cause change while High creates an alert
    valid_detection.cause = "Tamper" # changed cause
    mock_analyze.return_value = valid_detection
    
    # Insert existing case with different cause
    existing_case = Case(
        consumer_id="C1", risk_level="High", cause="Bypass", anomaly_score=0.9, confidence=0.8,
        status="Open"
    )
    db_session.add(existing_case)
    db_session.commit()
    
    # Need to add reading to DB so get_recent_readings finds it
    db_reading = Reading(consumer_id="C1", ts=datetime.utcnow(), kwh=2.0)
    db_session.add(db_reading)
    db_session.commit()
    
    reading = ReadingIn(consumer_id="C1", ts=datetime.utcnow(), kwh=2.0)
    asyncio.run(process_reading(reading))
    
    alerts = db_session.query(Alert).filter(Alert.consumer_id == "C1").all()
    assert len(alerts) == 1
    assert "Tamper" in alerts[0].message

@patch('app.services.pipeline.analyze')
def test_analyze_failure(mock_analyze, db_session):
    # 15. analyze() failure does not create a fake Detection
    mock_analyze.side_effect = Exception("Model failed")
    
    # Need to add reading to DB
    db_reading = Reading(consumer_id="C1", ts=datetime.utcnow(), kwh=2.0)
    db_session.add(db_reading)
    db_session.commit()
    
    reading = ReadingIn(consumer_id="C1", ts=datetime.utcnow(), kwh=2.0)
    asyncio.run(process_reading(reading))
    
    # Should not crash, and should not create a case
    case = db_session.query(Case).filter(Case.consumer_id == "C1").first()
    assert case is None
