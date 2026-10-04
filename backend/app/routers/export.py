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

@router.get("/cases/{consumer_id}/report")
def export_case_report(consumer_id: str):
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
    
    base_vals = [
        float(b.expected_kwh if hasattr(b, "expected_kwh") else b.get("expected_kwh", 10.5))
        for b in (baseline or [])
    ]
    avg_base = sum(base_vals) / len(base_vals) if base_vals else 10.5
    
    actual_vals = [float(r.kwh if hasattr(r, "kwh") else r.get("kwh", 0)) for r in (readings or []) if (r.kwh if hasattr(r, "kwh") else r.get("kwh")) is not None]
    avg_actual = sum(actual_vals) / len(actual_vals) if actual_vals else avg_base
    recent_actual = sum(actual_vals[-14:]) / len(actual_vals[-14:]) if len(actual_vals) >= 14 else avg_actual
    
    diff_kwh = recent_actual - avg_base
    deviation_pct = (diff_kwh / avg_base) * 100 if avg_base > 0 else 0.0
    
    if recent_actual < 0.1 and avg_base > 2.0:
        pattern = "Zero Flatline (Sensor Inactive or Complete Bypass)"
        pattern_desc = "Consumer power draw has completely dropped to zero while upstream line is energized."
    elif deviation_pct < -35:
        pattern = "Abrupt Step Down (Suspected Shunt/Bypass)"
        pattern_desc = "Sudden structural downward shift in daily load compared to established baseline."
    elif deviation_pct > 35:
        pattern = "Elevated Abnormal Draw (Unregistered Load)"
        pattern_desc = "Unusual surge exceeding sanctioned capacity and baseline expectations."
    elif abs(deviation_pct) <= 15:
        pattern = "Stable Periodic Tracking (Normal Profile)"
        pattern_desc = "Consumption closely matches expected historical curve and diurnal cycles."
    else:
        pattern = "Seasonal / Moderate Load Variance"
        pattern_desc = "Moderate variance within acceptable seasonal fluctuation bands."
        
    import json
    def _parse_list(val):
        if not val:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return parsed
                return [val]
            except Exception:
                return [val]
        return [str(val)]

    evidence = _parse_list(getattr(case, "evidence", None))
    counter_evidence = _parse_list(getattr(case, "counter_evidence", None))
    
    meter_id = f"MTR-{str(consumer_id).replace('SYN_', '').replace('CONS-', '').replace('CUS_', '')}"
    
    return {
        "consumer_details": {
            "consumer_id": consumer.id,
            "meter_id": meter_id,
            "category": consumer.category,
            "feeder_id": consumer.feeder_id,
            "transformer_id": consumer.transformer_id,
            "sanctioned_load_kw": getattr(consumer, "sanctioned_load_kw", None),
            "tariff": getattr(consumer, "tariff", 0.15),
        },
        "consumption_comparison": {
            "historical_baseline_kwh": round(avg_base, 2),
            "current_consumption_kwh": round(recent_actual, 2),
            "deviation_kwh": round(diff_kwh, 2),
            "deviation_pct": round(deviation_pct, 1),
            "time_period": "Past 120-Day Continuous Ingestion (Focus: 14-day analysis window)",
            "period_start": str(getattr(case, "period_start", None)) if getattr(case, "period_start", None) else None,
            "period_end": str(getattr(case, "period_end", None)) if getattr(case, "period_end", None) else None,
            "reading_count": len(actual_vals),
        },
        "anomaly_assessment": {
            "anomaly_score": getattr(case, "anomaly_score", None),
            "confidence": getattr(case, "confidence", None),
            "risk_level": getattr(case, "risk_level", None),
            "probable_cause": getattr(case, "cause", None),
            "status": getattr(case, "status", None),
            "priority": getattr(case, "priority", None),
            "estimated_loss_inr": getattr(case, "estimated_loss", None),
            "first_flagged_at": str(getattr(case, "first_flagged_at", None)) if getattr(case, "first_flagged_at", None) else None,
            "last_updated_at": str(getattr(case, "last_updated_at", None)) if getattr(case, "last_updated_at", None) else None,
        },
        "behavioural_pattern": {
            "name": pattern,
            "description": pattern_desc,
        },
        "supporting_features": {
            "drop_ratio": round(abs(diff_kwh) / max(avg_base, 0.01), 3),
            "mean_baseline_kwh": round(avg_base, 2),
            "recent_mean_kwh": round(recent_actual, 2),
            "zero_reading_pct": round(sum(1 for v in actual_vals[-14:] if v < 0.05) / max(len(actual_vals[-14:]), 1) * 100, 1),
            "deviation_pct": round(deviation_pct, 1),
        },
        "explainability": {
            "why_flagged": (
                f"Consumer was flagged as {getattr(case, 'risk_level', 'High')} risk due to {pattern.lower()}. "
                f"Observed draw of {recent_actual:.2f} kWh/day deviates by {deviation_pct:+.1f}% from historical baseline ({avg_base:.2f} kWh/day). "
                f"Attributed to '{getattr(case, 'cause', 'Suspected anomaly')}' with {float(getattr(case, 'confidence', 0.8) or 0.8)*100:.0f}% confidence."
            ),
            "evidence": evidence,
            "counter_evidence": counter_evidence,
        },
        "recommended_inspection": {
            "action": getattr(case, "recommended_action", None) or "Dispatch field team for tamper seal verification and CT test.",
            "priority": getattr(case, "risk_level", "High"),
            "assigned_team": "Field Anti-Theft & Meter Audit Unit",
            "notes": getattr(case, "note", "") or "",
        },
    }

