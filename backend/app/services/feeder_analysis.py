"""
backend/app/services/feeder_analysis.py
=======================================
Re-exports feeder analysis from backend/services/feeder_analysis.py (PRD 16.2).
"""

from backend.services.feeder_analysis import (
    compute_feeder_balance,
    run_feeder_analysis,
    FEEDER_SUMMARY_COLUMNS,
    ASSUMPTIONS,
)

__all__ = [
    "compute_feeder_balance",
    "run_feeder_analysis",
    "FEEDER_SUMMARY_COLUMNS",
    "ASSUMPTIONS",
]
