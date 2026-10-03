"""
backend/services/feeder_analysis.py
===================================
Phase-4 Feeder and Transformer Balance Analysis layer for TraceWatt.
Implements Deliverable D5: Transformer/Feeder Analysis (PRD 16.2, 16.3, 16.6).

Compares transformer input energy with aggregated consumer meters to flag
high unexplained technical and commercial losses and identify suspicious clusters.

KEY DESIGN PRINCIPLES:
  1. Pure pandas balance calculation (compute_feeder_balance) for fast testing and modularity.
  2. SQLAlchemy ORM integration (run_feeder_analysis) for database upsert into feeder_summary.
  3. Strict formulas per PRD Section 16.6.
  4. Deterministic: sorted outputs, consistent types.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Allow imports from app.models or relative fallback
try:
    from app.models import Consumer, FeederSummary, Reading, TransformerReading, Base
except (ImportError, ModuleNotFoundError):
    # Ensure backend directory is in sys.path
    backend_dir = str(Path(__file__).parent.parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from app.models import Consumer, FeederSummary, Reading, TransformerReading, Base

# ---------------------------------------------------------------------------
# Assumptions (printed at runtime)
# ---------------------------------------------------------------------------

ASSUMPTIONS = [
    "A1. Cluster flag threshold: cluster_flag = 1 when unexplained_loss_pct > 15.0%, else 0.",
    "A2. Cluster score heuristic: (unexplained_loss_pct / 100) * (1 + count_of_high_risk_consumers_on_transformer).",
    "A3. Analysis window: inclusive bounds [window_start, window_end].",
    "A4. Division by zero: unexplained_loss_pct = 0.0 when energy_in <= 0.",
    "A5. Null consumption: missing readings (NaN) in consumer meters are skipped (skipna=True).",
]

FEEDER_SUMMARY_COLUMNS = [
    "transformer_id",
    "window_start",
    "window_end",
    "energy_in_kwh",
    "energy_metered_kwh",
    "unexplained_loss_pct",
    "cluster_score",
    "cluster_flag",
]


# ---------------------------------------------------------------------------
# Pure Pandas Balance Engine
# ---------------------------------------------------------------------------

def compute_feeder_balance(
    readings_df: pd.DataFrame,
    transformer_readings_df: pd.DataFrame,
    consumers_df: pd.DataFrame,
    window_start: str,
    window_end: str,
    high_risk_consumer_ids: list[str] | None = None,
) -> pd.DataFrame:
    """
    Computes transformer energy balance over the specified window.

    Formulas (PRD Section 16.6):
      - energy_in = sum(transformer_readings.energy_in_kwh) for transformer in window.
      - energy_metered = sum(readings.kwh) over all consumers assigned to transformer in window.
      - unexplained_loss_pct = ((energy_in - energy_metered) / energy_in) * 100.
      - cluster_score = (unexplained_loss_pct / 100) * (1 + count_of_high_risk_consumers).
      - cluster_flag = 1 if unexplained_loss_pct > 15.0 else 0.

    Returns:
      pd.DataFrame with exact FEEDER_SUMMARY_COLUMNS in order.
    """
    if high_risk_consumer_ids is None:
        high_risk_consumer_ids = []
    high_risk_set = set(high_risk_consumer_ids)

    # 1. Filter transformer readings in window
    if not transformer_readings_df.empty:
        tx_mask = (transformer_readings_df["ts"] >= window_start) & (transformer_readings_df["ts"] <= window_end)
        tx_win = transformer_readings_df[tx_mask]
        tx_in = tx_win.groupby("transformer_id")["energy_in_kwh"].sum().to_dict()
    else:
        tx_in = {}

    # 2. Filter consumer readings in window and map to transformer
    if not readings_df.empty and not consumers_df.empty:
        rdg_mask = (readings_df["ts"] >= window_start) & (readings_df["ts"] <= window_end)
        rdg_win = readings_df[rdg_mask].copy()

        # Merge with consumers to get transformer_id
        cons_map = consumers_df[["consumer_id", "transformer_id"]].dropna().drop_duplicates("consumer_id")
        merged = rdg_win.merge(cons_map, on="consumer_id", how="inner")
        metered = merged.groupby("transformer_id")["kwh"].sum().to_dict()
    else:
        metered = {}

    # 3. High-risk consumer count per transformer
    high_risk_counts = {}
    if not consumers_df.empty and high_risk_set:
        risk_cons = consumers_df[consumers_df["consumer_id"].isin(high_risk_set)]
        high_risk_counts = risk_cons.groupby("transformer_id")["consumer_id"].nunique().to_dict()

    # 4. Determine universe of transformers
    all_transformers = set(tx_in.keys())
    if not consumers_df.empty and "transformer_id" in consumers_df.columns:
        all_transformers.update(consumers_df["transformer_id"].dropna().unique())
    if not transformer_readings_df.empty and "transformer_id" in transformer_readings_df.columns:
        all_transformers.update(transformer_readings_df["transformer_id"].dropna().unique())

    all_transformers = sorted([t for t in all_transformers if t])

    # 5. Compute metrics per transformer
    records = []
    for tx_id in all_transformers:
        e_in = float(tx_in.get(tx_id, 0.0))
        e_met = float(metered.get(tx_id, 0.0))

        if e_in > 0.0:
            loss_pct = float(((e_in - e_met) / e_in) * 100.0)
        else:
            loss_pct = 0.0

        risk_count = int(high_risk_counts.get(tx_id, 0))
        score = float((loss_pct / 100.0) * (1 + risk_count))
        flag = 1 if loss_pct > 15.0 else 0

        records.append({
            "transformer_id": str(tx_id),
            "window_start": str(window_start),
            "window_end": str(window_end),
            "energy_in_kwh": e_in,
            "energy_metered_kwh": e_met,
            "unexplained_loss_pct": loss_pct,
            "cluster_score": score,
            "cluster_flag": flag,
        })

    summary_df = pd.DataFrame(records, columns=FEEDER_SUMMARY_COLUMNS)
    summary_df = summary_df.sort_values("transformer_id", kind="mergesort").reset_index(drop=True)
    return summary_df


# ---------------------------------------------------------------------------
# SQLAlchemy Database Runner
# ---------------------------------------------------------------------------

def run_feeder_analysis(session: Session, window_start: str, window_end: str) -> None:
    """
    PRD 16.3 Contract: Fetches data for the window, computes balance, and upserts
    rows into the feeder_summary table.
    """
    # 1. Fetch transformer readings in window
    tx_stmt = select(TransformerReading).where(
        TransformerReading.ts >= window_start,
        TransformerReading.ts <= window_end,
    )
    tx_rows = session.scalars(tx_stmt).all()
    tx_df = pd.DataFrame([
        {
            "transformer_id": r.transformer_id,
            "ts": r.ts,
            "energy_in_kwh": getattr(r, "energy_in_kwh", getattr(r, "kwh", 0.0)),
        }
        for r in tx_rows
    ])

    # 2. Fetch consumer readings in window
    rdg_stmt = select(Reading).where(
        Reading.ts >= window_start,
        Reading.ts <= window_end,
    )
    rdg_rows = session.scalars(rdg_stmt).all()
    rdg_df = pd.DataFrame([
        {"consumer_id": r.consumer_id, "ts": r.ts, "kwh": r.kwh}
        for r in rdg_rows
    ])

    # 3. Fetch consumers mapping
    cons_stmt = select(Consumer)
    cons_rows = session.scalars(cons_stmt).all()
    cons_df = pd.DataFrame([
        {
            "consumer_id": getattr(c, "consumer_id", getattr(c, "id", "")),
            "transformer_id": c.transformer_id,
        }
        for c in cons_rows
    ])

    # 4. Compute balance metrics
    summary_df = compute_feeder_balance(
        readings_df=rdg_df,
        transformer_readings_df=tx_df,
        consumers_df=cons_df,
        window_start=window_start,
        window_end=window_end,
    )

    # 5. Upsert into feeder_summary table
    for _, row in summary_df.iterrows():
        feeder_obj = FeederSummary(
            transformer_id=row["transformer_id"],
            window_start=row["window_start"],
            window_end=row["window_end"],
            energy_in_kwh=row["energy_in_kwh"],
            energy_metered_kwh=row["energy_metered_kwh"],
            unexplained_loss_pct=row["unexplained_loss_pct"],
            cluster_score=row["cluster_score"],
            cluster_flag=row["cluster_flag"],
        )
        session.merge(feeder_obj)

    session.commit()


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 65)
    print("TraceWatt - Phase 4: Transformer / Feeder Analysis")
    print("=" * 65)

    print("\n[Assumptions]")
    for a in ASSUMPTIONS:
        print(f"  {a}")

    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    window_start = "2024-01-01"
    window_end = "2024-01-31"

    # Seed mock data
    with Session(engine) as session:
        # Consumers
        session.add_all([
            Consumer(consumer_id="C_1", transformer_id="TX_01"),
            Consumer(consumer_id="C_2", transformer_id="TX_01"),
            Consumer(consumer_id="C_3", transformer_id="TX_02"),
        ])

        # Transformer readings (TX_01 = 100 kWh, TX_02 = 50 kWh)
        session.add_all([
            TransformerReading(transformer_id="TX_01", ts="2024-01-15", energy_in_kwh=100.0),
            TransformerReading(transformer_id="TX_02", ts="2024-01-15", energy_in_kwh=50.0),
        ])

        # Consumer readings (C_1=40, C_2=40 -> TX_01 sum = 80; C_3=48 -> TX_02 sum = 48)
        session.add_all([
            Reading(consumer_id="C_1", ts="2024-01-15", kwh=40.0),
            Reading(consumer_id="C_2", ts="2024-01-15", kwh=40.0),
            Reading(consumer_id="C_3", ts="2024-01-15", kwh=48.0),
        ])
        session.commit()

        print("\n[Running run_feeder_analysis ...]")
        run_feeder_analysis(session, window_start, window_end)
        print("  Done.")

        # Query and display resulting feeder_summary
        stmt = select(FeederSummary).order_by(FeederSummary.transformer_id)
        results = session.scalars(stmt).all()
        res_df = pd.DataFrame([
            {
                "transformer_id": r.transformer_id,
                "window_start": r.window_start,
                "window_end": r.window_end,
                "energy_in_kwh": r.energy_in_kwh,
                "energy_metered_kwh": r.energy_metered_kwh,
                "unexplained_loss_pct": r.unexplained_loss_pct,
                "cluster_score": r.cluster_score,
                "cluster_flag": r.cluster_flag,
            }
            for r in results
        ])

        print("\n[Feeder Summary Results]")
        print(res_df.to_string(index=False))
