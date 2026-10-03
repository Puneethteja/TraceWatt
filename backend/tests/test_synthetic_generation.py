"""
backend/tests/test_synthetic_generation.py
==========================================
Phase-3 unit tests for backend/scripts/generate_synthetic.py.

All fixtures are defined INLINE — no conftest.py is needed or used.
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

# Ensure scripts and backend are importable
sys.path.insert(0, str(Path(__file__).parent.parent))  # backend/
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))  # backend/scripts/

from generate_synthetic import generate_synthetic_data, _sha256

# ---------------------------------------------------------------------------
# Fixture data generator (~50 base consumers x 365 days)
# ---------------------------------------------------------------------------

_N_CONSUMERS = 50
_N_DAYS = 365
_DATES = [
    (pd.Timestamp("2015-01-01") + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
    for i in range(_N_DAYS)
]


def _build_synthetic_fixture(tmp_dir: Path) -> tuple[Path, Path]:
    """Generates small in-memory clean inputs: consumers.csv and readings.parquet."""
    consumers = []
    readings = []

    for i in range(_N_CONSUMERS):
        cid = f"A_{i:04d}"
        consumers.append({
            "consumer_id": cid,
            "cons_no_original": f"{i:04d}",
            "source_dataset": "A",
            "theft_label": 0,
            "label_source": "FLAG",
        })

        # Base steady readings around 10.0 kWh/day
        rng = np.random.default_rng(i + 1000)
        base_vals = rng.uniform(9.0, 11.0, size=_N_DAYS)

        for dt, val in zip(_DATES, base_vals):
            readings.append({
                "consumer_id": cid,
                "ts": dt,
                "kwh": float(val),
            })

    consumers_df = pd.DataFrame(consumers)
    readings_df = pd.DataFrame(readings)

    c_path = tmp_dir / "consumers.csv"
    r_path = tmp_dir / "readings.parquet"

    consumers_df.to_csv(c_path, index=False)
    tbl = pa.Table.from_pandas(readings_df, preserve_index=False)
    pq.write_table(tbl, r_path)

    return c_path, r_path


@pytest.fixture(scope="module")
def synthetic_output(tmp_path_factory):
    base = tmp_path_factory.mktemp("syn_test")
    c_path, r_path = _build_synthetic_fixture(base)
    out_dir = base / "processed"

    # Run with 1 per scenario + 1 seasonal transformer = 5 transformers = 50 consumers
    res = generate_synthetic_data(
        consumers_path=str(c_path),
        readings_path=str(r_path),
        out_dir=str(out_dir),
        seed=42,
        n_per_scenario=1,
        seasonal_transformers=1,
    )

    return {
        "out_dir": out_dir,
        "c_path": c_path,
        "r_path": r_path,
        "labels_df": res["labels_df"],
        "synthetic_readings": res["synthetic_readings"],
        "consumers_synthetic": pd.read_csv(out_dir / "consumers_synthetic.csv"),
        "transformers": pd.read_csv(out_dir / "transformers.csv"),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTopologyConstraints:
    """Test 1: Topology constraints are met (>= 6 same-category NORMAL peers)."""

    def test_mixed_transformer_peer_category_constraint(self, synthetic_output):
        cons_df = synthetic_output["consumers_synthetic"]
        labels_df = synthetic_output["labels_df"]

        # Active consumers in transformers
        active_cons = cons_df[cons_df["transformer_id"] != ""].copy()
        merged = active_cons.merge(labels_df[["consumer_id", "true_cause"]], on="consumer_id")

        tx_groups = merged.groupby("transformer_id")
        for tx_id, group in tx_groups:
            assert len(group) == 10, f"Transformer {tx_id} must have exactly 10 consumers"

            targets = group[group["true_cause"] != "Normal"]
            if len(targets) == 1:  # Mixed transformer
                target_cat = targets["category"].iloc[0]
                normal_peers = group[group["true_cause"] == "Normal"]
                assert len(normal_peers) == 9

                same_cat_count = (normal_peers["category"] == target_cat).sum()
                assert same_cat_count >= 6, (
                    f"Transformer {tx_id} target category {target_cat} has only {same_cat_count} "
                    f"same-category peers (required >= 6)"
                )


class TestTheftScenario:
    """Test 2: THEFT: post-start mean / pre-start mean <= 0.55; persists >= 90 days; no recovery."""

    def test_theft_properties(self, synthetic_output):
        labels_df = synthetic_output["labels_df"]
        readings = synthetic_output["synthetic_readings"]

        theft_cids = labels_df[labels_df["true_cause"] == "Theft/Tampering"]["consumer_id"].tolist()
        assert len(theft_cids) >= 1

        for cid in theft_cids:
            c_readings = readings[readings["consumer_id"] == cid].sort_values("ts")
            label_row = labels_df[labels_df["consumer_id"] == cid].iloc[0]
            start_ts = label_row["period_start"]

            pre_readings = c_readings[c_readings["ts"] < start_ts]["generated_kwh"]
            post_readings = c_readings[c_readings["ts"] >= start_ts]["generated_kwh"]

            pre_mean = pre_readings.mean()
            post_mean = post_readings.mean()

            # 1. Post-start mean / pre-start mean <= 0.55
            assert (post_mean / pre_mean) <= 0.55, (
                f"Theft ratio {post_mean / pre_mean:.3f} must be <= 0.55"
            )

            # 2. Persists >= 90 days
            assert len(post_readings) >= 90, (
                f"Theft duration {len(post_readings)} must be >= 90 days"
            )

            # 3. No recovery: check each 30-day block after start remains dropped
            for b_start in range(0, len(post_readings), 30):
                block = post_readings.iloc[b_start : b_start + 30]
                if len(block) >= 10:
                    assert block.mean() < 0.65 * pre_mean, "Theft recovered unexpectedly"


class TestMeterScenario:
    """Test 3: METER: FAULT status only inside window; flatline zero variance, zero variant all 0.0."""

    def test_meter_fault_status_and_variants(self, synthetic_output):
        labels_df = synthetic_output["labels_df"]
        readings = synthetic_output["synthetic_readings"]

        meter_cids = labels_df[labels_df["true_cause"] == "Meter Malfunction"]["consumer_id"].tolist()
        assert len(meter_cids) >= 1

        for cid in meter_cids:
            c_readings = readings[readings["consumer_id"] == cid].sort_values("ts")
            label_row = labels_df[labels_df["consumer_id"] == cid].iloc[0]
            s_ts = label_row["period_start"]
            e_ts = label_row["period_end"]

            in_event = (c_readings["ts"] >= s_ts) & (c_readings["ts"] <= e_ts)
            event_readings = c_readings[in_event]
            outside_readings = c_readings[~in_event]

            # 1. FAULT status only inside the window
            assert (event_readings["meter_status"] == "FAULT").all()
            assert (outside_readings["meter_status"] == "OK").all()

            # 2. Check variant characteristics
            vals = event_readings["generated_kwh"].to_numpy()
            if np.isclose(vals, 0.0).all():
                # Zero variant verified
                assert (vals == 0.0).all()
            elif np.isclose(np.std(vals), 0.0):
                # Flatline variant verified
                assert np.isclose(np.std(vals), 0.0, atol=1e-12)



class TestCommunicationScenario:
    """Test 4: COMM: FAILED rows have NaN generated_kwh and non-NaN original_kwh."""

    def test_comm_failure_rows(self, synthetic_output):
        readings = synthetic_output["synthetic_readings"]
        comm_failed = readings[readings["comm_status"] == "FAILED"]
        assert len(comm_failed) > 0, "No COMM failure rows found"

        # generated_kwh is NaN
        assert comm_failed["generated_kwh"].isna().all(), "All FAILED rows must have NaN generated_kwh"
        # original_kwh is NOT NaN
        assert comm_failed["original_kwh"].notna().all(), "All FAILED rows must retain original_kwh"


class TestSeasonalScenario:
    """Test 5: SEASONAL: every member's window ratio >= 1.2 vs its own baseline."""

    def test_seasonal_window_ratio(self, synthetic_output):
        labels_df = synthetic_output["labels_df"]
        readings = synthetic_output["synthetic_readings"]

        seasonal_cids = labels_df[labels_df["true_cause"] == "Seasonal Variation"]["consumer_id"].tolist()
        assert len(seasonal_cids) == 10  # 1 full seasonal transformer

        for cid in seasonal_cids:
            c_readings = readings[readings["consumer_id"] == cid].sort_values("ts")
            label_row = labels_df[labels_df["consumer_id"] == cid].iloc[0]
            s_ts = label_row["period_start"]
            e_ts = label_row["period_end"]

            in_window = (c_readings["ts"] >= s_ts) & (c_readings["ts"] <= e_ts)
            w_mean = c_readings[in_window]["generated_kwh"].mean()
            base_mean = c_readings[~in_window]["generated_kwh"].mean()

            ratio = w_mean / base_mean
            assert ratio >= 1.20, f"Consumer {cid} seasonal ratio {ratio:.3f} must be >= 1.20"


class TestReproducibility:
    """Test 6: Two runs with the same seed produce byte-identical outputs."""

    def test_byte_identical_rerun(self, synthetic_output, tmp_path_factory):
        base2 = tmp_path_factory.mktemp("syn_test_2")
        out_dir2 = base2 / "processed"

        generate_synthetic_data(
            consumers_path=str(synthetic_output["c_path"]),
            readings_path=str(synthetic_output["r_path"]),
            out_dir=str(out_dir2),
            seed=42,
            n_per_scenario=1,
            seasonal_transformers=1,
        )

        out_dir1 = synthetic_output["out_dir"]
        for fname in (
            "consumers_synthetic.csv",
            "transformers.csv",
            "labels.csv",
            "synthetic_readings.parquet",
            "synthetic_validation_report.md",
        ):
            h1 = _sha256(out_dir1 / fname)
            h2 = _sha256(out_dir2 / fname)
            assert h1 == h2, f"{fname} is not byte-identical across runs:\n  run1={h1}\n  run2={h2}"
