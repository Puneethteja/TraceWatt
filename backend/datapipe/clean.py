"""
backend/datapipe/clean.py
=========================
Phase-1 data-cleaning layer for TraceWatt.

Reads two wide-format raw CSVs and writes:
  - data/processed/consumers.csv          (small, human-readable)
  - data/processed/readings.parquet       (full long-format, compressed)
  - data/processed/readings_demo.csv      (first 50 consumers, for inspection)

KEY DESIGN DECISIONS (see ASSUMPTIONS list / printed at runtime):
  A1. File-B rows where CONS_NO is NaN are dropped (no consumer identity).
  A2. File-A rows where FLAG is NaN -> theft_label = -1 (sentinel, not dropped).
  A3. File-B rows where CHK_STATE is NaN -> theft_label = -1 (sentinel, not dropped).
  A4. NaN and 0.0 in kwh are PRESERVED exactly; they are semantically different signals.
  A5. File-B date format: %d-%m-%y (two-digit year, 2000-based century).
  A6. File-A date format: %Y/%m/%d (four-digit year, no zero-padding).
  A7. Duplicate CONS_NO within the same source are kept as-is (no deduplication).
  A8. Parquet written with snappy compression and fixed schema for byte-determinism.
  A9. readings_demo.csv = first 50 consumer_ids (alphabetically) from the full output.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Assumptions (printed at runtime)
# ---------------------------------------------------------------------------

ASSUMPTIONS = [
    "A1. File-B rows where CONS_NO is NaN are dropped (no consumer identity).",
    "A2. File-A rows where FLAG is NaN -> theft_label = -1 (sentinel, not dropped).",
    "A3. File-B rows where CHK_STATE is NaN -> theft_label = -1 (sentinel, not dropped).",
    "A4. NaN and 0.0 in kwh are preserved exactly; they carry different semantic meaning.",
    "A5. File-B date format: %d-%m-%y (two-digit year, 2000-based century).",
    "A6. File-A date format: %Y/%m/%d (four-digit year, no zero-padding).",
    "A7. Duplicate CONS_NO within the same source are kept as-is (not deduplicated).",
    "A8. Parquet written with snappy compression; schema pinned for byte-determinism.",
    "A9. readings_demo.csv = first 50 consumer_ids alphabetically from full readings.",
]

# ---------------------------------------------------------------------------
# Parquet schema (pinned for determinism)
# ---------------------------------------------------------------------------

_READINGS_SCHEMA = pa.schema([
    pa.field("consumer_id", pa.string()),
    pa.field("ts",          pa.string()),
    pa.field("kwh",         pa.float64()),
])

# Number of consumers to include in the demo CSV
_DEMO_N_CONSUMERS = 50

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def clean_raw_data(file_a_path: str, file_b_path: str, out_dir: str) -> None:
    """
    Read both raw CSVs, apply all cleaning rules, and write:
      <out_dir>/consumers.csv
      <out_dir>/readings.parquet
      <out_dir>/readings_demo.csv

    Parameters
    ----------
    file_a_path : str   Path to File A (data.csv).
    file_b_path : str   Path to File B (Electricity_Theft_Data.csv).
    out_dir     : str   Output directory (created if absent).
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    cons_a, rdg_a = _process_file_a(file_a_path)
    cons_b, rdg_b = _process_file_b(file_b_path)

    # ── Merge ────────────────────────────────────────────────────────────────
    consumers = pd.concat([cons_a, cons_b], ignore_index=True)
    readings  = pd.concat([rdg_a,  rdg_b],  ignore_index=True)

    # ── Sort (deterministic) ─────────────────────────────────────────────────
    consumers = consumers.sort_values("consumer_id", kind="mergesort").reset_index(drop=True)
    readings  = readings.sort_values(["consumer_id", "ts"], kind="mergesort").reset_index(drop=True)

    # ── Enforce exact column order ───────────────────────────────────────────
    consumers = consumers[["consumer_id", "cons_no_original", "source_dataset",
                            "theft_label", "label_source"]]
    readings  = readings[["consumer_id", "ts", "kwh"]]

    # ── Write consumers.csv ──────────────────────────────────────────────────
    consumers.to_csv(out_path / "consumers.csv", index=False)

    # ── Write readings.parquet ───────────────────────────────────────────────
    _write_parquet(readings, out_path / "readings.parquet")

    # ── Write readings_demo.csv (first N consumer_ids) ───────────────────────
    demo_ids = sorted(readings["consumer_id"].unique())[:_DEMO_N_CONSUMERS]
    demo     = readings[readings["consumer_id"].isin(demo_ids)]
    demo.to_csv(out_path / "readings_demo.csv", index=False, float_format="%.10g")


# ---------------------------------------------------------------------------
# Parquet helper
# ---------------------------------------------------------------------------


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write readings DataFrame to Parquet with a pinned schema for determinism."""
    table = pa.Table.from_pandas(df, schema=_READINGS_SCHEMA, preserve_index=False)
    pq.write_table(
        table,
        path,
        compression="snappy",
        write_statistics=False,   # exclude mutable stats for byte-determinism
        store_schema=True,
    )


# ---------------------------------------------------------------------------
# File-A processing
# ---------------------------------------------------------------------------


def _process_file_a(path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Process data.csv -> (consumers_df, readings_df)."""

    # Read: CONS_NO must be str (Trap 3)
    df = pd.read_csv(path, dtype={"CONS_NO": str})

    meta_cols     = ["CONS_NO", "FLAG"]
    raw_date_cols = [c for c in df.columns if c not in meta_cols]

    # Parse date columns with explicit format, then sort chronologically (Traps 1 & 2)
    parsed_dates  = pd.to_datetime(raw_date_cols, format="%Y/%m/%d")
    order         = parsed_dates.argsort()
    sorted_date_cols = [raw_date_cols[i] for i in order]
    sorted_parsed    = [parsed_dates[i]  for i in order]

    # ── Consumers ────────────────────────────────────────────────────────────
    # Check NaN BEFORE casting FLAG (Trap 4 / Assumption A2)
    flag_raw    = df["FLAG"]
    has_nan     = flag_raw.isna()
    theft_label = flag_raw.copy()
    theft_label[has_nan]  = -1
    theft_label[~has_nan] = flag_raw[~has_nan].astype(int)
    theft_label = theft_label.astype(int)

    cons_no_str = df["CONS_NO"].astype(str)
    consumers = pd.DataFrame({
        "consumer_id":      "A_" + cons_no_str,
        "cons_no_original":  cons_no_str,
        "source_dataset":   "A",
        "theft_label":      theft_label,
        "label_source":     "FLAG",
    })

    # ── Readings (melt) ──────────────────────────────────────────────────────
    # Rename date columns to ISO strings before melting
    date_col_map = {raw: dt.strftime("%Y-%m-%d")
                    for raw, dt in zip(sorted_date_cols, sorted_parsed)}
    df_wide = df[["CONS_NO"] + sorted_date_cols].copy()
    df_wide.rename(columns=date_col_map, inplace=True)
    iso_cols = [date_col_map[c] for c in sorted_date_cols]

    readings = df_wide.melt(id_vars="CONS_NO", value_vars=iso_cols,
                             var_name="ts", value_name="kwh")
    readings["consumer_id"] = "A_" + readings["CONS_NO"].astype(str)
    readings = readings[["consumer_id", "ts", "kwh"]]

    return consumers, readings


# ---------------------------------------------------------------------------
# File-B processing
# ---------------------------------------------------------------------------


def _process_file_b(path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Process Electricity_Theft_Data.csv -> (consumers_df, readings_df)."""

    # All columns read as float initially (Trap 5)
    df = pd.read_csv(path)

    # Drop rows with NaN CONS_NO (Assumption A1)
    df = df[df["CONS_NO"].notna()].copy()

    # Strip trailing ".0" from float CONS_NO (Trap 5)
    df["CONS_NO"] = df["CONS_NO"].apply(
        lambda x: str(int(x)) if float(x) == int(float(x)) else str(x)
    )

    meta_cols     = ["CONS_NO", "CHK_STATE"]
    raw_date_cols = [c for c in df.columns if c not in meta_cols]

    # Parse date columns %d-%m-%y, sort chronologically (Trap 6)
    parsed_dates     = pd.to_datetime(raw_date_cols, format="%d-%m-%y")
    order            = parsed_dates.argsort()
    sorted_date_cols = [raw_date_cols[i] for i in order]
    sorted_parsed    = [parsed_dates[i]  for i in order]

    # ── Consumers ────────────────────────────────────────────────────────────
    chk_raw     = df["CHK_STATE"]
    has_nan     = chk_raw.isna()
    theft_label = chk_raw.copy()
    theft_label[has_nan]  = -1
    theft_label[~has_nan] = chk_raw[~has_nan].astype(int)
    theft_label = theft_label.astype(int)

    cons_no_str = df["CONS_NO"].astype(str)
    consumers = pd.DataFrame({
        "consumer_id":      "B_" + cons_no_str,
        "cons_no_original":  cons_no_str,
        "source_dataset":   "B",
        "theft_label":      theft_label,
        "label_source":     "CHK_STATE",
    })

    # ── Readings (melt) ──────────────────────────────────────────────────────
    date_col_map = {raw: dt.strftime("%Y-%m-%d")
                    for raw, dt in zip(sorted_date_cols, sorted_parsed)}
    df_wide = df[["CONS_NO"] + sorted_date_cols].copy()
    df_wide.rename(columns=date_col_map, inplace=True)
    iso_cols = [date_col_map[c] for c in sorted_date_cols]

    readings = df_wide.melt(id_vars="CONS_NO", value_vars=iso_cols,
                             var_name="ts", value_name="kwh")
    readings["consumer_id"] = "B_" + readings["CONS_NO"].astype(str)
    readings = readings[["consumer_id", "ts", "kwh"]]

    return consumers, readings


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------


def _fmt_size(path: Path) -> str:
    """Return human-readable file size."""
    b = path.stat().st_size
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


if __name__ == "__main__":
    file_a = "C:\\Users\\DELL\\TraceWatt\\backend\\data\\raw\\data.csv"
    file_b = "C:\\Users\\DELL\\TraceWatt\\backend\\data\\raw\\Electricity_Theft_Data.csv"
    out    = "C:\\Users\\DELL\\TraceWatt\\backend\\data\\processed"

    if len(sys.argv) == 4:
        file_a, file_b, out = sys.argv[1], sys.argv[2], sys.argv[3]

    print("=" * 60)
    print("TraceWatt - Phase 1: Data Cleaning")
    print("=" * 60)

    print("\n[Assumptions]")
    for a in ASSUMPTIONS:
        print(f"  {a}")

    print("\n[Running clean_raw_data ...]")
    clean_raw_data(file_a, file_b, out)
    print("  Done.\n")

    out_path    = Path(out)
    cons_csv    = out_path / "consumers.csv"
    rdg_parquet = out_path / "readings.parquet"
    rdg_demo    = out_path / "readings_demo.csv"

    consumers = pd.read_csv(cons_csv, dtype={"consumer_id": str,
                                              "cons_no_original": str,
                                              "source_dataset": str})
    readings  = pq.read_table(rdg_parquet).to_pandas()

    for src in ("A", "B"):
        c_src  = consumers[consumers["source_dataset"] == src]
        r_src  = readings[readings["consumer_id"].str.startswith(src + "_")]
        nan_k  = r_src["kwh"].isna().sum()
        zero_k = (r_src["kwh"] == 0.0).sum()
        print(f"[Source {src}]")
        print(f"  Consumers     : {len(c_src):,}")
        print(f"  Readings rows : {len(r_src):,}")
        print(f"  kwh NaN count : {nan_k:,}")
        print(f"  kwh 0.0 count : {zero_k:,}")

    print()
    print(f"[Output file sizes]")
    print(f"  consumers.csv    : {_fmt_size(cons_csv)}")
    print(f"  readings.parquet : {_fmt_size(rdg_parquet)}")
    print(f"  readings_demo.csv: {_fmt_size(rdg_demo)}")

    print()
    print("[First 5 rows -- consumers.csv]")
    print(pd.read_csv(cons_csv, dtype=str).head(5).to_string(index=False))
    print()
    print("[First 10 rows -- readings_demo.csv]")
    print(pd.read_csv(rdg_demo, dtype={"consumer_id": str, "ts": str}).head(10).to_string(index=False))
