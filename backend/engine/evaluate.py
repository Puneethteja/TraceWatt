"""
backend/engine/evaluate.py
==========================
TraceWatt Phase-4: Evaluation script for the ML detection engine.

Measures against synthetic scenario ground truth:
  - Theft detection : Precision, Recall, F1, PR-AUC, ROC-AUC, FPR, FNR
  - Cause accuracy  : Accuracy across all 7 cause classes
  - Latency         : Per-consumer inference time (must be < 1.0s)

Usage:
  cd backend
  python engine/evaluate.py
  python engine/evaluate.py --data-dir ../data/processed --model-dir engine/models
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    classification_report,
)

# Add backend to path for imports
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from engine.analyze import analyze  # noqa: E402

# Mapping from generate_synthetic.py TRUE_CAUSES to our 7-class display labels
TRUE_CAUSE_MAP = {
    "Theft/Tampering": "Suspected theft/tampering",
    "Meter Malfunction": "Meter malfunction",
    "Communication Failure": "Communication failure",
    "Legitimate Abnormal": "Legitimate abnormal usage",
    "Seasonal Variation": "Seasonal variation",
    "Normal": "Normal",
}

# Cause → theft binary label (for Precision/Recall/AUC)
THEFT_CAUSE = "Suspected theft/tampering"


def load_synthetic_data(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load:
      - synthetic_readings.parquet
      - labels.csv
      - consumers_synthetic.csv

    Returns (readings_df, labels_df, consumers_df).
    """
    dpath = Path(data_dir)
    readings_path = dpath / "synthetic_readings.parquet"
    labels_path = dpath / "labels.csv"
    consumers_path = dpath / "consumers_synthetic.csv"

    if not readings_path.exists():
        raise FileNotFoundError(
            f"synthetic_readings.parquet not found in {data_dir}. "
            "Run backend/scripts/generate_synthetic.py first."
        )

    readings_df = pq.read_table(str(readings_path)).to_pandas()
    labels_df = pd.read_csv(str(labels_path))
    consumers_df = pd.read_csv(str(consumers_path))

    print(f"[Data] Synthetic consumers : {labels_df['consumer_id'].nunique():,}")
    print(f"[Data] Reading records     : {len(readings_df):,}")
    print(f"[Data] True cause dist:\n{labels_df['true_cause'].value_counts().to_string()}")
    print()

    return readings_df, labels_df, consumers_df


def run_evaluation(data_dir: str) -> dict:
    """
    Main evaluation pipeline.

    Returns dict with all metric values.
    """
    readings_df, labels_df, consumers_df = load_synthetic_data(data_dir)

    # ── Group readings by consumer ──────────────────────────────────────────
    readings_grouped = readings_df.groupby("consumer_id", sort=False)
    cons_meta = consumers_df.set_index("consumer_id")

    results: list[dict] = []
    latencies: list[float] = []

    print("[Evaluating] Running analyze() on each synthetic consumer...")

    for _, label_row in labels_df.iterrows():
        cid = str(label_row["consumer_id"])
        raw_true_cause = str(label_row["true_cause"])
        true_cause = TRUE_CAUSE_MAP.get(raw_true_cause, raw_true_cause)

        # Build readings window
        try:
            c_df = readings_grouped.get_group(cid).copy()
        except KeyError:
            continue

        # Rename generated_kwh → kwh for the engine
        if "generated_kwh" in c_df.columns and "kwh" not in c_df.columns:
            c_df = c_df.rename(columns={"generated_kwh": "kwh"})
        elif "generated_kwh" in c_df.columns:
            c_df = c_df.copy()
            c_df["kwh"] = c_df["generated_kwh"]

        # If in_event_window is present and contains True, evaluate at the event occurrence
        if "in_event_window" in c_df.columns and c_df["in_event_window"].any():
            event_indices = c_df.index[c_df["in_event_window"]]
            event_end_pos = c_df.index.get_loc(event_indices[-1])
            eval_df = c_df.iloc[max(0, event_end_pos - 99) : event_end_pos + 1].copy()
        else:
            eval_df = c_df.tail(100).copy()

        # Consumer row
        if cid in cons_meta.index:
            consumer_row = cons_meta.loc[cid]
        else:
            consumer_row = {"consumer_id": cid, "tariff": 0.15, "category": "residential"}

        # Timed inference
        t0 = time.perf_counter()
        try:
            det = analyze(cid, eval_df, consumer_row)
        except Exception as e:
            print(f"  [WARN] analyze() failed for {cid}: {e}")
            continue
        elapsed = time.perf_counter() - t0
        latencies.append(elapsed)

        results.append({
            "consumer_id": cid,
            "true_cause": true_cause,
            "predicted_cause": det["cause"],
            "anomaly_score": det["anomaly_score"],
            "confidence": det["confidence"],
            "risk_level": det["risk_level"],
            "latency_s": elapsed,
        })

    if not results:
        raise RuntimeError("No evaluation results collected. Check data and model paths.")

    results_df = pd.DataFrame(results)
    n = len(results_df)

    # ── Theft Binary Classification ─────────────────────────────────────────
    y_true_theft = (results_df["true_cause"] == THEFT_CAUSE).astype(int)
    y_pred_theft = (results_df["predicted_cause"] == THEFT_CAUSE).astype(int)
    y_score_theft = results_df["anomaly_score"].values

    has_both_classes = y_true_theft.sum() > 0 and (y_true_theft == 0).sum() > 0

    theft_precision = precision_score(y_true_theft, y_pred_theft, zero_division=0)
    theft_recall = recall_score(y_true_theft, y_pred_theft, zero_division=0)
    theft_f1 = f1_score(y_true_theft, y_pred_theft, zero_division=0)
    theft_pr_auc = average_precision_score(y_true_theft, y_score_theft) if has_both_classes else float("nan")
    theft_roc_auc = roc_auc_score(y_true_theft, y_score_theft) if has_both_classes else float("nan")

    # FPR and FNR from confusion matrix
    if has_both_classes:
        tn, fp, fn, tp = confusion_matrix(y_true_theft, y_pred_theft).ravel()
        fpr = fp / max(fp + tn, 1)
        fnr = fn / max(fn + tp, 1)
    else:
        fpr = fnr = float("nan")

    # ── Cause Classification Accuracy ───────────────────────────────────────
    # Normalize "Requires Review" as a class only if that was the true label
    # For evaluation: predicted "Requires Review" on a true theft → wrong
    cause_acc = float((results_df["predicted_cause"] == results_df["true_cause"]).mean())

    # ── Latency ─────────────────────────────────────────────────────────────
    lat_arr = np.array(latencies)
    lat_mean = float(lat_arr.mean())
    lat_p95 = float(np.percentile(lat_arr, 95))
    lat_max = float(lat_arr.max())

    # Print Report
    sep = "=" * 62
    print(sep)
    print("TraceWatt Engine -- Evaluation Report")
    print(sep)

    print(f"\n{'Consumers evaluated':<35}: {n}")

    print(f"\n-- Theft Detection --")
    print(f"  {'Precision':<33}: {theft_precision:.4f}  {'PASS' if theft_precision >= 0.70 else 'FAIL (target >= 0.70)'}")
    print(f"  {'Recall':<33}: {theft_recall:.4f}  {'PASS' if theft_recall >= 0.80 else 'FAIL (target >= 0.80)'}")
    print(f"  {'F1':<33}: {theft_f1:.4f}")
    print(f"  {'PR-AUC':<33}: {theft_pr_auc:.4f}")
    print(f"  {'ROC-AUC':<33}: {theft_roc_auc:.4f}")
    print(f"  {'FPR (False Positive Rate)':<33}: {fpr:.4f}")
    print(f"  {'FNR (False Negative Rate)':<33}: {fnr:.4f}")

    print(f"\n-- Cause Classification --")
    print(f"  {'Accuracy (7 classes)':<33}: {cause_acc:.4f}  {'PASS' if cause_acc >= 0.80 else 'FAIL (target >= 0.80)'}")

    print("\n  Per-class breakdown:")
    print(
        classification_report(
            results_df["true_cause"],
            results_df["predicted_cause"],
            labels=list(TRUE_CAUSE_MAP.values()),
            zero_division=0,
        )
    )

    print(f"\n-- Inference Latency --")
    print(f"  {'Mean latency (s)':<33}: {lat_mean:.4f}  {'PASS' if lat_mean < 1.0 else 'FAIL (target < 1.0s)'}")
    print(f"  {'p95 latency (s)':<33}: {lat_p95:.4f}")
    print(f"  {'Max latency (s)':<33}: {lat_max:.4f}")

    print(f"\n-- Acceptance Check --")
    passed = (
        theft_recall >= 0.80
        and theft_precision >= 0.70
        and cause_acc >= 0.80
        and lat_mean < 1.0
    )
    print(f"  ALL TARGETS MET: {'[PASS]' if passed else '[FAIL]'}")
    print(sep)

    return {
        "theft_precision": theft_precision,
        "theft_recall": theft_recall,
        "theft_f1": theft_f1,
        "theft_pr_auc": theft_pr_auc,
        "theft_roc_auc": theft_roc_auc,
        "fpr": fpr,
        "fnr": fnr,
        "cause_accuracy": cause_acc,
        "latency_mean_s": lat_mean,
        "latency_p95_s": lat_p95,
        "latency_max_s": lat_max,
        "n_evaluated": n,
        "passed": passed,
        "results_df": results_df,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TraceWatt Engine — Evaluate")
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).resolve().parents[2] / "data" / "processed"),
        help="Directory with synthetic_readings.parquet and labels.csv",
    )
    parser.add_argument(
        "--model-dir",
        default=str(Path(__file__).resolve().parent / "models"),
        help="Directory containing trained model artifacts",
    )
    args = parser.parse_args()

    metrics = run_evaluation(args.data_dir)
    sys.exit(0 if metrics["passed"] else 1)
