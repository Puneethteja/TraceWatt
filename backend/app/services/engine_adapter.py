"""
backend/app/services/engine_adapter.py
=======================================
TraceWatt Phase-4: DB-to-DataFrame adapter wrapping analyze().

Loads models once at startup (singleton). Provides:
    score_consumer(session, consumer_id) -> dict   (Detection)
    score_all(session)                  -> list[dict]
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Ensure backend root on path for engine imports
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from engine.analyze import analyze, analyze_all, _load_models  # noqa: E402
from app.models import Consumer, Reading, Baseline  # noqa: E402
from app.services.loss import rank_cases  # noqa: E402

# ── Pre-load models (called at import time → once per process) ───────────────
try:
    _load_models()
except FileNotFoundError:
    # Models may not be trained yet during testing — deferred loading
    pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _readings_to_df(readings: list) -> pd.DataFrame:
    """Convert a list of Reading ORM objects to a DataFrame."""
    if not readings:
        return pd.DataFrame(columns=["consumer_id", "ts", "kwh", "meter_status", "comm_status"])

    rows = []
    for r in readings:
        rows.append({
            "consumer_id": r.consumer_id,
            "ts": r.ts,
            "kwh": r.kwh,
            "voltage": getattr(r, "voltage", None),
            "current": getattr(r, "current", None),
            "power_kw": getattr(r, "power_kw", None),
            "meter_status": getattr(r, "meter_status", None) or "OK",
            "comm_status": getattr(r, "comm_status", None) or "OK",
        })
    return pd.DataFrame(rows)


def _baselines_to_df(baselines: list) -> "pd.DataFrame | None":
    """Convert a list of Baseline ORM objects to a DataFrame."""
    if not baselines:
        return None
    rows = [{"ts": b.ts, "expected_kwh": b.expected_kwh} for b in baselines]
    return pd.DataFrame(rows)


def _consumer_to_dict(consumer: "Consumer") -> dict:
    """Convert a Consumer ORM object to a plain dict."""
    return {
        "consumer_id": consumer.id,
        "category": getattr(consumer, "category", "residential"),
        "feeder_id": getattr(consumer, "feeder_id", ""),
        "transformer_id": getattr(consumer, "transformer_id", ""),
        "tariff": getattr(consumer, "tariff", 0.15),
        "sanctioned_load_kw": getattr(consumer, "sanctioned_load_kw", 10.0),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_consumer(session, consumer_id: str) -> dict:
    """
    Score a single consumer using all available readings and baseline.

    Parameters
    ----------
    session     : SQLAlchemy Session (open, managed by caller).
    consumer_id : str — Consumer primary key.

    Returns
    -------
    dict — Detection result adhering to schemas.Detection.
           Returns a safe stub if consumer or readings not found.
    """
    from datetime import datetime, timezone

    # Load consumer
    consumer = session.query(Consumer).filter(Consumer.id == consumer_id).first()
    if not consumer:
        return _stub_detection(consumer_id, reason="Consumer not found")

    # Load readings (last 500 or WINDOW_ROWS, order asc)
    from app.config import WINDOW_ROWS
    readings = (
        session.query(Reading)
        .filter(Reading.consumer_id == consumer_id)
        .order_by(Reading.ts.desc())
        .limit(max(WINDOW_ROWS, 500))
        .all()
    )
    readings = list(reversed(readings))  # put back in chronological order

    readings_df = _readings_to_df(readings)

    # Load baseline
    baselines = (
        session.query(Baseline)
        .filter(Baseline.consumer_id == consumer_id)
        .order_by(Baseline.ts)
        .all()
    )
    baseline_df = _baselines_to_df(baselines)

    consumer_row = _consumer_to_dict(consumer)

    return analyze(consumer_id, readings_df, consumer_row, baseline_df)


def score_all(session) -> list[dict]:
    """
    Score all consumers in the database.

    Parameters
    ----------
    session : SQLAlchemy Session (open, managed by caller).

    Returns
    -------
    list[dict] — Detection dicts sorted by priority_rank ascending.
    """
    consumers = session.query(Consumer).all()
    results: list[dict] = []

    for consumer in consumers:
        try:
            det = score_consumer(session, consumer.id)
            results.append(det)
        except Exception:
            results.append(_stub_detection(consumer.id, reason="Inference error"))

    # Apply ranking across all results
    results = rank_cases(results)
    return results


def _stub_detection(consumer_id: str, reason: str = "No data") -> dict:
    """Return a safe stub Detection dict for consumers with no data."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return {
        "consumer_id": consumer_id,
        "anomaly_score": 0.0,
        "risk_level": "Low",
        "cause": "Requires Review",
        "confidence": 0.0,
        "period_start": now,
        "period_end": now,
        "baseline_kwh": 0.0,
        "actual_kwh": 0.0,
        "deviation_pct": 0.0,
        "evidence": reason,
        "counter_evidence": "Insufficient data to generate counter-evidence.",
        "recommended_action": "Collect more readings before scoring.",
        "estimated_loss": 0.0,
        "priority_rank": None,
        "_priority_score": 0.0,
    }
