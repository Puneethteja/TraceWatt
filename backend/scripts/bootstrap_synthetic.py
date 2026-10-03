"""
backend/scripts/bootstrap_synthetic.py
========================================
TraceWatt — Bootstrap synthetic training data from scratch.

Generates all processed data needed for training WITHOUT requiring raw CSV files.
Creates synthetic consumers and readings that mimic the 6 scenario patterns,
then saves features.parquet, labels.csv, synthetic_readings.parquet, and
consumers_synthetic.csv in data/processed/.

Usage:
    cd TraceWatt
    python backend/scripts/bootstrap_synthetic.py
    python backend/scripts/bootstrap_synthetic.py --n-consumers 2000 --out-dir data/processed
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Scenario codes (matching generate_synthetic.py)
SCENARIO_CODES = ["THEFT", "METER", "COMM", "LEGIT", "SEASONAL", "NORMAL"]
TRUE_CAUSES = {
    "THEFT": "Theft/Tampering",
    "METER": "Meter Malfunction",
    "COMM": "Communication Failure",
    "LEGIT": "Legitimate Abnormal",
    "SEASONAL": "Seasonal Variation",
    "NORMAL": "Normal",
}

CATEGORIES = ["residential", "commercial", "industrial"]
TARIFFS = {"residential": 5.0, "commercial": 8.0, "industrial": 12.0}
BASE_LOADS = {"residential": 60.0, "commercial": 300.0, "industrial": 2000.0}


def generate_consumer_readings(
    cid: str,
    scenario: str,
    n_days: int,
    base_kwh: float,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, dict]:
    """Generate synthetic readings for a single consumer with a given scenario."""
    kwh = base_kwh + rng.normal(0, base_kwh * 0.05, n_days)
    kwh = np.clip(kwh, 0.01, None)
    meter_status = np.full(n_days, "OK", dtype=object)
    comm_status = np.full(n_days, "OK", dtype=object)
    in_window = np.zeros(n_days, dtype=bool)
    theft_flag = 0
    true_cause = TRUE_CAUSES[scenario]
    period_start = period_end = ""

    # Place events in the LAST 90 days so analyze()'s 100-day trailing window captures them
    _event_zone_start = max(20, n_days - 90)

    if scenario == "THEFT":
        theft_flag = 1
        start = int(rng.integers(_event_zone_start, max(_event_zone_start + 1, n_days - 60)))
        factor = float(rng.uniform(0.10, 0.35))
        for i in range(start, n_days):
            kwh[i] *= factor
            in_window[i] = True
        period_start = str(start)
        period_end = str(n_days - 1)

    elif scenario == "METER":
        start = int(rng.integers(_event_zone_start, max(_event_zone_start + 1, n_days - 25)))
        dur = int(rng.integers(20, min(50, n_days - start)))
        end = min(start + dur, n_days)
        variant = int(rng.integers(0, 3))
        meter_status[start:end] = "FAULT"
        if variant == 0:
            kwh[start:end] = 0.0
        elif variant == 1:
            valid = kwh[:start]
            last = float(valid[-1]) if len(valid) > 0 else base_kwh
            kwh[start:end] = last
        else:
            kwh[start:end] = np.clip(rng.lognormal(2.0, 2.5, end - start), 0.0, base_kwh * 20)
        in_window[start:end] = True
        period_start = str(start)
        period_end = str(end - 1)

    elif scenario == "COMM":
        start = int(rng.integers(_event_zone_start, max(_event_zone_start + 1, n_days - 15)))
        dur = int(rng.integers(10, min(20, n_days - start)))
        end = min(start + dur, n_days)
        kwh[start:end] = np.nan
        comm_status[start:end] = "FAILED"
        in_window[start:end] = True
        period_start = str(start)
        period_end = str(end - 1)

    elif scenario == "LEGIT":
        start = int(rng.integers(_event_zone_start, max(_event_zone_start + 1, n_days - 25)))
        if rng.uniform() < 0.5:
            # temporary reduction
            dur = int(rng.integers(14, 30))
            end = min(start + dur, n_days)
            kwh[start:end] *= rng.uniform(0.10, 0.35)
            in_window[start:end] = True
            period_end = str(end - 1)
        else:
            # step increase
            kwh[start:] *= rng.uniform(1.3, 1.8)
            in_window[start:] = True
            period_end = str(n_days - 1)
        period_start = str(start)

    elif scenario == "SEASONAL":
        s = int(rng.integers(_event_zone_start, max(_event_zone_start + 1, n_days - 60)))
        dur = int(rng.integers(40, min(80, n_days - s)))
        e = min(s + dur, n_days - 1)
        t = np.arange(s, e + 1)
        bump = 1.0 + 0.45 * np.sin(np.pi * (t - s) / max(dur, 1)) ** 2
        for i, idx in enumerate(range(s, e + 1)):
            kwh[idx] = max(kwh[idx] * bump[i], 0.01)
        in_window[s:e + 1] = True
        period_start = str(s)
        period_end = str(e)

    # NORMAL: no modification

    dates = pd.date_range("2020-01-01", periods=n_days, freq="D")
    df = pd.DataFrame({
        "consumer_id": cid,
        "ts": dates.strftime("%Y-%m-%d"),
        "kwh": kwh,
        "meter_status": meter_status,
        "comm_status": comm_status,
        "scenario_id": scenario,
        "in_event_window": in_window,
    })

    label = {
        "consumer_id": cid,
        "label_source": "BOOTSTRAP",
        "theft_label": theft_flag,
        "true_cause": true_cause,
        "period_start": period_start,
        "period_end": period_end,
    }
    return df, label


def compute_features_for_consumer(readings: pd.DataFrame, theft_label: int, source: str) -> dict:
    """Compute the 8 feature columns for a single consumer."""
    kwh = readings["kwh"].to_numpy(dtype=np.float64)
    n = len(kwh)
    nans = np.isnan(kwh)
    zeros = (kwh == 0.0) & ~nans

    missing_ratio = float(nans.sum() / n) if n > 0 else 0.0
    zero_ratio = float(zeros.sum() / n) if n > 0 else 0.0

    valid = kwh[~nans]
    overall_mean = float(np.mean(valid)) if len(valid) > 0 else 0.0

    last_30 = kwh[-30:] if n >= 30 else kwh
    last_30_valid = last_30[~np.isnan(last_30)]
    rolling_mean_30d = float(np.mean(last_30_valid)) if len(last_30_valid) > 0 else 0.0
    rolling_std_30d = float(np.std(last_30_valid)) if len(last_30_valid) > 1 else 0.0

    mom_change_pct = 0.0
    if n >= 60:
        prior_30 = kwh[-60:-30]
        prior_valid = prior_30[~np.isnan(prior_30)]
        m_last = np.mean(last_30_valid) if len(last_30_valid) > 0 else np.nan
        m_prior = np.mean(prior_valid) if len(prior_valid) > 0 else np.nan
        if not (np.isnan(m_prior) or m_prior == 0.0 or np.isnan(m_last)):
            mom_change_pct = float(((m_last - m_prior) / m_prior) * 100.0)

    s = pd.Series(kwh)
    rm = s.rolling(30, min_periods=1).mean()
    baseline = np.maximum(rm.values, rm.expanding().max().values)
    is_drop = (s.values < 0.5 * baseline)
    max_c = curr = 0
    for v in is_drop:
        if v:
            curr += 1
            max_c = max(max_c, curr)
        else:
            curr = 0

    seasonal_residual = float(rolling_mean_30d - overall_mean) if overall_mean != 0 else 0.0

    return {
        "consumer_id": readings["consumer_id"].iloc[0],
        "source_dataset": source,
        "theft_label": theft_label,
        "total_readings": n,
        "missing_ratio": missing_ratio,
        "zero_reading_ratio": zero_ratio,
        "rolling_mean_30d": rolling_mean_30d,
        "rolling_std_30d": rolling_std_30d,
        "mom_change_pct": mom_change_pct,
        "drop_length": int(max_c),
        "peer_deviation": 0.0,  # filled later
        "seasonal_residual": seasonal_residual,
        "_overall_mean": overall_mean,
    }


def bootstrap(
    n_consumers: int,
    out_dir: str,
    seed: int,
    n_days: int,
    n_per_scenario: int,
) -> None:
    rng = np.random.default_rng(seed)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"[Bootstrap] Generating {n_consumers} consumers × {n_days} days each...")

    all_readings = []
    all_labels = []
    all_features = []
    consumers_meta = []

    # Assign scenarios: balanced, repeat if needed
    scenarios = []
    n_per_each = max(n_per_scenario, n_consumers // len(SCENARIO_CODES))
    for sc in SCENARIO_CODES:
        scenarios.extend([sc] * n_per_each)
    # top up with NORMAL
    while len(scenarios) < n_consumers:
        scenarios.append("NORMAL")
    # trim
    scenarios = scenarios[:n_consumers]
    rng.shuffle(scenarios)

    for i, scenario in enumerate(scenarios):
        cat = CATEGORIES[i % 3]
        cid = f"SYN_{i:05d}_{scenario}"
        base_kwh = BASE_LOADS[cat] * float(rng.uniform(0.8, 1.2))
        tariff = TARIFFS[cat]
        theft_label = 1 if scenario == "THEFT" else 0

        c_rng = np.random.default_rng([seed, i])
        readings_df, label = generate_consumer_readings(cid, scenario, n_days, base_kwh, c_rng)

        feat_row = compute_features_for_consumer(readings_df, theft_label, "SYNTH")

        all_readings.append(readings_df)
        all_labels.append(label)
        all_features.append(feat_row)
        consumers_meta.append({
            "consumer_id": cid,
            "category": cat,
            "tariff": tariff,
            "sanctioned_load_kw": base_kwh / 24.0,
            "feeder_id": f"FDR_{i // 40 + 1:02d}",
            "transformer_id": f"TX_{i // 10 + 1:03d}",
            "theft_label": theft_label,
        })

    readings_full = pd.concat(all_readings, ignore_index=True)
    labels_df = pd.DataFrame(all_labels)
    features_df = pd.DataFrame(all_features)
    consumers_df = pd.DataFrame(consumers_meta)

    # Compute peer_deviation per source_dataset
    dataset_medians = features_df.groupby("source_dataset")["_overall_mean"].transform("median")
    features_df["peer_deviation"] = features_df["_overall_mean"] - dataset_medians
    features_df = features_df.drop(columns=["_overall_mean"])

    # Write features.parquet
    feat_schema = pa.schema([
        pa.field("consumer_id", pa.string()),
        pa.field("source_dataset", pa.string()),
        pa.field("theft_label", pa.int64()),
        pa.field("total_readings", pa.int64()),
        pa.field("missing_ratio", pa.float64()),
        pa.field("zero_reading_ratio", pa.float64()),
        pa.field("rolling_mean_30d", pa.float64()),
        pa.field("rolling_std_30d", pa.float64()),
        pa.field("mom_change_pct", pa.float64()),
        pa.field("drop_length", pa.int64()),
        pa.field("peer_deviation", pa.float64()),
        pa.field("seasonal_residual", pa.float64()),
    ])
    tbl = pa.Table.from_pandas(features_df, schema=feat_schema, preserve_index=False)
    pq.write_table(tbl, out_path / "features.parquet", compression="snappy", write_statistics=False)

    # Write synthetic_readings.parquet
    readings_schema = pa.schema([
        pa.field("consumer_id", pa.string()),
        pa.field("ts", pa.string()),
        pa.field("kwh", pa.float64()),
        pa.field("meter_status", pa.string()),
        pa.field("comm_status", pa.string()),
        pa.field("scenario_id", pa.string()),
        pa.field("in_event_window", pa.bool_()),
    ])
    tbl2 = pa.Table.from_pandas(readings_full, schema=readings_schema, preserve_index=False)
    pq.write_table(tbl2, out_path / "synthetic_readings.parquet", compression="snappy", write_statistics=False)

    # Write labels.csv and consumers_synthetic.csv
    labels_df.to_csv(out_path / "labels.csv", index=False)
    consumers_df.to_csv(out_path / "consumers_synthetic.csv", index=False)

    # Also write a minimal consumers.csv for compatibility
    cons_csv = consumers_df[["consumer_id"]].copy()
    cons_csv["cons_no_original"] = cons_csv["consumer_id"]
    cons_csv["source_dataset"] = "SYNTH"
    cons_csv["theft_label"] = consumers_df["theft_label"]
    cons_csv["label_source"] = "BOOTSTRAP"
    cons_csv.to_csv(out_path / "consumers.csv", index=False)

    print(f"[Bootstrap] Written {len(consumers_df):,} consumers")
    print(f"[Bootstrap] Written {len(readings_full):,} reading rows")
    print(f"[Bootstrap] Scenario distribution:")
    print(labels_df["true_cause"].value_counts().to_string())
    print(f"[Bootstrap] Output: {out_path.resolve()}")
    print(f"  - features.parquet")
    print(f"  - synthetic_readings.parquet")
    print(f"  - labels.csv")
    print(f"  - consumers_synthetic.csv")
    print(f"  - consumers.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap synthetic TraceWatt training data")
    parser.add_argument("--n-consumers", type=int, default=2400, help="Total synthetic consumers")
    parser.add_argument("--n-days", type=int, default=365, help="Days of readings per consumer")
    parser.add_argument("--n-per-scenario", type=int, default=400, help="Consumers per scenario")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--out-dir", type=str, default="data/processed")
    args = parser.parse_args()

    bootstrap(
        n_consumers=args.n_consumers,
        out_dir=args.out_dir,
        seed=args.seed,
        n_days=args.n_days,
        n_per_scenario=args.n_per_scenario,
    )
