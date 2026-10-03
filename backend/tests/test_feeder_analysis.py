"""
backend/tests/test_feeder_analysis.py
=====================================
Phase-4 unit tests for backend/services/feeder_analysis.py.

All fixtures are defined INLINE — no conftest.py is needed or used.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Ensure backend directory is in path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.models import Base, Consumer, FeederSummary, Reading, TransformerReading
from services.feeder_analysis import (
    compute_feeder_balance,
    run_feeder_analysis,
    FEEDER_SUMMARY_COLUMNS,
)


@pytest.fixture
def sqlite_session():
    """Provides an isolated in-memory SQLite session with initialized schema."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def seeded_session(sqlite_session):
    """
    Seeds database with mock data per PRD / test requirements:
      - TX_01: 2 consumers (C_1, C_2). Input = 100 kWh, sum = 80 kWh.
      - TX_02: 1 consumer (C_3). Input = 50 kWh, sum = 48 kWh.
    """
    session = sqlite_session

    session.add_all([
        Consumer(consumer_id="C_1", transformer_id="TX_01"),
        Consumer(consumer_id="C_2", transformer_id="TX_01"),
        Consumer(consumer_id="C_3", transformer_id="TX_02"),
    ])

    session.add_all([
        TransformerReading(transformer_id="TX_01", ts="2024-01-15", energy_in_kwh=100.0),
        TransformerReading(transformer_id="TX_02", ts="2024-01-15", energy_in_kwh=50.0),
    ])

    session.add_all([
        Reading(consumer_id="C_1", ts="2024-01-15", kwh=40.0),
        Reading(consumer_id="C_2", ts="2024-01-15", kwh=40.0),
        Reading(consumer_id="C_3", ts="2024-01-15", kwh=48.0),
    ])

    session.commit()
    return session


class TestRunFeederAnalysis:
    """Tests the SQLAlchemy-based run_feeder_analysis pipeline."""

    def test_feeder_summary_rows_and_math(self, seeded_session):
        session = seeded_session
        window_start = "2024-01-01"
        window_end = "2024-01-31"

        run_feeder_analysis(session, window_start, window_end)

        stmt = select(FeederSummary).order_by(FeederSummary.transformer_id)
        rows = session.scalars(stmt).all()

        assert len(rows) == 2, f"Expected 2 rows in feeder_summary, got {len(rows)}"

        # TX_01: In = 100, Metered = 80 -> loss = 20%, flag = 1
        tx1 = rows[0]
        assert tx1.transformer_id == "TX_01"
        assert tx1.window_start == window_start
        assert tx1.window_end == window_end
        assert tx1.energy_in_kwh == pytest.approx(100.0)
        assert tx1.energy_metered_kwh == pytest.approx(80.0)
        assert tx1.unexplained_loss_pct == pytest.approx(20.0)
        assert tx1.cluster_flag == 1
        assert tx1.cluster_score == pytest.approx(0.20)

        # TX_02: In = 50, Metered = 48 -> loss = 4%, flag = 0
        tx2 = rows[1]
        assert tx2.transformer_id == "TX_02"
        assert tx2.window_start == window_start
        assert tx2.window_end == window_end
        assert tx2.energy_in_kwh == pytest.approx(50.0)
        assert tx2.energy_metered_kwh == pytest.approx(48.0)
        assert tx2.unexplained_loss_pct == pytest.approx(4.0)
        assert tx2.cluster_flag == 0
        assert tx2.cluster_score == pytest.approx(0.04)


class TestComputeFeederBalancePandas:
    """Tests the pure pandas compute_feeder_balance function directly."""

    def test_pandas_math_matches_sql(self):
        readings_df = pd.DataFrame([
            {"consumer_id": "C_1", "ts": "2024-01-15", "kwh": 40.0},
            {"consumer_id": "C_2", "ts": "2024-01-15", "kwh": 40.0},
            {"consumer_id": "C_3", "ts": "2024-01-15", "kwh": 48.0},
        ])
        tx_df = pd.DataFrame([
            {"transformer_id": "TX_01", "ts": "2024-01-15", "energy_in_kwh": 100.0},
            {"transformer_id": "TX_02", "ts": "2024-01-15", "energy_in_kwh": 50.0},
        ])
        cons_df = pd.DataFrame([
            {"consumer_id": "C_1", "transformer_id": "TX_01"},
            {"consumer_id": "C_2", "transformer_id": "TX_01"},
            {"consumer_id": "C_3", "transformer_id": "TX_02"},
        ])

        summary_df = compute_feeder_balance(
            readings_df=readings_df,
            transformer_readings_df=tx_df,
            consumers_df=cons_df,
            window_start="2024-01-01",
            window_end="2024-01-31",
        )

        assert list(summary_df.columns) == FEEDER_SUMMARY_COLUMNS
        assert len(summary_df) == 2

        tx1_row = summary_df[summary_df["transformer_id"] == "TX_01"].iloc[0]
        assert tx1_row["unexplained_loss_pct"] == pytest.approx(20.0)
        assert tx1_row["cluster_flag"] == 1

        tx2_row = summary_df[summary_df["transformer_id"] == "TX_02"].iloc[0]
        assert tx2_row["unexplained_loss_pct"] == pytest.approx(4.0)
        assert tx2_row["cluster_flag"] == 0

    def test_high_risk_consumers_influence_cluster_score(self):
        readings_df = pd.DataFrame([
            {"consumer_id": "C_1", "ts": "2024-01-15", "kwh": 40.0},
            {"consumer_id": "C_2", "ts": "2024-01-15", "kwh": 40.0},
        ])
        tx_df = pd.DataFrame([
            {"transformer_id": "TX_01", "ts": "2024-01-15", "energy_in_kwh": 100.0},
        ])
        cons_df = pd.DataFrame([
            {"consumer_id": "C_1", "transformer_id": "TX_01"},
            {"consumer_id": "C_2", "transformer_id": "TX_01"},
        ])

        # C_1 is flagged high-risk -> count = 1
        # cluster_score = (20.0 / 100) * (1 + 1) = 0.40
        summary_df = compute_feeder_balance(
            readings_df=readings_df,
            transformer_readings_df=tx_df,
            consumers_df=cons_df,
            window_start="2024-01-01",
            window_end="2024-01-31",
            high_risk_consumer_ids=["C_1"],
        )

        row = summary_df.iloc[0]
        assert row["cluster_score"] == pytest.approx(0.40)

    def test_division_by_zero_handling(self):
        readings_df = pd.DataFrame([
            {"consumer_id": "C_1", "ts": "2024-01-15", "kwh": 10.0},
        ])
        tx_df = pd.DataFrame([
            {"transformer_id": "TX_01", "ts": "2024-01-15", "energy_in_kwh": 0.0},
        ])
        cons_df = pd.DataFrame([
            {"consumer_id": "C_1", "transformer_id": "TX_01"},
        ])

        summary_df = compute_feeder_balance(
            readings_df=readings_df,
            transformer_readings_df=tx_df,
            consumers_df=cons_df,
            window_start="2024-01-01",
            window_end="2024-01-31",
        )

        row = summary_df.iloc[0]
        assert row["unexplained_loss_pct"] == 0.0
        assert row["cluster_flag"] == 0
