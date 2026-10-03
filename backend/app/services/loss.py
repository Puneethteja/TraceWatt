"""
backend/app/services/loss.py
============================
TraceWatt Phase-4: Pure loss calculation and priority ranking functions.

All functions are stateless and side-effect free — safe to unit test directly.

Formulas (from PRD contracts):
  estimated_loss  = max(baseline_kwh - actual_kwh, 0.0) * tariff
  priority_score  = anomaly_score * confidence * estimated_loss
  rank_cases()    : sort descending by priority_score → assign 1-based priority_rank
"""

from __future__ import annotations

from typing import Sequence

# Default tariff (₹ per kWh) when consumer metadata does not provide one
TARIFF_DEFAULT: float = 0.15


def compute_loss(
    baseline_kwh: float,
    actual_kwh: float,
    tariff: float = TARIFF_DEFAULT,
) -> float:
    """
    Compute estimated financial loss for a consumer.

    Parameters
    ----------
    baseline_kwh : float — Expected consumption (kWh) for the period.
    actual_kwh   : float — Recorded/metered consumption (kWh).
    tariff       : float — Rate in currency per kWh (default 0.15).

    Returns
    -------
    float — Estimated loss ≥ 0.0.
            Returns 0.0 when actual ≥ baseline (no loss situation).
    """
    return max(float(baseline_kwh) - float(actual_kwh), 0.0) * float(tariff)


def priority_score(
    anomaly_score: float,
    confidence: float,
    estimated_loss: float,
) -> float:
    """
    Compute a priority score for a detected case.

    Higher score ↔ higher urgency for field action.

    Parameters
    ----------
    anomaly_score   : float in [0, 1] — ML anomaly confidence.
    confidence      : float in [0, 1] — Cause classification confidence.
    estimated_loss  : float ≥ 0 — Estimated financial loss (from compute_loss).

    Returns
    -------
    float — Priority score ≥ 0.0.
    """
    return float(anomaly_score) * float(confidence) * float(estimated_loss)


def rank_cases(cases: "list[dict]") -> "list[dict]":
    """
    Sort detection cases by priority and assign 1-based integer priority_rank.

    Sorting is descending by `_priority_score` (if present) or computed from
    anomaly_score × confidence × estimated_loss. Ties are broken by consumer_id
    for determinism.

    Parameters
    ----------
    cases : list[dict] — Detection dicts (as returned by analyze()).

    Returns
    -------
    list[dict] — Same dicts, each with `priority_rank` set (int, 1-based).
                 Returned list is sorted descending by priority score.
    """
    if not cases:
        return cases

    def _score(c: dict) -> float:
        if "_priority_score" in c:
            return float(c["_priority_score"])
        return priority_score(
            float(c.get("anomaly_score", 0.0)),
            float(c.get("confidence", 0.0)),
            float(c.get("estimated_loss", 0.0)),
        )

    sorted_cases = sorted(
        cases,
        key=lambda c: (_score(c), str(c.get("consumer_id", ""))),
        reverse=True,
    )

    for rank, case in enumerate(sorted_cases, start=1):
        case["priority_rank"] = rank

    return sorted_cases
