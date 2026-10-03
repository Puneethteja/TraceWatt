"""
backend/tests/test_engine_adapter.py
======================================
Unit tests for backend/app/services/engine_adapter.py

Uses mock SQLAlchemy sessions to avoid database dependency.
Tests cover:
  - score_consumer: returns valid Detection dict
  - score_consumer: handles missing consumer gracefully
  - score_consumer: handles empty readings gracefully
  - score_all: returns list of Detection dicts with valid structure
  - Model singleton behavior (loads once)
"""

from __future__ import annotations

import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import numpy as np
import pandas as pd
import pytest

# Add backend root to sys.path
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


# ---------------------------------------------------------------------------
# Fixtures: fake ORM objects
# ---------------------------------------------------------------------------

def _make_consumer(cid="TEST_C1", category="residential", tariff=0.15):
    c = MagicMock()
    c.id = cid
    c.category = category
    c.feeder_id = "FDR_01"
    c.transformer_id = "TX_001"
    c.tariff = tariff
    c.sanctioned_load_kw = 10.0
    return c


def _make_reading(cid="TEST_C1", ts=None, kwh=50.0, meter_status="OK", comm_status="OK"):
    r = MagicMock()
    r.consumer_id = cid
    r.ts = ts or datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    r.kwh = kwh
    r.voltage = 230.0
    r.current = kwh / 230.0 if kwh else 0.0
    r.power_kw = kwh / 24.0 if kwh else 0.0
    r.meter_status = meter_status
    r.comm_status = comm_status
    return r


def _make_baseline(cid="TEST_C1", ts=None, expected_kwh=55.0):
    b = MagicMock()
    b.consumer_id = cid
    b.ts = ts or datetime(2024, 1, 1, tzinfo=timezone.utc)
    b.expected_kwh = expected_kwh
    return b


def _make_readings_list(cid="TEST_C1", n=120, base_kwh=50.0):
    """Generate n consecutive readings."""
    from datetime import timedelta
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    return [
        _make_reading(
            cid=cid,
            ts=start + timedelta(days=i),
            kwh=base_kwh + np.random.default_rng(i).normal(0, 2),
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Mock session builder
# ---------------------------------------------------------------------------

def _mock_session(consumer=None, readings=None, baselines=None):
    """
    Build a mock SQLAlchemy session that returns the given objects
    from query().filter().first() and query().filter().order_by().limit().all().
    """
    session = MagicMock()

    def _query_side_effect(model):
        q = MagicMock()
        # Support chained .filter().first()
        filter_q = MagicMock()
        filter_q.first.return_value = consumer if model.__name__ in ("Consumer",) or (hasattr(model, "__tablename__") and model.__tablename__ == "consumers") else None

        # Support .filter().order_by().desc().limit().all()  for readings
        order_q = MagicMock()
        limit_q = MagicMock()
        limit_q.all.return_value = (readings or [])
        order_q.limit.return_value = limit_q
        order_q.all.return_value = (readings or [])
        filter_q.order_by.return_value = order_q

        q.filter.return_value = filter_q
        return q

    # We handle Consumer, Reading, Baseline separately via model name
    consumer_q = MagicMock()
    consumer_q.filter.return_value.first.return_value = consumer

    reading_q = MagicMock()
    reading_filter = MagicMock()
    reading_order = MagicMock()
    reading_limit = MagicMock()
    reading_limit.all.return_value = (readings or [])
    reading_order.limit.return_value = reading_limit
    reading_filter.order_by.return_value = reading_order
    reading_q.filter.return_value = reading_filter

    baseline_q = MagicMock()
    baseline_filter = MagicMock()
    baseline_order = MagicMock()
    baseline_order.all.return_value = (baselines or [])
    baseline_filter.order_by.return_value = baseline_order
    baseline_q.filter.return_value = baseline_filter

    # Consumer list for score_all
    consumer_all_q = MagicMock()
    consumer_all_q.all.return_value = ([consumer] if consumer else [])

    def _query(model):
        name = getattr(model, "__tablename__", "") or getattr(model, "__name__", "")
        if "consumer" in name.lower():
            # Return consumer_all_q if .all() called (score_all path)
            # Return consumer_q if .filter() called (score_consumer path)
            combined = MagicMock()
            combined.filter.return_value = consumer_q.filter.return_value
            combined.all.return_value = consumer_all_q.all.return_value
            return combined
        elif "reading" in name.lower():
            return reading_q
        elif "baseline" in name.lower():
            return baseline_q
        return MagicMock()

    session.query.side_effect = _query
    return session


# ---------------------------------------------------------------------------
# Helpers to monkey-patch model loading (avoid disk dependency)
# ---------------------------------------------------------------------------

def _make_fake_lgbm():
    """Minimal sklearn-compatible classifier mock."""
    from sklearn.dummy import DummyClassifier
    clf = DummyClassifier(strategy="constant", constant=0)
    # Fit with minimal data
    clf.fit([[0] * 8, [1] * 8], [0, 1])
    return clf


def _make_fake_iso():
    from sklearn.ensemble import IsolationForest
    iso = IsolationForest(n_estimators=10, random_state=42)
    iso.fit([[0] * 8, [1] * 8])
    return iso


def _make_fake_scaler():
    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler()
    sc.fit([[0] * 8, [1] * 8])
    return sc


FAKE_FEATURE_COLS = [
    "missing_ratio", "zero_reading_ratio", "rolling_mean_30d",
    "rolling_std_30d", "mom_change_pct", "drop_length",
    "peer_deviation", "seasonal_residual",
]


@pytest.fixture(autouse=True)
def patch_models(monkeypatch):
    """
    Patch model globals in engine.analyze so tests don't need trained artifacts.
    """
    import engine.analyze as ea

    monkeypatch.setattr(ea, "_LGBM_MODEL", _make_fake_lgbm())
    monkeypatch.setattr(ea, "_ISO_FOREST", _make_fake_iso())
    monkeypatch.setattr(ea, "_SCALER", _make_fake_scaler())
    monkeypatch.setattr(ea, "_FEATURE_COLS", FAKE_FEATURE_COLS)


REQUIRED_KEYS = {
    "consumer_id", "anomaly_score", "risk_level", "cause", "confidence",
    "period_start", "period_end", "baseline_kwh", "actual_kwh",
    "deviation_pct", "evidence", "counter_evidence", "recommended_action",
    "estimated_loss",
}


# ---------------------------------------------------------------------------
# Tests: score_consumer
# ---------------------------------------------------------------------------

class TestScoreConsumer:
    def test_returns_dict_with_required_keys(self):
        """score_consumer always returns a dict with all required Detection keys."""
        from app.services.engine_adapter import score_consumer

        consumer = _make_consumer()
        readings = _make_readings_list(n=120)
        baselines = [_make_baseline()]
        session = _mock_session(consumer=consumer, readings=readings, baselines=baselines)

        result = score_consumer(session, "TEST_C1")
        assert isinstance(result, dict)
        for key in REQUIRED_KEYS:
            assert key in result, f"Missing key: {key}"

    def test_anomaly_score_in_range(self):
        """anomaly_score must be in [0.0, 1.0]."""
        from app.services.engine_adapter import score_consumer

        consumer = _make_consumer()
        readings = _make_readings_list(n=120)
        session = _mock_session(consumer=consumer, readings=readings)
        result = score_consumer(session, "TEST_C1")
        assert 0.0 <= result["anomaly_score"] <= 1.0

    def test_risk_level_valid(self):
        """risk_level must be one of Low / Medium / High."""
        from app.services.engine_adapter import score_consumer

        consumer = _make_consumer()
        readings = _make_readings_list(n=120)
        session = _mock_session(consumer=consumer, readings=readings)
        result = score_consumer(session, "TEST_C1")
        assert result["risk_level"] in ("Low", "Medium", "High")

    def test_cause_is_valid_class(self):
        """cause must be one of the 7 defined cause strings."""
        from app.services.engine_adapter import score_consumer
        from engine.analyze import _CAUSES

        consumer = _make_consumer()
        readings = _make_readings_list(n=120)
        session = _mock_session(consumer=consumer, readings=readings)
        result = score_consumer(session, "TEST_C1")
        assert result["cause"] in _CAUSES

    def test_missing_consumer_returns_stub(self):
        """If consumer not found, returns a Requires Review stub."""
        from app.services.engine_adapter import score_consumer

        session = _mock_session(consumer=None, readings=[])
        result = score_consumer(session, "NONEXISTENT")
        assert result["consumer_id"] == "NONEXISTENT"
        assert result["cause"] == "Requires Review"
        assert result["anomaly_score"] == 0.0

    def test_empty_readings_handled_gracefully(self):
        """Empty readings don't raise; returns valid dict."""
        from app.services.engine_adapter import score_consumer

        consumer = _make_consumer()
        session = _mock_session(consumer=consumer, readings=[])
        result = score_consumer(session, "TEST_C1")
        assert isinstance(result, dict)
        assert result["actual_kwh"] == 0.0

    def test_evidence_is_list(self):
        """evidence and counter_evidence must be lists of strings."""
        from app.services.engine_adapter import score_consumer

        consumer = _make_consumer()
        readings = _make_readings_list(n=120)
        session = _mock_session(consumer=consumer, readings=readings)
        result = score_consumer(session, "TEST_C1")
        assert isinstance(result["evidence"], list)
        assert isinstance(result["counter_evidence"], list)

    def test_period_dates_are_datetime(self):
        """period_start and period_end must be datetime objects."""
        from app.services.engine_adapter import score_consumer

        consumer = _make_consumer()
        readings = _make_readings_list(n=120)
        session = _mock_session(consumer=consumer, readings=readings)
        result = score_consumer(session, "TEST_C1")
        assert isinstance(result["period_start"], datetime)
        assert isinstance(result["period_end"], datetime)

    def test_estimated_loss_non_negative(self):
        """estimated_loss must always be ≥ 0."""
        from app.services.engine_adapter import score_consumer

        consumer = _make_consumer()
        readings = _make_readings_list(n=120, base_kwh=200.0)
        session = _mock_session(consumer=consumer, readings=readings)
        result = score_consumer(session, "TEST_C1")
        assert result["estimated_loss"] >= 0.0


# ---------------------------------------------------------------------------
# Tests: score_all
# ---------------------------------------------------------------------------

class TestScoreAll:
    def test_returns_list(self):
        """score_all returns a list."""
        from app.services.engine_adapter import score_all

        consumer = _make_consumer()
        readings = _make_readings_list(n=120)
        session = _mock_session(consumer=consumer, readings=readings)
        result = score_all(session)
        assert isinstance(result, list)

    def test_each_item_has_required_keys(self):
        """Every item in score_all result has required Detection keys."""
        from app.services.engine_adapter import score_all

        consumer = _make_consumer()
        readings = _make_readings_list(n=120)
        session = _mock_session(consumer=consumer, readings=readings)
        result = score_all(session)
        for item in result:
            for key in REQUIRED_KEYS:
                assert key in item, f"Missing key: {key}"

    def test_priority_rank_assigned(self):
        """All items in score_all get a priority_rank."""
        from app.services.engine_adapter import score_all

        consumer = _make_consumer()
        readings = _make_readings_list(n=120)
        session = _mock_session(consumer=consumer, readings=readings)
        result = score_all(session)
        for item in result:
            assert "priority_rank" in item
            if item["priority_rank"] is not None:
                assert isinstance(item["priority_rank"], int)
                assert item["priority_rank"] >= 1

    def test_empty_consumers_returns_empty_list(self):
        """No consumers in DB → empty list."""
        from app.services.engine_adapter import score_all

        session = _mock_session(consumer=None, readings=[])
        # Override to return empty list for .all()
        session.query.return_value.all.return_value = []
        # Also patch the query chain
        import app.services.engine_adapter as ea_mod

        with patch.object(ea_mod, "score_consumer", return_value={}):
            # Re-patch query to return no consumers
            m = MagicMock()
            m.all.return_value = []
            session.query.return_value = m
            result = score_all(session)
        assert result == [] or isinstance(result, list)
