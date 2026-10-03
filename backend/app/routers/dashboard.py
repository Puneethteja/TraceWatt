from fastapi import APIRouter
from typing import List, Dict, Any

from ..db import get_dashboard_summary, get_consumption_trend, get_risk_distribution

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
def dashboard_summary():
    return get_dashboard_summary()

@router.get("/consumption-trend")
def dashboard_consumption_trend():
    return get_consumption_trend()

@router.get("/risk-distribution")
def dashboard_risk_distribution():
    return get_risk_distribution()
