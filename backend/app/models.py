from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Feeder(Base):
    __tablename__ = "feeders"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
class Transformer(Base):
    __tablename__ = "transformers"
    id = Column(String, primary_key=True, index=True)
    feeder_id = Column(String, ForeignKey("feeders.id"), nullable=False)
    
class Consumer(Base):
    __tablename__ = "consumers"
    id = Column(String, primary_key=True, index=True)
    category = Column(String, nullable=False)
    feeder_id = Column(String, ForeignKey("feeders.id"), nullable=False)
    transformer_id = Column(String, ForeignKey("transformers.id"), nullable=False)

class Reading(Base):
    __tablename__ = "readings"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    consumer_id = Column(String, ForeignKey("consumers.id"), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    kwh = Column(Float, nullable=True)
    voltage = Column(Float, nullable=True)
    current = Column(Float, nullable=True)
    power_kw = Column(Float, nullable=True)
    meter_status = Column(String, nullable=True)
    comm_status = Column(String, nullable=True)

class TransformerReading(Base):
    __tablename__ = "transformer_readings"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transformer_id = Column(String, ForeignKey("transformers.id"), nullable=False)
    ts = Column(DateTime, nullable=False)
    kwh = Column(Float, nullable=False)

class Baseline(Base):
    __tablename__ = "baselines"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    consumer_id = Column(String, ForeignKey("consumers.id"), nullable=False)
    ts = Column(DateTime, nullable=False)
    expected_kwh = Column(Float, nullable=False)

class Label(Base):
    __tablename__ = "labels"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    consumer_id = Column(String, ForeignKey("consumers.id"), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    is_theft = Column(Boolean, nullable=False)

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    consumer_id = Column(String, ForeignKey("consumers.id"), nullable=False, unique=True)
    status = Column(String, nullable=False, default="Open")
    risk_level = Column(String, nullable=False)
    cause = Column(String, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    first_flagged_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    note = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    counter_evidence = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    estimated_loss = Column(Float, nullable=True)
    priority = Column(Float, nullable=True)

class CaseEvent(Base):
    __tablename__ = "case_events"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    event_type = Column(String, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    consumer_id = Column(String, ForeignKey("consumers.id"), nullable=False)
    risk_level = Column(String, nullable=False)
    cause = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class FeederSummary(Base):
    __tablename__ = "feeder_summary"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
<<<<<<< HEAD
    feeder_id = Column(String, ForeignKey("feeders.id"), nullable=True)
    transformer_id = Column(String, nullable=True)
    window_start = Column(String, nullable=True)
    window_end = Column(String, nullable=True)
    ts = Column(DateTime, nullable=True, default=datetime.utcnow)
    total_consumers = Column(Integer, nullable=True, default=0)
    high_risk_consumers = Column(Integer, nullable=True, default=0)
    total_consumption = Column(Float, nullable=True, default=0.0)
    avg_loss_pct = Column(Float, nullable=True, default=0.0)
    energy_in_kwh = Column(Float, nullable=True, default=0.0)
    energy_metered_kwh = Column(Float, nullable=True, default=0.0)
    unexplained_loss_pct = Column(Float, nullable=True, default=0.0)
    cluster_score = Column(Float, nullable=True, default=0.0)
    cluster_flag = Column(Integer, nullable=True, default=0)
=======
    feeder_id = Column(String, ForeignKey("feeders.id"), nullable=False)
    ts = Column(DateTime, nullable=False)
    total_consumers = Column(Integer, nullable=False)
    high_risk_consumers = Column(Integer, nullable=False)
    total_consumption = Column(Float, nullable=False, default=0.0)
    avg_loss_pct = Column(Float, nullable=False, default=0.0)
    transformer_id = Column(String, nullable=True)
    window_start = Column(String, nullable=True)
    window_end = Column(String, nullable=True)
    energy_in_kwh = Column(Float, nullable=True)
    energy_metered_kwh = Column(Float, nullable=True)
    unexplained_loss_pct = Column(Float, nullable=True)
    cluster_score = Column(Float, nullable=True)
    cluster_flag = Column(Integer, nullable=True)
>>>>>>> 533fc623c44f4b3e0f731bea39c6c27377d94866

class PipelineMetric(Base):
    __tablename__ = "pipeline_metrics"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    consumer_id = Column(String, ForeignKey("consumers.id"), nullable=False)
    ingest_to_detect_ms = Column(Float, nullable=False)
    detect_to_store_ms = Column(Float, nullable=False)
    ts = Column(DateTime, nullable=False, default=datetime.utcnow)
