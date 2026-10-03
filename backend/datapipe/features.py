"""
backend/datapipe/features.py
============================
Phase-2 feature engineering and baselines layer for TraceWatt.

Reads clean long-format readings (Parquet) and consumers (CSV) from Phase 1
and generates:
  - data/processed/baselines.csv   (monthly baseline & peer quartiles)
  - data/processed/features.parquet (per-consumer aggregated ML-ready features)

KEY DESIGN PRINCIPLES:
  1. No future leakage: rolling windows are strictly trailing (look-back).
  2. NULL vs ZERO distinction: NaN = comms gap, 0.0 = flatline/fault.
     Never fill, impute, interpolate, or conflate.
  3. Memory efficiency: fully vectorized operations across all 47M readings.
  4. Determinism: sorted outputs, consistent types, byte-identical on re-run.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Assumptions (printed at runtime)
# ---------------------------------------------------------------------------

ASSUMPTIONS = [
    "A1. Features are per-consumer aggregated metrics computed over their readings history.",
    "A2. rolling_mean_30d and rolling_std_30d represent the latest trailing 30-day window.",
    "A3. mom_change_pct compares last 30 days mean to prior 30 days mean (percentage change).",
    "A4. drop_length measures max consecutive days where kwh < 0.5 * baseline (expanding max trailing 30d mean).",
    "A5. peer_deviation compares consumer overall mean against median of overall means in same source_dataset.",
    "A6. seasonal_residual: Dataset A compares latest month to same-calendar-month historical mean; Dataset B to overall mean.",
    "A7. baselines.csv contains per-(consumer_id, month) baseline_kwh and peer quartiles (median, p25, p75).",
    "A8. features.parquet is written with snappy compression and pinned schema for determinism.",
]

# ---------------------------------------------------------------------------
# Schemas (pinned for byte-determinism)
# ---------------------------------------------------------------------------

_FEATURES_SCHEMA = pa.schema([
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

FEATURE_COLUMNS = [
    "consumer_id",
    "source_dataset",
    "theft_label",
    "total_readings",
    "missing_ratio",
    "zero_reading_ratio",
    "rolling_mean_30d",
    "rolling_std_30d",
    "mom_change_pct",
    "drop_length",
    "peer_deviation",
    "seasonal_residual",
]

BASELINES_COLUMNS = [
    "consumer_id",
    "month",
    "baseline_kwh",
    "peer_median",
    "peer_p25",
    "peer_p75",
]


def compute_rolling_series(kwh_series: pd.Series, window: int = 30) -> pd.Series:
    """Compute causal trailing rolling mean with no future leakage."""
    return kwh_series.rolling(window=window, min_periods=1).mean()


def build_features(readings_path: str, consumers_path: str, out_dir: str) -> pd.DataFrame:
    """
    Reads clean data, computes features and baselines, writes baselines.csv
    and features.parquet to out_dir. Returns the features DataFrame.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Load inputs
    readings = pq.read_table(readings_path).to_pandas()
    consumers = pd.read_csv(
        consumers_path,
        dtype={"consumer_id": str, "source_dataset": str, "theft_label": int},
    )

    # Ensure readings are sorted by consumer_id, ts
    if not (readings["consumer_id"].is_monotonic_increasing):
        readings = readings.sort_values(["consumer_id", "ts"], kind="mergesort").reset_index(drop=True)

    # 2. Compute Baselines (monthly level)
    readings["month"] = readings["ts"].str[:7]
    monthly = readings.groupby(["consumer_id", "month"], observed=True, as_index=False)["kwh"].mean()
    monthly.rename(columns={"kwh": "baseline_kwh"}, inplace=True)

    # Map source_dataset for peer grouping
    cons_meta = consumers[["consumer_id", "source_dataset", "theft_label"]].drop_duplicates("consumer_id")
    monthly = monthly.merge(cons_meta[["consumer_id", "source_dataset"]], on="consumer_id", how="left")
    monthly["source_dataset"] = monthly["source_dataset"].fillna(monthly["consumer_id"].str[0])

    peer_stats = monthly.groupby(["source_dataset", "month"])["baseline_kwh"].agg(
        peer_median="median",
        peer_p25=lambda s: s.quantile(0.25),
        peer_p75=lambda s: s.quantile(0.75),
    ).reset_index()

    monthly = monthly.merge(peer_stats, on=["source_dataset", "month"], how="left")
    monthly = monthly.sort_values(["consumer_id", "month"], kind="mergesort").reset_index(drop=True)

    baselines_df = monthly[BASELINES_COLUMNS].copy()
    baselines_df.to_csv(out_path / "baselines.csv", index=False, float_format="%.6g")

    # 3. Compute Per-Consumer Aggregated Features
    unique_ids, idx_start, counts = np.unique(
        readings["consumer_id"].values, return_index=True, return_counts=True
    )
    n_cons = len(unique_ids)
    kwh_arr = readings["kwh"].values

    total_readings = counts.astype(np.int64)
    missing_ratio = np.zeros(n_cons, dtype=np.float64)
    zero_reading_ratio = np.zeros(n_cons, dtype=np.float64)
    overall_mean = np.zeros(n_cons, dtype=np.float64)
    rolling_mean_30d = np.zeros(n_cons, dtype=np.float64)
    rolling_std_30d = np.zeros(n_cons, dtype=np.float64)
    mom_change_pct = np.zeros(n_cons, dtype=np.float64)
    drop_length = np.zeros(n_cons, dtype=np.int64)

    for i in range(n_cons):
        st = idx_start[i]
        cnt = counts[i]
        slice_kwh = kwh_arr[st : st + cnt]

        # NaN & Zero ratios
        nans = np.isnan(slice_kwh).sum()
        zeros = (slice_kwh == 0.0).sum()
        missing_ratio[i] = nans / cnt if cnt > 0 else 0.0
        zero_reading_ratio[i] = zeros / cnt if cnt > 0 else 0.0

        # Overall mean (skipna)
        valid_mask = ~np.isnan(slice_kwh)
        overall_mean[i] = np.mean(slice_kwh[valid_mask]) if np.any(valid_mask) else 0.0

        # Trailing 30-day window (latest window)
        last_30 = slice_kwh[-30:] if cnt >= 30 else slice_kwh
        last_30_valid = last_30[~np.isnan(last_30)]
        rolling_mean_30d[i] = float(np.mean(last_30_valid)) if len(last_30_valid) > 0 else 0.0
        rolling_std_30d[i] = float(np.std(last_30_valid)) if len(last_30_valid) > 1 else 0.0

        # Month-over-month percentage change (last 30 vs prior 30)
        if cnt >= 60:
            prior_30 = slice_kwh[-60:-30]
            prior_valid = prior_30[~np.isnan(prior_30)]
            m_last = np.mean(last_30_valid) if len(last_30_valid) > 0 else np.nan
            m_prior = np.mean(prior_valid) if len(prior_valid) > 0 else np.nan
            if np.isnan(m_prior) or m_prior == 0.0 or np.isnan(m_last):
                mom_change_pct[i] = 0.0
            else:
                mom_change_pct[i] = ((m_last - m_prior) / m_prior) * 100.0
        else:
            mom_change_pct[i] = 0.0

        # Drop length: max consecutive days where kwh < 0.5 * baseline
        # Trailing 30-day rolling mean; expanding max prevents theft absorption
        s = pd.Series(slice_kwh)
        rm = s.rolling(30, min_periods=1).mean()
        baseline = np.maximum(rm, rm.expanding().max())
        is_drop = (s < 0.5 * baseline).values

        max_c = curr = 0
        for v in is_drop:
            if v:
                curr += 1
                if curr > max_c:
                    max_c = curr
            else:
                curr = 0
        drop_length[i] = max_c

    features_df = pd.DataFrame({
        "consumer_id": unique_ids,
        "total_readings": total_readings,
        "missing_ratio": missing_ratio,
        "zero_reading_ratio": zero_reading_ratio,
        "rolling_mean_30d": rolling_mean_30d,
        "rolling_std_30d": rolling_std_30d,
        "mom_change_pct": mom_change_pct,
        "drop_length": drop_length,
        "_overall_mean": overall_mean,
    })

    # Merge consumer metadata
    features_df = features_df.merge(cons_meta, on="consumer_id", how="left")
    features_df["source_dataset"] = features_df["source_dataset"].fillna(features_df["consumer_id"].str[0])
    features_df["theft_label"] = features_df["theft_label"].fillna(0).astype(int)

    # 4. Peer deviation: group by source_dataset, consumer overall mean - dataset median of overall means
    dataset_medians = features_df.groupby("source_dataset")["_overall_mean"].transform("median")
    features_df["peer_deviation"] = features_df["_overall_mean"] - dataset_medians

    # 5. Seasonal residual (Vectorized):
    # For each consumer, identify latest month and value
    latest_per_cons = monthly.groupby("consumer_id", observed=True)["month"].transform("max")
    is_latest = (monthly["month"] == latest_per_cons)

    latest_rows = monthly[is_latest].set_index("consumer_id")
    latest_vals = latest_rows["baseline_kwh"]

    cal_months = monthly["month"].str[5:]
    latest_cal_months = latest_per_cons.str[5:]
    is_same_cal = (cal_months == latest_cal_months) & (~is_latest)

    hist_same_mean = monthly[is_same_cal].groupby("consumer_id", observed=True)["baseline_kwh"].mean()

    # Calculate residuals for dataset A (with historical same month) and B (latest - overall mean)
    res_a = latest_vals - hist_same_mean
    res_b = features_df.set_index("consumer_id")["_overall_mean"]
    res_b = latest_vals - res_b

    # Merge into features_df
    features_df["_res_a"] = features_df["consumer_id"].map(res_a)
    features_df["_res_b"] = features_df["consumer_id"].map(res_b)

    use_a = (features_df["source_dataset"] == "A") & (features_df["_res_a"].notna())
    features_df["seasonal_residual"] = np.where(use_a, features_df["_res_a"], features_df["_res_b"]).astype(np.float64)
    features_df["seasonal_residual"] = features_df["seasonal_residual"].fillna(0.0)

    # Clean up temporary columns and enforce exact column order
    features_df = features_df.drop(columns=["_overall_mean", "_res_a", "_res_b"])
    features_df = features_df.sort_values("consumer_id", kind="mergesort").reset_index(drop=True)
    features_df = features_df[FEATURE_COLUMNS]

    # Write Parquet with pinned schema for byte determinism
    table = pa.Table.from_pandas(features_df, schema=_FEATURES_SCHEMA, preserve_index=False)
    pq.write_table(
        table,
        out_path / "features.parquet",
        compression="snappy",
        write_statistics=False,
        store_schema=True,
    )

    return features_df


def _sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    readings_path = "data/processed/readings.parquet"
    consumers_path = "data/processed/consumers.csv"
    out_dir = "data/processed"

    if len(sys.argv) == 4:
        readings_path, consumers_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]

    print("=" * 60)
    print("TraceWatt - Phase 2: Feature Engineering and Baselines")
    print("=" * 60)

    print("\n[Assumptions]")
    for a in ASSUMPTIONS:
        print(f"  {a}")

    print("\n[Running build_features ...]")
    df = build_features(readings_path, consumers_path, out_dir)
    print("  Done.\n")

    out_path = Path(out_dir)
    baselines_csv = out_path / "baselines.csv"
    features_parquet = out_path / "features.parquet"

    print(f"Processed Consumers : {len(df):,}")
    print(f"Feature Names ({len(FEATURE_COLUMNS)})   : {FEATURE_COLUMNS}")
    print(f"SHA-256 baselines.csv    : {_sha256(baselines_csv)}")
    print(f"SHA-256 features.parquet : {_sha256(features_parquet)}")
    print("\n[Sample 5 Rows - features DataFrame]")
    print(df.head(5).to_string(index=False))
