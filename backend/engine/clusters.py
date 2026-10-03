"""
backend/engine/clusters.py
==========================
TraceWatt Phase-4: Feeder and transformer cluster scoring.

Public API:
    feeder_clusters(balance_df, detections) -> pd.DataFrame

Adds two columns to the balance DataFrame:
  - cluster_flag  : int   1 if unexplained_loss_pct > 15.0 else 0
  - cluster_score : float (unexplained_loss_pct / 100) * (1 + high_risk_count)
"""

from __future__ import annotations

import pandas as pd


def feeder_clusters(
    balance_df: pd.DataFrame,
    detections: list[dict],
) -> pd.DataFrame:
    """
    Score feeder/transformer clusters for systemic loss.

    Parameters
    ----------
    balance_df : DataFrame containing at minimum:
        - feeder_id (str)
        - unexplained_loss_pct (float)  — % of transformer output unaccounted for

        Optionally:
        - transformer_id (str)
        - total_consumers (int)

    detections : list[dict] — Detection dicts from analyze() / analyze_all().
        Each dict must have: consumer_id, risk_level, cause.
        Optionally: feeder_id (used to join; if absent, joined via consumer lookup).

    Returns
    -------
    pd.DataFrame — balance_df copy with two new columns appended:
        cluster_flag  : int   (0 or 1)
        cluster_score : float
    """
    df = balance_df.copy()

    # ── Build feeder → high-risk count lookup from detections ───────────────
    # Collect high-risk detections per feeder_id
    feeder_high_risk: dict[str, int] = {}

    for det in detections:
        fid = det.get("feeder_id", "")
        if not fid:
            continue
        if det.get("risk_level") == "High":
            feeder_high_risk[fid] = feeder_high_risk.get(fid, 0) + 1

    # Map high_risk_count into balance_df
    if "feeder_id" in df.columns:
        df["high_risk_count"] = df["feeder_id"].map(feeder_high_risk).fillna(0).astype(int)
    else:
        df["high_risk_count"] = 0

    # ── Ensure unexplained_loss_pct column exists ───────────────────────────
    if "unexplained_loss_pct" not in df.columns:
        df["unexplained_loss_pct"] = 0.0

    loss_pct = df["unexplained_loss_pct"].fillna(0.0)

    # ── Cluster flag ─────────────────────────────────────────────────────────
    df["cluster_flag"] = (loss_pct > 15.0).astype(int)

    # ── Cluster score ─────────────────────────────────────────────────────────
    df["cluster_score"] = (loss_pct / 100.0) * (1.0 + df["high_risk_count"])

    return df


def transformer_clusters(
    balance_df: pd.DataFrame,
    detections: list[dict],
) -> pd.DataFrame:
    """
    Same as feeder_clusters but grouped at the transformer level.

    Parameters
    ----------
    balance_df : DataFrame with transformer_id and unexplained_loss_pct columns.
    detections : list[dict] with transformer_id and risk_level fields.

    Returns
    -------
    pd.DataFrame with cluster_flag and cluster_score columns added.
    """
    df = balance_df.copy()

    tx_high_risk: dict[str, int] = {}
    for det in detections:
        txid = det.get("transformer_id", "")
        if not txid:
            continue
        if det.get("risk_level") == "High":
            tx_high_risk[txid] = tx_high_risk.get(txid, 0) + 1

    if "transformer_id" in df.columns:
        df["high_risk_count"] = df["transformer_id"].map(tx_high_risk).fillna(0).astype(int)
    else:
        df["high_risk_count"] = 0

    if "unexplained_loss_pct" not in df.columns:
        df["unexplained_loss_pct"] = 0.0

    loss_pct = df["unexplained_loss_pct"].fillna(0.0)

    df["cluster_flag"] = (loss_pct > 15.0).astype(int)
    df["cluster_score"] = (loss_pct / 100.0) * (1.0 + df["high_risk_count"])

    return df
