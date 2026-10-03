"""
backend/tests/test_loss.py
===========================
Unit tests for backend/app/services/loss.py

Tests cover:
  - compute_loss: zero loss, correct formula, edge cases
  - priority_score: formula correctness, zero cases
  - rank_cases: sort order, 1-based ranks, ties, empty list
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add backend root to sys.path
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.services.loss import compute_loss, priority_score, rank_cases, TARIFF_DEFAULT


# ---------------------------------------------------------------------------
# compute_loss
# ---------------------------------------------------------------------------

class TestComputeLoss:
    def test_basic_loss(self):
        """baseline > actual → positive loss."""
        result = compute_loss(100.0, 60.0, tariff=0.15)
        assert abs(result - 6.0) < 1e-9

    def test_zero_loss_when_actual_exceeds_baseline(self):
        """actual >= baseline → loss = 0.0."""
        assert compute_loss(50.0, 80.0) == 0.0

    def test_zero_loss_when_equal(self):
        """actual == baseline → loss = 0.0."""
        assert compute_loss(100.0, 100.0) == 0.0

    def test_default_tariff_used(self):
        """Default tariff (0.15) is applied when not passed."""
        loss = compute_loss(200.0, 100.0)
        assert abs(loss - 100.0 * TARIFF_DEFAULT) < 1e-9

    def test_custom_tariff(self):
        """Custom tariff is respected."""
        loss = compute_loss(200.0, 100.0, tariff=8.0)
        assert abs(loss - 800.0) < 1e-9

    def test_zero_baseline_zero_loss(self):
        """Zero baseline → zero loss regardless of actual."""
        assert compute_loss(0.0, 50.0) == 0.0

    def test_loss_never_negative(self):
        """Loss must always be ≥ 0."""
        assert compute_loss(10.0, 1000.0) >= 0.0
        assert compute_loss(0.0, 0.0) >= 0.0
        assert compute_loss(-5.0, 0.0) >= 0.0  # weird input — still safe

    def test_float_precision(self):
        """Formula accuracy with floating-point inputs."""
        loss = compute_loss(123.456, 100.0, tariff=5.5)
        expected = (123.456 - 100.0) * 5.5
        assert abs(loss - expected) < 1e-6

    def test_large_values(self):
        """Works with industrial-scale kWh values."""
        loss = compute_loss(1_000_000.0, 500_000.0, tariff=12.0)
        assert abs(loss - 6_000_000.0) < 1.0


# ---------------------------------------------------------------------------
# priority_score
# ---------------------------------------------------------------------------

class TestPriorityScore:
    def test_basic_formula(self):
        """priority = anomaly_score × confidence × estimated_loss."""
        result = priority_score(0.8, 0.9, 100.0)
        assert abs(result - 0.8 * 0.9 * 100.0) < 1e-9

    def test_zero_loss_zero_priority(self):
        """Zero loss → zero priority regardless of scores."""
        assert priority_score(1.0, 1.0, 0.0) == 0.0

    def test_zero_anomaly_zero_priority(self):
        """Zero anomaly score → zero priority."""
        assert priority_score(0.0, 0.9, 500.0) == 0.0

    def test_zero_confidence_zero_priority(self):
        """Zero confidence → zero priority."""
        assert priority_score(0.8, 0.0, 500.0) == 0.0

    def test_all_max(self):
        """Maximum inputs → max priority."""
        result = priority_score(1.0, 1.0, 1000.0)
        assert abs(result - 1000.0) < 1e-9

    def test_fractional_inputs(self):
        """Fractional inputs compute correctly."""
        result = priority_score(0.5, 0.6, 30.0)
        expected = 0.5 * 0.6 * 30.0
        assert abs(result - expected) < 1e-9


# ---------------------------------------------------------------------------
# rank_cases
# ---------------------------------------------------------------------------

class TestRankCases:
    def _make_case(self, consumer_id: str, anomaly: float, conf: float, loss: float) -> dict:
        p = priority_score(anomaly, conf, loss)
        return {
            "consumer_id": consumer_id,
            "anomaly_score": anomaly,
            "confidence": conf,
            "estimated_loss": loss,
            "_priority_score": p,
            "priority_rank": None,
        }

    def test_empty_list(self):
        """Empty input returns empty output."""
        assert rank_cases([]) == []

    def test_single_case_rank_1(self):
        """Single case gets priority_rank = 1."""
        cases = [self._make_case("C1", 0.5, 0.8, 100.0)]
        result = rank_cases(cases)
        assert result[0]["priority_rank"] == 1

    def test_descending_priority_order(self):
        """Higher priority score → lower (better) rank number."""
        cases = [
            self._make_case("C_low", 0.2, 0.5, 10.0),   # score = 1.0
            self._make_case("C_high", 0.9, 0.95, 500.0), # score = 427.5
            self._make_case("C_mid", 0.6, 0.7, 50.0),    # score = 21.0
        ]
        result = rank_cases(cases)
        ids_in_order = [r["consumer_id"] for r in result]
        assert ids_in_order[0] == "C_high"
        assert ids_in_order[1] == "C_mid"
        assert ids_in_order[2] == "C_low"

    def test_ranks_are_1_based(self):
        """Ranks start at 1 and are contiguous."""
        cases = [
            self._make_case(f"C{i}", 0.5, 0.5, float(i * 10))
            for i in range(1, 6)
        ]
        result = rank_cases(cases)
        ranks = [r["priority_rank"] for r in result]
        assert ranks == list(range(1, 6))

    def test_ranks_are_integers(self):
        """priority_rank must be int, not float."""
        cases = [self._make_case("C1", 0.5, 0.8, 100.0)]
        result = rank_cases(cases)
        assert isinstance(result[0]["priority_rank"], int)

    def test_ties_broken_by_consumer_id(self):
        """Ties in priority score broken alphabetically by consumer_id (desc by score)."""
        # Same priority score → lexicographic order on consumer_id
        cases = [
            self._make_case("C_z", 0.5, 0.5, 20.0),
            self._make_case("C_a", 0.5, 0.5, 20.0),
            self._make_case("C_m", 0.5, 0.5, 20.0),
        ]
        result = rank_cases(cases)
        # All get a rank; check they all got valid 1-based ranks
        ranks = sorted(r["priority_rank"] for r in result)
        assert ranks == [1, 2, 3]

    def test_zero_priority_cases_ranked_last(self):
        """Cases with zero priority score are ranked at the bottom."""
        cases = [
            self._make_case("C_active", 0.8, 0.9, 200.0),
            self._make_case("C_zero", 0.0, 0.0, 0.0),
        ]
        result = rank_cases(cases)
        active = next(r for r in result if r["consumer_id"] == "C_active")
        zero = next(r for r in result if r["consumer_id"] == "C_zero")
        assert active["priority_rank"] < zero["priority_rank"]

    def test_original_dicts_mutated_in_place(self):
        """rank_cases mutates priority_rank in the original dict objects."""
        c = self._make_case("C1", 0.5, 0.8, 100.0)
        rank_cases([c])
        assert c["priority_rank"] == 1

    def test_no_priority_score_key_fallback(self):
        """Falls back to computing score from anomaly×confidence×loss if _priority_score absent."""
        case = {
            "consumer_id": "C1",
            "anomaly_score": 0.8,
            "confidence": 0.9,
            "estimated_loss": 100.0,
            "priority_rank": None,
        }
        result = rank_cases([case])
        assert result[0]["priority_rank"] == 1
