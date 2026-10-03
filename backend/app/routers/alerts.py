from fastapi import APIRouter, Query
from typing import List

from ..db import list_alerts
from ..schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=List[AlertOut])
def get_alerts(
    since_id: int = Query(0, ge=0, description="Fetch alerts strictly after this ID"),
    limit: int = Query(50, ge=1, le=1000, description="Max number of alerts to return")
):
    return list_alerts(since_id=since_id, limit=limit)
