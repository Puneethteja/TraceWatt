from fastapi import APIRouter, HTTPException, Query, Response
from typing import List, Optional

from ..db import export_cases, get_case, list_consumers, get_baseline, get_consumption, SessionLocal
from ..models import Consumer
from ..schemas import CaseOut
from ..services.report_pdf import render_report

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/cases", response_model=List[CaseOut])
def export_cases_route():
    cases = export_cases(filters=None)
    return cases

@router.get("/cases/{consumer_id}/pdf")
def export_case_pdf(consumer_id: str):
    case = get_case(consumer_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    db = SessionLocal()
    try:
        consumer = db.query(Consumer).filter(Consumer.id == consumer_id).first()
        if not consumer:
            raise HTTPException(status_code=404, detail="Consumer not found")
    finally:
        db.close()
        
    baseline = get_baseline(consumer_id)
    readings = get_consumption(consumer_id)
    
    pdf_bytes = render_report(case=case, consumer=consumer, baseline=baseline, readings=readings)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="TraceWatt-{consumer_id}.pdf"'},
    )
