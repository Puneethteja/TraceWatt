from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional

from ..db import list_feeders, get_feeder_summary
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
    # db.py get_feeder_summary actually only supports feeder_id and transformer_id depending on the implementation
    # Let's pass both and see if they are used
    summaries = get_feeder_summary(transformer_id=transformer_id, feeder_id=feeder_id)
    return summaries
