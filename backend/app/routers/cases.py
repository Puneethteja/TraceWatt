from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..db import list_cases, get_case, update_case_status
from ..schemas import CaseOut, CaseStatusUpdate

router = APIRouter(prefix="/cases", tags=["cases"])

ALLOWED_STATUSES = ["New", "Under Review", "Inspection Scheduled", "Confirmed", "False Alarm", "Closed", "Open"]

@router.get("", response_model=List[CaseOut])
def get_all_cases(
    status: Optional[str] = Query(None, description="Filter by status"),
    risk: Optional[str] = Query(None, description="Filter by risk level"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    return list_cases(status=status, risk=risk, limit=limit, offset=offset)

@router.get("/{consumer_id}", response_model=CaseOut)
def get_case_by_consumer(consumer_id: str):
    case = get_case(consumer_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.patch("/{consumer_id}/status", response_model=CaseOut)
def update_case_status_route(consumer_id: str, payload: CaseStatusUpdate):
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Allowed values: {ALLOWED_STATUSES}")
    
    success = update_case_status(consumer_id=consumer_id, status=payload.status, note=payload.note)
    if not success:
        raise HTTPException(status_code=404, detail="Case not found")
        
    return get_case(consumer_id)
