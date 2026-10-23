"""
Isolation Forest anomaly detection pipeline for AccessGuard AI.

Pipeline:
  1. Select 6 numeric feature columns
  2. Median-impute ONLY columns that had missing values (documented in result)
  3. StandardScaler
  4. IsolationForest(n_estimators=200, contamination=configurable, random_state=42)
  5. Convert decision_function output → 0-100 anomaly score (higher = more unusual)

Anomaly score formula:
    raw  = model.decision_function(X_scaled)   # positive=inlier, negative=outlier
    score = clip((1 - (raw - raw.min()) / (raw.max() - raw.min())) * 100, 0, 100)
    i.e. the most-outlier record gets score ≈ 100, most-inlier gets score ≈ 0.

"Why anomalous": top-3 features by absolute z-score vs population (or role-group) median.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ── Feature columns (the 6 ML features; employee_id is never used as a feature) ──
FEATURE_COLS = [
    "permission_count",
    "sensitive_access_count",
    "inactive_days",
    "off_hours_access_count",
    "failed_logins_7d",
    "role_mismatch",
]

# ── Defaults (overridden by env vars or caller) ────────────────────────────────
DEFAULT_CONTAMINATION = float(os.getenv("IF_CONTAMINATION", "0.08"))
DEFAULT_N_ESTIMATORS  = int(os.getenv("IF_N_ESTIMATORS", "200"))
DEFAULT_RANDOM_STATE  = int(os.getenv("IF_RANDOM_STATE", "42"))


@dataclass
class ScoringResult:
    """Result for a single scored record."""
    employee_id: str
    anomaly_score: float          # 0-100; higher = more unusual
    is_anomaly: bool              # True if IsolationForest flagged as outlier
    raw_if_score: float           # raw decision_function value (for audit)
    top_features: list[dict]      # top-3 features by |z-score| vs population median
    imputed_cols: list[str]       # columns that had missing values and were imputed


@dataclass
class PipelineResult:
    """Returned by run_pipeline()."""
    scores: list[ScoringResult]
    model_params: dict
    feature_cols: list[str]
    n_records: int
    n_anomalies: int
    contamination: float
    imputed_cols: list[str]       # global list of columns that needed imputation


def _compute_zscore_features(
    df: pd.DataFrame,
    feature_cols: list[str],
    has_role: bool,
) -> pd.DataFrame:
    """
    For each row, compute z-scores relative to the population (or per-role group).
    Returns a DataFrame of z-scores with the same index as df.
    """
    z_df = pd.DataFrame(index=df.index, columns=feature_cols, dtype=float)

    if has_role and "role" in df.columns:
        # Per-role z-score
        for col in feature_cols:
            grp = df.groupby("role")[col]
            med = grp.transform("median")
            mad = grp.transform(lambda x: (x - x.median()).abs().median())
            mad = mad.replace(0, 1e-6)  # avoid division by zero
            z_df[col] = (df[col] - med) / (mad * 1.4826)
    else:
        # Population z-score
        for col in feature_cols:
            med = df[col].median()
            mad = (df[col] - med).abs().median()
            if mad == 0:
                mad = 1e-6
            z_df[col] = (df[col] - med) / (mad * 1.4826)

    return z_df.fillna(0.0)


def run_pipeline(
    df: pd.DataFrame,
    contamination: float = DEFAULT_CONTAMINATION,
    n_estimators: int = DEFAULT_N_ESTIMATORS,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> PipelineResult:
    """
    Run the full anomaly-detection pipeline on a validated DataFrame.

    Args:
        df: DataFrame that has passed validate_csv(); must contain FEATURE_COLS.
        contamination: Expected fraction of outliers (default 0.08).
        n_estimators: Number of trees (default 200).
        random_state: For reproducibility (default 42).

    Returns:
        PipelineResult with per-record ScoringResult objects.

    Raises:
        ValueError: If required feature columns are missing or df is empty.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    df = df.reset_index(drop=True).copy()

    # ── 1. Median-impute missing values (documented) ───────────────────────────
    imputed_cols: list[str] = []
    for col in FEATURE_COLS:
        null_mask = df[col].isna()
        if null_mask.any():
            median_val = df[col].median()
            df.loc[null_mask, col] = median_val
            imputed_cols.append(col)

    X = df[FEATURE_COLS].values.astype(float)

    # ── 2. Standard scale ─────────────────────────────────────────────────────
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ── 3. Isolation Forest ───────────────────────────────────────────────────
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    predictions = model.predict(X_scaled)         # 1 = inlier, -1 = outlier
    raw_scores  = model.decision_function(X_scaled)  # positive = inlier

    # ── 4. Normalize to 0-100 (higher = more anomalous) ──────────────────────
    s_min, s_max = raw_scores.min(), raw_scores.max()
    if s_max == s_min:
        norm_scores = np.zeros(len(raw_scores))
    else:
        norm_scores = (1.0 - (raw_scores - s_min) / (s_max - s_min)) * 100.0
    norm_scores = np.clip(norm_scores, 0.0, 100.0)

    # ── 5. Z-scores for explanation ───────────────────────────────────────────
    has_role = "role" in df.columns
    z_df = _compute_zscore_features(df, FEATURE_COLS, has_role)

    # ── 6. Build per-record results ───────────────────────────────────────────
    scores: list[ScoringResult] = []
    for i in range(len(df)):
        emp_id = str(df.at[i, "employee_id"]) if "employee_id" in df.columns else str(i)
        is_anomaly = bool(predictions[i] == -1)

        # Top-3 features by absolute z-score
        row_z = z_df.iloc[i]
        top3 = (
            row_z.abs()
            .sort_values(ascending=False)
            .head(3)
        )
        top_features = [
            {
                "feature": feat,
                "value": float(df.at[i, feat]),
                "z_score": float(row_z[feat]),
                "direction": "above" if row_z[feat] > 0 else "below",
            }
            for feat in top3.index
        ]

        scores.append(
            ScoringResult(
                employee_id=emp_id,
                anomaly_score=float(round(norm_scores[i], 2)),
                is_anomaly=is_anomaly,
                raw_if_score=float(round(raw_scores[i], 6)),
                top_features=top_features,
                imputed_cols=imputed_cols,
            )
        )

    n_anomalies = int(np.sum(predictions == -1))

    return PipelineResult(
        scores=scores,
        model_params={
            "algorithm": "IsolationForest",
            "n_estimators": n_estimators,
            "contamination": contamination,
            "random_state": random_state,
            "scaler": "StandardScaler",
            "score_formula": "score = clip((1 - (raw - raw.min()) / (raw.max() - raw.min())) * 100, 0, 100)",
        },
        feature_cols=FEATURE_COLS,
        n_records=len(df),
        n_anomalies=n_anomalies,
        contamination=contamination,
        imputed_cols=imputed_cols,
    )
