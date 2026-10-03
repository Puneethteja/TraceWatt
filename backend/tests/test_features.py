"""
backend/tests/test_features.py
==============================
Phase-2 unit tests for backend/datapipe/features.py.

All fixtures are defined INLINE — no conftest.py is needed or used.

Fixture layout (~10 consumers x 100 days: 2015-01-01 to 2015-04-10):
  - A_NORM1, A_NORM2, A_NORM3 : Normal baseline usage (10.0 kWh/day).
  - A_DROP     : Sudden 60% drop (4.0 kWh/day) lasting exactly 40 days (days 30..69).
  - A_NAN      : 15 consecutive NaN values (days 10..24), remaining days 10.0 kWh/day.
  - A_ZERO     : 15 consecutive 0.0 values (days 10..24), remaining days 10.0 kWh/day.
  - B_NORM1, B_NORM2, B_NORM3 : Normal baseline usage (8.0 kWh/day).
  - B_SEASONAL : Normal 8.0 kWh/day for days 0..69, then 30% increase (10.4 kWh/day) in target month.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

# Make sure datapipe package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))  # backend/
from datapipe.features import (
    build_features,
    compute_rolling_series,
    FEATURE_COLUMNS,
    BASELINES_COLUMNS,
)

# ---------------------------------------------------------------------------
# Fixture data generator
# ---------------------------------------------------------------------------

_N_DAYS = 100
_DATES = [
    (pd.Timestamp("2015-01-01") + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
    for i in range(_N_DAYS)
]


def _build_fixture_dfs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generates synthetic in-memory readings and consumers DataFrames."""
    consumers_meta = [
        ("A_NORM1", "A", 0),
        ("A_NORM2", "A", 0),
        ("A_NORM3", "A", 0),
        ("A_DROP", "A", 1),
        ("A_NAN", "A", 0),
        ("A_ZERO", "A", 1),
        ("B_NORM1", "B", 0),
        ("B_NORM2", "B", 0),
        ("B_NORM3", "B", 0),
        ("B_SEASONAL", "B", 0),
    ]

    consumers_df = pd.DataFrame(
        consumers_meta,
        columns=["consumer_id", "source_dataset", "theft_label"],
    )

    rows = []
    for cid, src, _ in consumers_meta:
        if cid == "A_DROP":
            # 30 days normal (10.0), 40 days drop by 60% (4.0), 30 days normal (10.0)
            kwh = [10.0] * 30 + [4.0] * 40 + [10.0] * 30
        elif cid == "A_NAN":
            # 15 consecutive NaNs (days 10..24), others 10.0
            kwh = [10.0] * 10 + [np.nan] * 15 + [10.0] * 75
        elif cid == "A_ZERO":
            # 15 consecutive 0.0 values (days 10..24), others 10.0
            kwh = [10.0] * 10 + [0.0] * 15 + [10.0] * 75
        elif cid == "B_SEASONAL":
            # Days 0..69 normal (8.0), Days 70..99 (last 30 days / target month) 30% increase (10.4)
            kwh = [8.0] * 70 + [10.4] * 30
        elif src == "A":
            kwh = [10.0] * _N_DAYS
        else:
            kwh = [8.0] * _N_DAYS

        for dt, val in zip(_DATES, kwh):
            rows.append({"consumer_id": cid, "ts": dt, "kwh": val})

    readings_df = pd.DataFrame(rows)
    return readings_df, consumers_df


# ---------------------------------------------------------------------------
# Module Fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def processed_outputs(tmp_path_factory):
    base = tmp_path_factory.mktemp("feat_test")
    readings_path = base / "readings.parquet"
    consumers_path = base / "consumers.csv"
    out_dir = base / "processed"

    readings_df, consumers_df = _build_fixture_dfs()

    table = pa.Table.from_pandas(readings_df, preserve_index=False)
    pq.write_table(table, readings_path)
    consumers_df.to_csv(consumers_path, index=False)

    features_df = build_features(str(readings_path), str(consumers_path), str(out_dir))
    baselines_df = pd.read_csv(out_dir / "baselines.csv")

    return {
        "features_df": features_df,
        "baselines_df": baselines_df,
        "out_dir": out_dir,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFeatureSchema:
    """Test 1: build_features returns DataFrame with exact expected columns in order."""

    def test_features_columns_exact(self, processed_outputs):
        features_df = processed_outputs["features_df"]
        assert list(features_df.columns) == FEATURE_COLUMNS, (
            f"Columns mismatch:\nGot: {list(features_df.columns)}\nExpected: {FEATURE_COLUMNS}"
        )

    def test_consumer_count(self, processed_outputs):
        features_df = processed_outputs["features_df"]
        assert len(features_df) == 10


class TestMissingRatio:
    """Test 2: missing_ratio for A_NAN > 0.1, and zero_reading_ratio == 0.0."""

    def test_a_nan_metrics(self, processed_outputs):
        features_df = processed_outputs["features_df"]
        row = features_df[features_df["consumer_id"] == "A_NAN"].iloc[0]
        assert row["missing_ratio"] > 0.1, f"Expected missing_ratio > 0.1, got {row['missing_ratio']}"
        assert row["zero_reading_ratio"] == 0.0, f"Expected zero_reading_ratio == 0.0, got {row['zero_reading_ratio']}"


class TestZeroReadingRatio:
    """Test 3: zero_reading_ratio for A_ZERO > 0.1, and missing_ratio == 0.0."""

    def test_a_zero_metrics(self, processed_outputs):
        features_df = processed_outputs["features_df"]
        row = features_df[features_df["consumer_id"] == "A_ZERO"].iloc[0]
        assert row["zero_reading_ratio"] > 0.1, f"Expected zero_reading_ratio > 0.1, got {row['zero_reading_ratio']}"
        assert row["missing_ratio"] == 0.0, f"Expected missing_ratio == 0.0, got {row['missing_ratio']}"


class TestDropLength:
    """Test 4: drop_length for A_DROP is >= 40."""

    def test_a_drop_length(self, processed_outputs):
        features_df = processed_outputs["features_df"]
        row = features_df[features_df["consumer_id"] == "A_DROP"].iloc[0]
        assert row["drop_length"] >= 40, f"Expected drop_length >= 40, got {row['drop_length']}"


class TestSeasonalResidual:
    """Test 5: seasonal_residual for B_SEASONAL during target month is significantly positive."""

    def test_b_seasonal_residual(self, processed_outputs):
        features_df = processed_outputs["features_df"]
        row = features_df[features_df["consumer_id"] == "B_SEASONAL"].iloc[0]
        # Target month has 10.4 kWh vs overall mean ~8.72 kWh -> residual > +1.0
        assert row["seasonal_residual"] > 0.5, (
            f"Expected positive seasonal_residual > 0.5, got {row['seasonal_residual']}"
        )


class TestPeerDeviation:
    """Test 6: peer_deviation correctly calculates difference from dataset median."""

    def test_peer_deviation_calculation(self, processed_outputs):
        features_df = processed_outputs["features_df"]
        norm1 = features_df[features_df["consumer_id"] == "A_NORM1"].iloc[0]
        # Normal consumers have mean 10.0, which matches dataset A median
        assert abs(norm1["peer_deviation"]) < 0.1

        # A_DROP had a 40-day drop, so its overall mean is lower than dataset median
        drop_row = features_df[features_df["consumer_id"] == "A_DROP"].iloc[0]
        assert drop_row["peer_deviation"] < 0.0


class TestNoFutureLeakage:
    """Test 7: rolling_mean_30d at day T does not include data from day T+1."""

    def test_no_leakage_on_t_plus_one(self):
        # Create a series of 50 days of 10.0
        s_orig = pd.Series([10.0] * 50)
        roll_orig = compute_rolling_series(s_orig, window=30)

        # Alter day 30 to a spike of 1000.0
        s_altered = s_orig.copy()
        s_altered.iloc[30] = 1000.0
        roll_altered = compute_rolling_series(s_altered, window=30)

        # Values at day T=29 (and prior) must be identical
        assert roll_orig.iloc[29] == roll_altered.iloc[29]
        # Day 30 reflects the alteration
        assert roll_altered.iloc[30] > roll_orig.iloc[30]


class TestBaselinesSchema:
    """Test 8: baselines.csv is written with the exact 6 columns specified."""

    def test_baselines_columns(self, processed_outputs):
        baselines_df = processed_outputs["baselines_df"]
        assert list(baselines_df.columns) == BASELINES_COLUMNS, (
            f"Baselines columns mismatch:\nGot: {list(baselines_df.columns)}\nExpected: {BASELINES_COLUMNS}"
        )

    def test_baselines_values_valid(self, processed_outputs):
        baselines_df = processed_outputs["baselines_df"]
        assert not baselines_df["peer_median"].isna().all()
        assert not baselines_df["peer_p25"].isna().all()
        assert not baselines_df["peer_p75"].isna().all()


class TestDeterminism:
    """Test 9: Two runs with same inputs produce byte-identical output files."""

    def test_byte_identical_rerun(self, processed_outputs, tmp_path_factory):
        base2 = tmp_path_factory.mktemp("feat_test_2")
        readings_path = base2 / "readings.parquet"
        consumers_path = base2 / "consumers.csv"
        out_dir2 = base2 / "processed"

        readings_df, consumers_df = _build_fixture_dfs()
        table = pa.Table.from_pandas(readings_df, preserve_index=False)
        pq.write_table(table, readings_path)
        consumers_df.to_csv(consumers_path, index=False)

        build_features(str(readings_path), str(consumers_path), str(out_dir2))

        out_dir1 = processed_outputs["out_dir"]
        for fname in ("baselines.csv", "features.parquet"):
            h1 = hashlib.sha256((out_dir1 / fname).read_bytes()).hexdigest()
            h2 = hashlib.sha256((out_dir2 / fname).read_bytes()).hexdigest()
            assert h1 == h2, f"{fname} is not byte-identical across runs:\n  run1={h1}\n  run2={h2}"

