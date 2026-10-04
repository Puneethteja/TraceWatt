from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from ..db import list_alerts, update_alert_read_status, mark_all_alerts_read
from ..schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])

class AlertReadUpdate(BaseModel):
    is_read: Optional[bool] = True

@router.get("", response_model=List[AlertOut])
def get_alerts(
    since_id: int = Query(0, ge=0, description="Fetch alerts strictly after this ID"),
    limit: int = Query(50, ge=1, le=1000, description="Max number of alerts to return")
):
    return list_alerts(since_id=since_id, limit=limit)

@router.patch("/{alert_id}")
@router.patch("/{alert_id}/read")
def update_alert(alert_id: int, payload: Optional[AlertReadUpdate] = None):
    is_read = payload.is_read if payload is not None and payload.is_read is not None else True
    success = update_alert_read_status(alert_id, is_read=is_read)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"id": alert_id, "is_read": is_read, "status": "updated"}

@router.post("/mark-all-read")
def mark_all_read():
    count = mark_all_alerts_read()
    return {"marked_read": count}
