import asyncio
import pandas as pd
import time
import logging
from datetime import datetime
from ..db import (
    get_recent_readings, SessionLocal,
    Case, CaseEvent, PipelineMetric, get_baseline
)
from ..models import Consumer
from .alerts import handle_alert_transition
from ..config import WINDOW_ROWS

logger = logging.getLogger(__name__)

# Import the external analyze function provided by Puneet
try:
    from engine.analyze import analyze
except ImportError:
    # Fallback or mock for testing if engine is not yet available
    def analyze(consumer_id, readings_df, consumer_row, baseline_df=None):
        return None

reading_queue = asyncio.Queue()

async def queue_reading(reading):
    await reading_queue.put(reading)

async def process_queue():
    while True:
        reading = await reading_queue.get()
        try:
            await process_reading(reading)
        except Exception as e:
            logger.error(f"Error processing reading for {reading.consumer_id}: {e}")
        finally:
            reading_queue.task_done()

async def process_reading(reading):
    t_start = time.time()
    
    db = SessionLocal()
    try:
        # Load last WINDOW_ROWS readings
        readings = get_recent_readings(reading.consumer_id, n=WINDOW_ROWS)
        if not readings:
            return
            
        readings_df = pd.DataFrame([r.__dict__ for r in readings])
        
        # Load consumer information
        consumer = db.query(Consumer).filter(Consumer.id == reading.consumer_id).first()
        if not consumer:
            return
        
        # We assume consumer object can be represented as series
        consumer_row = pd.Series(consumer.__dict__)
        
        # Load baseline if available
        baselines = get_baseline(reading.consumer_id)
        baseline_df = pd.DataFrame([b.__dict__ for b in baselines]) if baselines else None
        
        # Detect
        t_detect_start = time.time()
        
        try:
            detection = analyze(
                consumer_id=reading.consumer_id,
                readings_df=readings_df,
                consumer_row=consumer_row,
                baseline_df=baseline_df
            )
        except Exception as e:
            logger.error(f"analyze() failed for {reading.consumer_id}: {e}")
            return
            
        if not detection:
            return
            
        t_detect_end = time.time()
        
        # Calculate estimated loss
        # max(baseline_kwh - actual_kwh, 0) * tariff
        # Extract tariff from consumer dictionary or default to a generic value if not present (although expected to be present)
        tariff = consumer_row.get("tariff", 0.15)
        estimated_loss = max(detection.baseline_kwh - detection.actual_kwh, 0) * tariff
        
        # Calculate priority
        # priority = anomaly_score * confidence * estimated_loss
        priority = detection.anomaly_score * detection.confidence * estimated_loss
        
        # Existing case state preservation
        existing_case = db.query(Case).filter(Case.consumer_id == reading.consumer_id).first()
        old_status = existing_case.status if existing_case else "Open"
        old_note = existing_case.note if existing_case else None
        old_risk = existing_case.risk_level if existing_case else None
        old_cause = existing_case.cause if existing_case else None
        first_flagged_at = existing_case.first_flagged_at if existing_case else datetime.utcnow()
        
        # Upsert case logic
        if existing_case:
            existing_case.risk_level = detection.risk_level
            existing_case.cause = detection.cause
            existing_case.anomaly_score = detection.anomaly_score
            existing_case.confidence = detection.confidence
            existing_case.evidence = detection.evidence
            existing_case.counter_evidence = detection.counter_evidence
            existing_case.recommended_action = detection.recommended_action
            existing_case.estimated_loss = estimated_loss
            existing_case.priority = priority
            existing_case.last_updated_at = datetime.utcnow()
            
            # Restore preserved fields
            existing_case.status = old_status
            existing_case.note = old_note
            existing_case.first_flagged_at = first_flagged_at
        else:
            new_case = Case(
                consumer_id=detection.consumer_id,
                risk_level=detection.risk_level,
                cause=detection.cause,
                anomaly_score=detection.anomaly_score,
                confidence=detection.confidence,
                evidence=detection.evidence,
                counter_evidence=detection.counter_evidence,
                recommended_action=detection.recommended_action,
                estimated_loss=estimated_loss,
                priority=priority,
                status="Open",
                first_flagged_at=first_flagged_at
            )
            db.add(new_case)
            existing_case = new_case
            
        db.flush()
        
        # Create case event if risk changed
        if old_risk != detection.risk_level:
            event = CaseEvent(
                case_id=existing_case.id,
                event_type="RISK_CHANGED",
                note=f"Risk changed from {old_risk} to {detection.risk_level}"
            )
            db.add(event)
        
        db.commit()
        
        # Handle alert transition
        handle_alert_transition(detection, old_risk, old_cause)
        
        t_store_end = time.time()
        
        # Record pipeline metrics
        metric = PipelineMetric(
            consumer_id=reading.consumer_id,
            ingest_to_detect_ms=(t_detect_start - t_start) * 1000,
            detect_to_store_ms=(t_store_end - t_detect_end) * 1000
        )
        db.add(metric)
        db.commit()

    finally:
        db.close()
