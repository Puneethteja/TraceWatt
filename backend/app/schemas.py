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
    evidence: str
    counter_evidence: str
    recommended_action: str

class CaseOut(BaseModel):
    id: int
    consumer_id: str
    status: str
    risk_level: str
    cause: str
    anomaly_score: float
    confidence: float
    first_flagged_at: datetime
    last_updated_at: datetime
    note: Optional[str] = None
    evidence: Optional[str] = None
    counter_evidence: Optional[str] = None
    recommended_action: Optional[str] = None
    estimated_loss: Optional[float] = None
    priority: Optional[float] = None

class CaseStatusUpdate(BaseModel):
    status: str
    note: Optional[str] = None

class ConsumerSummary(BaseModel):
    consumer_id: str
    category: str
    feeder_id: str
    transformer_id: str
    risk_level: Optional[str] = None
    status: Optional[str] = None
    anomaly_score: Optional[float] = None
    last_reading_ts: Optional[datetime] = None

class ConsumptionPoint(BaseModel):
    ts: datetime
    kwh: float

class BaselinePoint(BaseModel):
    ts: datetime
    expected_kwh: float

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
    created_at: datetime

class FeederOut(BaseModel):
    id: str
    name: str

class FeederSummaryOut(BaseModel):
    feeder_id: str
    total_consumers: int
    high_risk_consumers: int
    total_consumption: float
    avg_loss_pct: float
