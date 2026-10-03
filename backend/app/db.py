from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, Consumer, Case, Reading, Baseline, Feeder, FeederSummary, Alert, PipelineMetric, CaseEvent
from .config import DATABASE_URL
from datetime import datetime

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def list_consumers(risk=None, feeder=None, transformer=None, category=None, limit=200, offset=0):
    db = SessionLocal()
    try:
        query = db.query(Consumer, Case).outerjoin(Case, Consumer.id == Case.consumer_id)
        if risk:
            query = query.filter(Case.risk_level == risk)
        if feeder:
            query = query.filter(Consumer.feeder_id == feeder)
        if transformer:
            query = query.filter(Consumer.transformer_id == transformer)
        if category:
            query = query.filter(Consumer.category == category)
        
        results = query.offset(offset).limit(limit).all()
        consumers = []
        for consumer, case in results:
            consumers.append({
                "consumer_id": consumer.id,
                "category": consumer.category,
                "feeder_id": consumer.feeder_id,
                "transformer_id": consumer.transformer_id,
                "risk_level": case.risk_level if case else None,
                "status": case.status if case else None,
                "anomaly_score": case.anomaly_score if case else None,
            })
        return consumers
    finally:
        db.close()

def get_case(consumer_id):
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.consumer_id == consumer_id).first()
        return case
    finally:
        db.close()

def get_consumption(consumer_id, start=None, end=None, resample="D"):
    # Resampling should ideally be done in pandas if "D" is provided, but we return raw data or basic aggregated data here
    # For simplicity, returning raw data in range
    db = SessionLocal()
    try:
        query = db.query(Reading).filter(Reading.consumer_id == consumer_id)
        if start:
            query = query.filter(Reading.ts >= start)
        if end:
            query = query.filter(Reading.ts <= end)
        return query.order_by(Reading.ts).all()
    finally:
        db.close()

def get_baseline(consumer_id):
    db = SessionLocal()
    try:
        return db.query(Baseline).filter(Baseline.consumer_id == consumer_id).order_by(Baseline.ts).all()
    finally:
        db.close()

def update_case_status(consumer_id, status, note=None):
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.consumer_id == consumer_id).first()
        if case:
            case.status = status
            case.note = note
            case.last_updated_at = datetime.utcnow()
            db.commit()
            return True
        return False
    finally:
        db.close()

def list_feeders():
    db = SessionLocal()
    try:
        return db.query(Feeder).all()
    finally:
        db.close()

def get_feeder_summary(transformer_id=None, feeder_id=None):
    db = SessionLocal()
    try:
        query = db.query(FeederSummary)
        if feeder_id:
            query = query.filter(FeederSummary.feeder_id == feeder_id)
        # Assuming summary is aggregated at feeder level only based on model
        return query.all()
    finally:
        db.close()

def list_alerts(since_id=0, limit=50):
    db = SessionLocal()
    try:
        return db.query(Alert).filter(Alert.id > since_id).order_by(Alert.id.desc()).limit(limit).all()
    finally:
        db.close()

def export_cases(filters):
    # Simplistic export just returning dicts
    db = SessionLocal()
    try:
        query = db.query(Case)
        # Apply filters as needed, simplistic approach:
        return query.all()
    finally:
        db.close()

def insert_reading(reading) -> bool:
    db = SessionLocal()
    try:
        # Check duplicate
        exists = db.query(Reading).filter(
            Reading.consumer_id == reading.consumer_id,
            Reading.ts == reading.ts
        ).first()
        if exists:
            return False
            
        new_reading = Reading(
            consumer_id=reading.consumer_id,
            ts=reading.ts,
            kwh=reading.kwh,
            voltage=reading.voltage,
            current=reading.current,
            power_kw=reading.power_kw,
            meter_status=reading.meter_status,
            comm_status=reading.comm_status
        )
        db.add(new_reading)
        db.commit()
        return True
    finally:
        db.close()

def get_recent_readings(consumer_id, n=500):
    db = SessionLocal()
    try:
        return db.query(Reading).filter(Reading.consumer_id == consumer_id).order_by(Reading.ts.desc()).limit(n).all()
    finally:
        db.close()

def upsert_case(detection):
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.consumer_id == detection.consumer_id).first()
        if case:
            case.risk_level = detection.risk_level
            case.cause = detection.cause
            case.anomaly_score = detection.anomaly_score
            case.confidence = detection.confidence
            case.evidence = detection.evidence
            case.counter_evidence = detection.counter_evidence
            case.recommended_action = detection.recommended_action
            case.last_updated_at = datetime.utcnow()
        else:
            case = Case(
                consumer_id=detection.consumer_id,
                risk_level=detection.risk_level,
                cause=detection.cause,
                anomaly_score=detection.anomaly_score,
                confidence=detection.confidence,
                evidence=detection.evidence,
                counter_evidence=detection.counter_evidence,
                recommended_action=detection.recommended_action,
                status="Open"
            )
            db.add(case)
        db.commit()
    finally:
        db.close()

def insert_alert(detection):
    db = SessionLocal()
    try:
        alert = Alert(
            consumer_id=detection.consumer_id,
            risk_level=detection.risk_level,
            cause=detection.cause,
            message=f"Alert for consumer {detection.consumer_id}: {detection.risk_level} risk due to {detection.cause}",
            is_read=False
        )
        db.add(alert)
        db.commit()
    finally:
        db.close()

def log_metric(consumer_id, ingest_to_detect_ms, detect_to_store_ms):
    db = SessionLocal()
    try:
        metric = PipelineMetric(
            consumer_id=consumer_id,
            ingest_to_detect_ms=ingest_to_detect_ms,
            detect_to_store_ms=detect_to_store_ms
        )
        db.add(metric)
        db.commit()
    finally:
        db.close()
