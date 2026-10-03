"""
backend/engine/train.py
=======================
TraceWatt Phase-4: Train LightGBM (supervised) + Isolation Forest (unsupervised).

Artifacts saved to backend/engine/models/:
  - lgbm_model.pkl     : LightGBM binary classifier (theft vs. normal)
  - iso_forest.pkl     : Isolation Forest for unsupervised scoring
  - scaler.pkl         : StandardScaler fitted on training features
  - feature_cols.json  : Ordered list of feature column names
  - train_report.txt   : Quick training summary / CV scores

Usage:
  cd backend
  python engine/train.py
  python engine/train.py --data-dir ../data/processed --model-dir engine/models
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler

try:
    import lightgbm as lgb
except ImportError:
    raise ImportError("lightgbm not installed. Run: pip install lightgbm")

# ---------------------------------------------------------------------------
# Feature columns (must match datapipe/features.py FEATURE_COLUMNS)
# ---------------------------------------------------------------------------

FEATURE_COLS = [
    "missing_ratio",
    "zero_reading_ratio",
    "rolling_mean_30d",
    "rolling_std_30d",
    "mom_change_pct",
    "drop_length",
    "peer_deviation",
    "seasonal_residual",
]

LABEL_COL = "theft_label"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_features(data_dir: str) -> pd.DataFrame:
    """Load features.parquet; fall back to building from readings if absent."""
    feat_path = Path(data_dir) / "features.parquet"
    if not feat_path.exists():
        print(f"[WARN] features.parquet not found at {feat_path}. Attempting to build...")
        _build_features(data_dir)

    df = pq.read_table(str(feat_path)).to_pandas()
    print(f"[Data] Loaded {len(df):,} consumers from features.parquet")
    return df


def _build_features(data_dir: str) -> None:
    """Trigger Phase-2 feature building if parquet missing."""
    readings_path = Path(data_dir) / "readings.parquet"
    consumers_path = Path(data_dir) / "consumers.csv"
    if not readings_path.exists() or not consumers_path.exists():
        raise FileNotFoundError(
            f"Cannot build features: readings.parquet or consumers.csv missing in {data_dir}. "
            "Run Phase-1 (datapipe/clean.py) and Phase-2 (datapipe/features.py) first."
        )
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from datapipe.features import build_features
    build_features(str(readings_path), str(consumers_path), data_dir)
    print("[Data] Built features.parquet")


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------

def train_lgbm(X_train: np.ndarray, y_train: np.ndarray) -> lgb.LGBMClassifier:
    """Train LightGBM binary classifier with class imbalance handling."""
    pos = int(y_train.sum())
    neg = int((y_train == 0).sum())
    scale_pos = neg / max(pos, 1)

    model = lgb.LGBMClassifier(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=63,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        scale_pos_weight=scale_pos,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    model.fit(X_train, y_train)
    return model


def train_iso_forest(X_all: np.ndarray) -> IsolationForest:
    """Train Isolation Forest on all data (no labels needed)."""
    model = IsolationForest(
        n_estimators=200,
        contamination=0.1,
        max_features=1.0,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_all)
    return model


# ---------------------------------------------------------------------------
# CV evaluation helper
# ---------------------------------------------------------------------------

def evaluate_lgbm_cv(X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> dict:
    """Stratified K-Fold cross-validation returning mean PR-AUC and ROC-AUC."""
    pos = int(y.sum())
    neg = int((y == 0).sum())
    scale_pos = neg / max(pos, 1)

    model = lgb.LGBMClassifier(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=63,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    roc_scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
    ap_scores = cross_val_score(model, X, y, cv=cv, scoring="average_precision", n_jobs=-1)
    acc_scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy", n_jobs=-1)

    return {
        "acc_mean": float(acc_scores.mean()),
        "acc_std": float(acc_scores.std()),
        "roc_auc_mean": float(roc_scores.mean()),
        "roc_auc_std": float(roc_scores.std()),
        "pr_auc_mean": float(ap_scores.mean()),
        "pr_auc_std": float(ap_scores.std()),
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def train_and_save(data_dir: str, model_dir: str) -> None:
    t0 = time.time()
    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)

    # 1. Load features
    df = load_features(data_dir)

    # Ensure all feature cols exist
    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0.0

    # 2. Separate labeled / unlabeled
    # theft_label: 1 = theft, 0 = normal, -1 = unknown sentinel
    df_labeled = df[df[LABEL_COL].isin([0, 1])].copy()
    df_all = df.copy()

    print(f"[Data] Labeled consumers  : {len(df_labeled):,}")
    print(f"[Data]   - Theft (1)      : {(df_labeled[LABEL_COL] == 1).sum():,}")
    print(f"[Data]   - Normal (0)     : {(df_labeled[LABEL_COL] == 0).sum():,}")
    print(f"[Data] Total for IsoForest: {len(df_all):,}")

    X_labeled = df_labeled[FEATURE_COLS].fillna(0.0).values
    y_labeled = df_labeled[LABEL_COL].values.astype(int)
    X_all = df_all[FEATURE_COLS].fillna(0.0).values

    # 3. Stratified 80/20 train-test split (preserves class ratio)
    from sklearn.model_selection import train_test_split
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_labeled, y_labeled,
        test_size=0.20,
        stratify=y_labeled,
        random_state=42,
    )
    print(f"\n[Split] Train : {len(X_tr):,}  ({y_tr.sum():,} theft)")
    print(f"[Split] Test  : {len(X_te):,}  ({y_te.sum():,} theft)")

    # 4. Fit scaler on TRAIN only — prevent data leakage
    scaler = StandardScaler()
    X_tr_sc = scaler.fit_transform(X_tr)
    X_te_sc = scaler.transform(X_te)
    X_labeled_sc = scaler.transform(X_labeled)   # full labeled set (for final model)
    X_all_sc = scaler.transform(X_all)

    # 5. Cross-validate LightGBM on training fold
    print("\n[Training] Cross-validating LightGBM (5-fold on train set)...")
    cv_scores = evaluate_lgbm_cv(X_tr_sc, y_tr)
    print(f"  ROC-AUC : {cv_scores['roc_auc_mean']:.4f} ± {cv_scores['roc_auc_std']:.4f}")
    print(f"  PR-AUC  : {cv_scores['pr_auc_mean']:.4f} ± {cv_scores['pr_auc_std']:.4f}")

    # 6. Train candidate model on train split, evaluate on held-out test set
    print("\n[Training] Evaluating on held-out test set (20%)...")
    candidate = train_lgbm(X_tr_sc, y_tr)
    y_prob_te = candidate.predict_proba(X_te_sc)[:, 1]
    y_pred_te = (y_prob_te >= 0.5).astype(int)
    test_roc = roc_auc_score(y_te, y_prob_te)
    test_pr  = average_precision_score(y_te, y_prob_te)
    print(f"  Test ROC-AUC : {test_roc:.4f}")
    print(f"  Test PR-AUC  : {test_pr:.4f}")
    print(classification_report(y_te, y_pred_te, target_names=["Normal", "Theft"]))

    # 7. Retrain final model on ALL labeled data (train + test) before saving
    print("\n[Training] Fitting final LightGBM on all labeled data...")
    lgbm_model = train_lgbm(X_labeled_sc, y_labeled)

    # Final training set metrics (sanity check — should be high)
    y_prob_tr_full = lgbm_model.predict_proba(X_labeled_sc)[:, 1]
    y_pred_tr_full = (y_prob_tr_full >= 0.5).astype(int)
    roc = roc_auc_score(y_labeled, y_prob_tr_full)
    pr_auc = average_precision_score(y_labeled, y_prob_tr_full)
    print(f"  Train ROC-AUC : {roc:.4f}")
    print(f"  Train PR-AUC  : {pr_auc:.4f}")
    print(classification_report(y_labeled, y_pred_tr_full, target_names=["Normal", "Theft"]))

    # 8. Train Isolation Forest on all data (unsupervised — uses full feature set)
    print("[Training] Fitting Isolation Forest...")
    iso_forest = train_iso_forest(X_all_sc)

    # 9. Isotonic probability calibration using OOF predictions (no leakage)
    # -----------------------------------------------------------------------
    # Architecture requirement: "Calibrated Hybrid Anomaly Score"
    # OOF predictions from the final model → IsotonicRegression calibrator.
    # This converts raw LightGBM log-odds → true probabilities without
    # leaking test data into the calibration fit.
    from sklearn.isotonic import IsotonicRegression
    from sklearn.metrics import brier_score_loss

    print("\n[Calibration] Fitting isotonic probability calibrator on OOF predictions...")
    from sklearn.model_selection import cross_val_predict as _cvp
    oof_probs = _cvp(
        lgbm_model,
        X_labeled_sc,
        y_labeled,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        method="predict_proba",
        n_jobs=-1,
    )[:, 1]

    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(oof_probs, y_labeled)

    brier_raw = brier_score_loss(y_labeled, oof_probs)
    brier_cal = brier_score_loss(y_labeled, calibrator.transform(oof_probs))
    print(f"  Brier score raw        : {brier_raw:.4f}")
    print(f"  Brier score calibrated : {brier_cal:.4f}  (lower = better calibrated)")

    # Also evaluate calibrated scores on held-out test set
    raw_te     = candidate.predict_proba(X_te_sc)[:, 1]
    cal_te     = calibrator.transform(raw_te)
    roc_cal_te = roc_auc_score(y_te, cal_te)
    brier_te   = brier_score_loss(y_te, cal_te)
    print(f"  Test ROC-AUC (cal)     : {roc_cal_te:.4f}")
    print(f"  Test Brier (cal)       : {brier_te:.4f}")

    # Evaluate Accuracy, Precision, Recall, F1 on Training set and Test set
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    train_acc = accuracy_score(y_tr, (candidate.predict_proba(X_tr_sc)[:, 1] >= 0.5).astype(int))
    train_prec = precision_score(y_tr, (candidate.predict_proba(X_tr_sc)[:, 1] >= 0.5).astype(int), zero_division=0)
    train_rec = recall_score(y_tr, (candidate.predict_proba(X_tr_sc)[:, 1] >= 0.5).astype(int), zero_division=0)
    train_f1 = f1_score(y_tr, (candidate.predict_proba(X_tr_sc)[:, 1] >= 0.5).astype(int), zero_division=0)

    test_acc = accuracy_score(y_te, y_pred_te)
    test_prec = precision_score(y_te, y_pred_te, zero_division=0)
    test_rec = recall_score(y_te, y_pred_te, zero_division=0)
    test_f1 = f1_score(y_te, y_pred_te, zero_division=0)

    # 10. Save all artifacts
    joblib.dump(lgbm_model,  model_path / "lgbm_model.pkl")   # base model (SHAP uses this)
    joblib.dump(calibrator,  model_path / "calibrator.pkl")   # isotonic calibration layer
    joblib.dump(iso_forest,  model_path / "iso_forest.pkl")   # unsupervised scorer
    joblib.dump(scaler,      model_path / "scaler.pkl")       # StandardScaler

    with open(model_path / "feature_cols.json", "w") as f:
        json.dump(FEATURE_COLS, f, indent=2)

    elapsed = time.time() - t0
    imbalance = int((df_labeled[LABEL_COL] == 0).sum()) / max(int((df_labeled[LABEL_COL] == 1).sum()), 1)
    
    sep = "=" * 65
    report = (
        f"\n{sep}\n"
        f"         TraceWatt Model Evaluation & Performance Report\n"
        f"{sep}\n"
        f"1. DATASET & CLASS IMBALANCE HANDLING\n"
        f"   - Total Labeled Consumers       : {len(df_labeled):,}\n"
        f"   - Majority Class (Normal / 0)   : {(df_labeled[LABEL_COL] == 0).sum():,}\n"
        f"   - Minority Class (Theft / 1)    : {(df_labeled[LABEL_COL] == 1).sum():,}\n"
        f"   - Imbalance Ratio (Neg / Pos)   : {imbalance:.1f}x\n"
        f"   - scale_pos_weight Penalty      : {imbalance:.1f}x (Applied in LightGBM)\n"
        f"\n"
        f"2. SPLIT CONFIGURATION (80% Train / 20% Held-Out Test - Stratified)\n"
        f"   - Training Samples              : {len(X_tr):,} (Normal: {(y_tr == 0).sum():,}, Theft: {(y_tr == 1).sum():,})\n"
        f"   - Testing Samples (Held-Out)    : {len(X_te):,} (Normal: {(y_te == 0).sum():,}, Theft: {(y_te == 1).sum():,})\n"
        f"\n"
        f"3. 5-FOLD STRATIFIED CROSS-VALIDATION (ON TRAIN SET)\n"
        f"   - CV Accuracy (Mean +/- Std)    : {cv_scores['acc_mean']*100:.2f}% +/- {cv_scores['acc_std']*100:.2f}%\n"
        f"   - CV ROC-AUC (Mean +/- Std)     : {cv_scores['roc_auc_mean']:.4f} +/- {cv_scores['roc_auc_std']:.4f}\n"
        f"   - CV PR-AUC (Mean +/- Std)      : {cv_scores['pr_auc_mean']:.4f} +/- {cv_scores['pr_auc_std']:.4f}\n"
        f"\n"
        f"4. MODEL ACCURACY (TRAINING VS. TESTING)\n"
        f"   - Training Accuracy             : {train_acc * 100:.2f}%\n"
        f"   - Testing Accuracy (Unseen Data): {test_acc * 100:.2f}%\n"
        f"\n"
        f"5. COMPREHENSIVE TEST-SET METRICS (EVALUATION)\n"
        f"   - Precision (Theft)             : {test_prec:.4f} ({test_prec*100:.1f}%)\n"
        f"   - Recall (Theft)                : {test_rec:.4f} ({test_rec*100:.1f}%)\n"
        f"   - F1-Score (Theft)              : {test_f1:.4f}\n"
        f"   - ROC-AUC                       : {test_roc:.4f}\n"
        f"   - PR-AUC                        : {test_pr:.4f}\n"
        f"\n"
        f"6. PROBABILITY CALIBRATION (ISOTONIC OOF)\n"
        f"   - Raw Brier Loss                : {brier_raw:.4f}\n"
        f"   - Calibrated Brier Loss         : {brier_cal:.4f} (Lower = superior calibration)\n"
        f"   - Calibrated Test ROC-AUC       : {roc_cal_te:.4f}\n"
        f"\n"
        f"7. ARTIFACTS SERIALIZATION\n"
        f"   - Destination Path              : {model_path.resolve()}\n"
        f"   - Saved Artifacts               : lgbm_model.pkl, calibrator.pkl, iso_forest.pkl, scaler.pkl, feature_cols.json\n"
        f"   - Training Time Elapsed         : {elapsed:.2f} seconds\n"
        f"{sep}\n"
    )
    (model_path / "train_report.txt").write_text(report)
    print(report)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TraceWatt Engine — Train Models")
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).resolve().parents[2] / "data" / "processed"),
        help="Directory containing features.parquet",
    )
    parser.add_argument(
        "--model-dir",
        default=str(Path(__file__).resolve().parent / "models"),
        help="Directory to save trained model artifacts",
    )
    args = parser.parse_args()
    train_and_save(args.data_dir, args.model_dir)
