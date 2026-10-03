"""
backend/tests/test_clean.py
============================
Phase-1 unit tests for backend/datapipe/clean.py.

All fixtures are defined INLINE — no conftest.py needed or used.

Fixture layout
--------------
File A  (~10 consumers x 30 days):
  - Date columns in deliberately shuffled TEXT order (trap 1).
  - One consumer (C_NAN_FLAG) has NaN FLAG value (trap 4 / assumption A2).
  - Consumer AAA003 has planted NaN and 0.0 kwh values (hard constraint 3).

File B  (~10 consumers x 30 days):
  - One consumer (555000111.0) has NaN CHK_STATE (trap 6 / assumption A3).
  - All CONS_NO stored as floats e.g. 8546920085.0 (trap 5).
  - Consumer 777888999 has planted NaN and 0.0 kwh values.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))  # backend/
from datapipe.clean import clean_raw_data

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_parquet(path: Path) -> pd.DataFrame:
    return pq.read_table(path).to_pandas()


# ---------------------------------------------------------------------------
# Fixture data builders
# ---------------------------------------------------------------------------

# File A: 30 date columns deliberately shuffled in TEXT sort order
_A_DATES_SHUFFLED = [
    "2016/9/10", "2016/9/3",  "2016/9/28", "2016/9/1",  "2016/9/2",
    "2016/9/15", "2016/9/5",  "2016/9/20", "2016/9/7",  "2016/9/12",
    "2016/10/1", "2016/8/31", "2016/9/25", "2016/9/8",  "2016/9/18",
    "2016/9/22", "2016/9/4",  "2016/9/9",  "2016/9/6",  "2016/9/11",
    "2016/9/13", "2016/9/14", "2016/9/16", "2016/9/17", "2016/9/19",
    "2016/9/21", "2016/9/23", "2016/9/24", "2016/9/26", "2016/9/27",
]

_A_DATES_SORTED_ISO = sorted(
    pd.to_datetime(d, format="%Y/%m/%d").strftime("%Y-%m-%d")
    for d in _A_DATES_SHUFFLED
)

_B_DATES = [
    "01-01-15", "02-01-15", "03-01-15", "04-01-15", "05-01-15",
    "06-01-15", "07-01-15", "08-01-15", "09-01-15", "10-01-15",
    "11-01-15", "12-01-15", "13-01-15", "14-01-15", "15-01-15",
    "16-01-15", "17-01-15", "18-01-15", "19-01-15", "20-01-15",
    "21-01-15", "22-01-15", "23-01-15", "24-01-15", "25-01-15",
    "26-01-15", "27-01-15", "28-01-15", "29-01-15", "30-01-15",
]

_N_DAYS = 30


def _make_file_a() -> str:
    rng = np.random.default_rng(42)
    consumers = [
        ("AAA001", 0),
        ("AAA002", 1),
        ("AAA003", 0),
        ("AAA004", 1),
        ("AAA005", 0),
        ("AAA006", 1),
        ("AAA007", 0),
        ("AAA008", 1),
        ("C_NAN_FLAG", np.nan),   # NaN FLAG trap
        ("AAA010", 0),
    ]
    rows = []
    for cons_no, flag in consumers:
        kwh_vals = rng.uniform(0.5, 10, _N_DAYS).tolist()
        if cons_no == "AAA003":
            kwh_vals[0] = np.nan  # NaN preserved
            kwh_vals[1] = 0.0     # zero preserved
        row = {"CONS_NO": cons_no, "FLAG": flag}
        row.update(dict(zip(_A_DATES_SHUFFLED, kwh_vals)))
        rows.append(row)
    return pd.DataFrame(rows).to_csv(index=False)


def _make_file_b() -> str:
    rng = np.random.default_rng(99)
    consumers = [
        (8546920085.0, 1.0),
        (617718257.0,  0.0),
        (111222333.0,  1.0),
        (444555666.0,  0.0),
        (777888999.0,  1.0),     # NaN + 0.0 in kwh
        (123456789.0,  0.0),
        (987654321.0,  1.0),
        (555000111.0,  np.nan),  # NaN CHK_STATE trap
        (999000444.0,  0.0),
        (333111222.0,  1.0),
    ]
    rows = []
    for cons_no, chk in consumers:
        kwh_vals = rng.uniform(0.5, 10, _N_DAYS).tolist()
        if cons_no == 777888999.0:
            kwh_vals[0] = np.nan
            kwh_vals[1] = 0.0
        row = {"CONS_NO": cons_no, "CHK_STATE": chk}
        row.update(dict(zip(_B_DATES, kwh_vals)))
        rows.append(row)
    return pd.DataFrame(rows).to_csv(index=False)


# ---------------------------------------------------------------------------
# Module-scoped fixture: run clean_raw_data once, share across all tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def output_dir(tmp_path_factory):
    base   = tmp_path_factory.mktemp("cleaned")
    file_a = base / "data.csv"
    file_b = base / "Electricity_Theft_Data.csv"
    out    = base / "processed"

    file_a.write_text(_make_file_a(), encoding="utf-8")
    file_b.write_text(_make_file_b(), encoding="utf-8")
    clean_raw_data(str(file_a), str(file_b), str(out))
    return out


@pytest.fixture(scope="module")
def consumers(output_dir):
    return pd.read_csv(output_dir / "consumers.csv",
                       dtype={"consumer_id": str, "cons_no_original": str,
                              "source_dataset": str})


@pytest.fixture(scope="module")
def readings(output_dir):
    return _read_parquet(output_dir / "readings.parquet")


@pytest.fixture(scope="module")
def readings_demo(output_dir):
    return pd.read_csv(output_dir / "readings_demo.csv",
                       dtype={"consumer_id": str, "ts": str})


# ---------------------------------------------------------------------------
# Test 1: consumers.csv schema
# ---------------------------------------------------------------------------


class TestConsumersSchema:
    def test_exact_columns(self, consumers):
        expected = ["consumer_id", "cons_no_original", "source_dataset",
                    "theft_label", "label_source"]
        assert list(consumers.columns) == expected

    def test_row_count(self, consumers):
        assert len(consumers) == 20  # 10 A + 10 B


# ---------------------------------------------------------------------------
# Test 2: readings schema (parquet)
# ---------------------------------------------------------------------------


class TestReadingsSchema:
    def test_exact_columns(self, readings):
        expected = ["consumer_id", "ts", "kwh"]
        assert list(readings.columns) == expected

    def test_row_count(self, readings):
        assert len(readings) == 600  # 20 consumers x 30 days

    def test_demo_columns(self, readings_demo):
        expected = ["consumer_id", "ts", "kwh"]
        assert list(readings_demo.columns) == expected

    def test_demo_is_subset(self, readings, readings_demo):
        demo_ids = set(readings_demo["consumer_id"].unique())
        all_ids  = set(readings["consumer_id"].unique())
        assert demo_ids.issubset(all_ids)

    def test_demo_max_consumers(self, readings_demo):
        assert readings_demo["consumer_id"].nunique() <= 50


# ---------------------------------------------------------------------------
# Test 3: consumer_id prefix
# ---------------------------------------------------------------------------


class TestConsumerIDPrefix:
    def test_file_a_prefix(self, consumers):
        src_a = consumers[consumers["source_dataset"] == "A"]
        assert src_a["consumer_id"].str.startswith("A_").all()

    def test_file_b_prefix(self, consumers):
        src_b = consumers[consumers["source_dataset"] == "B"]
        assert src_b["consumer_id"].str.startswith("B_").all()

    def test_readings_prefixes(self, readings):
        prefixes = readings["consumer_id"].str[:2].unique().tolist()
        assert set(prefixes) == {"A_", "B_"}


# ---------------------------------------------------------------------------
# Test 4: File A date columns sorted chronologically
# ---------------------------------------------------------------------------


class TestFilADateSorting:
    def test_ts_chronological_order(self, readings):
        src_a     = readings[readings["consumer_id"].str.startswith("A_")]
        sample_id = src_a["consumer_id"].iloc[0]
        ts_vals   = src_a[src_a["consumer_id"] == sample_id]["ts"].tolist()
        assert ts_vals == sorted(ts_vals)

    def test_ts_matches_expected_sorted_dates(self, readings):
        src_a     = readings[readings["consumer_id"].str.startswith("A_")]
        sample_id = src_a["consumer_id"].iloc[0]
        ts_vals   = src_a[src_a["consumer_id"] == sample_id]["ts"].tolist()
        assert ts_vals == _A_DATES_SORTED_ISO


# ---------------------------------------------------------------------------
# Test 5: File B CONS_NO ".0" suffix stripped
# ---------------------------------------------------------------------------


class TestFileBConsNoStripping:
    def test_no_dot_zero_in_original(self, consumers):
        src_b = consumers[consumers["source_dataset"] == "B"]
        assert not src_b["cons_no_original"].str.endswith(".0").any()

    def test_no_dot_zero_in_consumer_id(self, consumers):
        src_b = consumers[consumers["source_dataset"] == "B"]
        assert not src_b["consumer_id"].str.endswith(".0").any()


# ---------------------------------------------------------------------------
# Test 6: NaN in FLAG / CHK_STATE handled gracefully
# ---------------------------------------------------------------------------


class TestNaNLabelHandling:
    def test_file_a_nan_flag_is_sentinel(self, consumers):
        row = consumers[consumers["cons_no_original"] == "C_NAN_FLAG"]
        assert len(row) == 1
        assert row.iloc[0]["theft_label"] == -1

    def test_file_b_nan_chkstate_is_sentinel(self, consumers):
        row = consumers[consumers["cons_no_original"] == "555000111"]
        assert len(row) == 1
        assert row.iloc[0]["theft_label"] == -1

    def test_no_nan_in_theft_label_column(self, consumers):
        assert consumers["theft_label"].isna().sum() == 0


# ---------------------------------------------------------------------------
# Test 7: NaN in kwh preserved
# ---------------------------------------------------------------------------


class TestKwhNaNPreserved:
    def test_file_a_nan_preserved(self, readings):
        src = readings[readings["consumer_id"] == "A_AAA003"]
        assert src["kwh"].isna().any()

    def test_file_b_nan_preserved(self, readings):
        src = readings[readings["consumer_id"] == "B_777888999"]
        assert src["kwh"].isna().any()


# ---------------------------------------------------------------------------
# Test 8: 0.0 in kwh preserved (not converted to NaN)
# ---------------------------------------------------------------------------


class TestKwhZeroPreserved:
    def test_file_a_zero_preserved(self, readings):
        src = readings[readings["consumer_id"] == "A_AAA003"]
        assert (src["kwh"] == 0.0).any()

    def test_file_b_zero_preserved(self, readings):
        src = readings[readings["consumer_id"] == "B_777888999"]
        assert (src["kwh"] == 0.0).any()

    def test_nan_and_zero_are_disjoint(self, readings):
        src = readings[readings["consumer_id"] == "A_AAA003"]
        assert not (src["kwh"].isna() & (src["kwh"] == 0.0)).any()


# ---------------------------------------------------------------------------
# Test 9: Output sorted by consumer_id then ts
# ---------------------------------------------------------------------------


class TestOutputSorting:
    def test_consumers_sorted(self, consumers):
        ids = consumers["consumer_id"].tolist()
        assert ids == sorted(ids)

    def test_readings_sorted(self, readings):
        pairs = list(zip(readings["consumer_id"], readings["ts"]))
        assert pairs == sorted(pairs)


# ---------------------------------------------------------------------------
# Test 10: Byte-identical output on two runs
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_byte_identical(self, output_dir, tmp_path_factory):
        base2  = tmp_path_factory.mktemp("cleaned2")
        file_a = base2 / "data.csv"
        file_b = base2 / "Electricity_Theft_Data.csv"
        out2   = base2 / "processed"

        file_a.write_text(_make_file_a(), encoding="utf-8")
        file_b.write_text(_make_file_b(), encoding="utf-8")
        clean_raw_data(str(file_a), str(file_b), str(out2))

        for fname in ("consumers.csv", "readings.parquet", "readings_demo.csv"):
            h1 = _sha256_file(output_dir / fname)
            h2 = _sha256_file(out2 / fname)
            assert h1 == h2, (
                f"{fname} is NOT byte-identical across two runs\n"
                f"  run1: {h1}\n  run2: {h2}"
            )
