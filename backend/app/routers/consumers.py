from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from ..db import list_consumers, get_consumption, get_baseline
from ..schemas import ConsumerSummary, ConsumptionPoint, BaselinePoint

router = APIRouter(prefix="/consumers", tags=["consumers"])

@router.get("", response_model=List[ConsumerSummary])
def get_consumers(
    risk: Optional[str] = Query(None, description="Filter by risk level"),
    feeder: Optional[str] = Query(None, description="Filter by feeder ID"),
    transformer: Optional[str] = Query(None, description="Filter by transformer ID"),
    category: Optional[str] = Query(None, description="Filter by consumer category"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    return list_consumers(risk=risk, feeder=feeder, transformer=transformer, category=category, limit=limit, offset=offset)

@router.get("/{consumer_id}/consumption", response_model=List[ConsumptionPoint])
def get_consumer_consumption(
    consumer_id: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    resample: str = Query("D", description="Resampling frequency")
):
    readings = get_consumption(consumer_id=consumer_id, start=start, end=end, resample=resample)
    if not readings:
        raise HTTPException(status_code=404, detail="No consumption data found for this consumer")
    
    # Return mapping to ConsumptionPoint
    return [{"ts": r.ts, "kwh": r.kwh if r.kwh is not None else 0.0} for r in readings]

@router.get("/{consumer_id}/baseline", response_model=List[BaselinePoint])
def get_consumer_baseline(consumer_id: str):
    baselines = get_baseline(consumer_id)
    if not baselines:
        raise HTTPException(status_code=404, detail="No baseline data found for this consumer")
    return [{"ts": b.ts, "expected_kwh": b.expected_kwh} for b in baselines]
