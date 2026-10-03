from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Any

from ..db import list_feeders, get_feeder_summary, get_feeder_losses
from ..schemas import FeederOut, FeederSummaryOut

router = APIRouter(prefix="/feeders", tags=["feeders"])

@router.get("", response_model=List[FeederOut])
def get_feeders():
    return list_feeders()

@router.get("/summary", response_model=List[FeederSummaryOut])
def get_feeder_summaries(
    transformer_id: Optional[str] = Query(None, description="Filter by transformer ID"),
    feeder_id: Optional[str] = Query(None, description="Filter by feeder ID")
):
    return get_feeder_summary(transformer_id=transformer_id, feeder_id=feeder_id)

@router.get("/{feeder_id}", response_model=FeederOut)
def get_single_feeder(feeder_id: str):
    feeders = list_feeders()
    for f in feeders:
        if f["id"] == feeder_id or f.get("feeder_id") == feeder_id:
            return f
    raise HTTPException(status_code=404, detail="Feeder not found")

@router.get("/{feeder_id}/losses")
def get_feeder_losses_route(feeder_id: str):
    return get_feeder_losses(feeder_id)
