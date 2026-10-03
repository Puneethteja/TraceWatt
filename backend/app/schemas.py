from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ReadingIn(BaseModel):
    consumer_id: str
    ts: datetime
    kwh: Optional[float] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_kw: Optional[float] = None
    meter_status: Optional[str] = None
    comm_status: Optional[str] = None

class ReadingAck(BaseModel):
    stored: bool
    queued: bool

class Detection(BaseModel):
    consumer_id: str
    anomaly_score: float
    risk_level: str
    cause: str
    confidence: float
    period_start: datetime
    period_end: datetime
    baseline_kwh: float
    actual_kwh: float
    deviation_pct: float
    evidence: Any
    counter_evidence: Any
    recommended_action: str

class CaseOut(BaseModel):
    id: Optional[int] = None
    case_id: Optional[str] = None
    consumer_id: str
    status: str
    risk_level: str
    cause: str
    anomaly_score: float
    confidence: Optional[float] = 0.90
    first_flagged_at: Optional[Any] = None
    last_updated: Optional[str] = None
    last_updated_at: Optional[Any] = None
    note: Optional[str] = None
    evidence: Optional[Any] = None
    counter_evidence: Optional[Any] = None
    recommended_action: Optional[str] = None
    estimated_loss: Optional[float] = 0.0
    priority_rank: Optional[int] = None
    priority: Optional[float] = None

class CaseStatusUpdate(BaseModel):
    status: str
    note: Optional[str] = None

class ConsumerSummary(BaseModel):
    consumer_id: str
    category: str
    feeder_id: str
    transformer_id: str
    meter_id: Optional[str] = None
    risk_level: Optional[str] = None
    status: Optional[str] = None
    cause: Optional[str] = None
    anomaly_score: Optional[float] = None
    confidence: Optional[float] = None
    estimated_loss: Optional[float] = None
    priority_rank: Optional[int] = None
    tariff: Optional[str] = None
    sanctioned_load_kw: Optional[float] = None

class ConsumptionPoint(BaseModel):
    ts: Optional[Any] = None
    date: Optional[str] = None
    kwh: float
    baseline_kwh: Optional[float] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_kw: Optional[float] = None

class BaselinePoint(BaseModel):
    ts: Optional[Any] = None
    expected_kwh: float
    baseline_kwh: Optional[float] = None

class CaseEventOut(BaseModel):
    id: int
    case_id: int
    event_type: str
    note: Optional[str] = None
    created_at: datetime

class AlertOut(BaseModel):
    id: int
    consumer_id: str
    risk_level: str
    cause: str
    message: str
    is_read: bool
    ts: Optional[str] = None
    created_at: Optional[Any] = None

class FeederOut(BaseModel):
    id: str
    feeder_id: Optional[str] = None
    name: str
    transformer_count: Optional[int] = 0
    consumer_count: Optional[int] = 0
    high_risk_consumers: Optional[int] = 0
    total_unexplained_loss_pct: Optional[float] = 0.0
    unexplained_loss_pct: Optional[float] = 0.0
    cluster_flag: Optional[bool] = False

class FeederSummaryOut(BaseModel):
    feeder_id: str
    total_consumers: int
    high_risk_consumers: int
    total_consumption: float
    avg_loss_pct: float
