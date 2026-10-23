"""Tests for the IsolationForest anomaly detection pipeline (Stage 3)."""
import pathlib
import sys
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from backend.app.ml.anomaly import run_pipeline, FEATURE_COLS, ScoringResult, PipelineResult

# ── Helper: build a minimal valid DataFrame ───────────────────────────────────
def make_df(n: int = 50, seed: int = 42, inject_anomalies: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "employee_id": [f"emp_{i:04d}" for i in range(n)],
        "permission_count": rng.integers(5, 20, size=n),
        "sensitive_access_count": rng.integers(0, 6, size=n),
        "inactive_days": rng.integers(0, 30, size=n),
        "off_hours_access_count": rng.integers(0, 10, size=n),
        "failed_logins_7d": rng.integers(0, 3, size=n),
        "role_mismatch": rng.integers(0, 2, size=n),
    })
    if inject_anomalies:
        # Inject 5 obvious anomalies at the end
        for i in range(5):
            idx = n - 5 + i
            df.at[idx, "permission_count"] = 200
            df.at[idx, "sensitive_access_count"] = 100
            df.at[idx, "failed_logins_7d"] = 50
            df.at[idx, "off_hours_access_count"] = 100
    return df


# ── Basic output shape ────────────────────────────────────────────────────────
class TestBasicOutput:
    def setup_method(self):
        self.df = make_df(60)
        self.result = run_pipeline(self.df)

    def test_returns_pipeline_result(self):
        assert isinstance(self.result, PipelineResult)

    def test_score_count_matches_rows(self):
        assert len(self.result.scores) == len(self.df)

    def test_all_employee_ids_present(self):
        result_ids = {s.employee_id for s in self.result.scores}
        expected_ids = set(self.df["employee_id"])
        assert result_ids == expected_ids

    def test_scores_in_range(self):
        for s in self.result.scores:
            assert 0.0 <= s.anomaly_score <= 100.0, \
                f"Score {s.anomaly_score} out of range for {s.employee_id}"

    def test_anomaly_flag_is_bool(self):
        for s in self.result.scores:
            assert isinstance(s.is_anomaly, bool)

    def test_top_features_count(self):
        for s in self.result.scores:
            assert len(s.top_features) == 3, \
                f"Expected 3 top features, got {len(s.top_features)}"

    def test_top_features_valid_names(self):
        for s in self.result.scores:
            for f in s.top_features:
                assert f["feature"] in FEATURE_COLS

    def test_model_params_present(self):
        p = self.result.model_params
        assert "algorithm" in p
        assert "n_estimators" in p
        assert "contamination" in p
        assert "score_formula" in p


# ── Reproducibility ───────────────────────────────────────────────────────────
class TestReproducibility:
    def test_same_data_same_scores(self):
        df = make_df(60, seed=42)
        r1 = run_pipeline(df, random_state=42)
        r2 = run_pipeline(df, random_state=42)
        scores1 = [s.anomaly_score for s in r1.scores]
        scores2 = [s.anomaly_score for s in r2.scores]
        assert scores1 == scores2

    def test_different_seed_different_scores(self):
        df = make_df(60, seed=42)
        r1 = run_pipeline(df, random_state=42)
        r2 = run_pipeline(df, random_state=99)
        scores1 = [s.anomaly_score for s in r1.scores]
        scores2 = [s.anomaly_score for s in r2.scores]
        assert scores1 != scores2


# ── Anomalies detected ────────────────────────────────────────────────────────
class TestAnomalyDetection:
    def test_injected_anomalies_mostly_flagged(self):
        n = 55
        df = make_df(n, inject_anomalies=True)
        result = run_pipeline(df, contamination=0.08)
        # The 5 injected anomalies are at indices n-5 to n-1
        injected_ids = {f"emp_{i:04d}" for i in range(n - 5, n)}
        flagged = {s.employee_id for s in result.scores if s.is_anomaly}
        detected = injected_ids & flagged
        # Expect at least 3 of 5 detected (60% recall on strong anomalies)
        assert len(detected) >= 3, \
            f"Only detected {len(detected)}/5 injected anomalies"

    def test_anomalies_have_higher_scores_than_normals(self):
        n = 55
        df = make_df(n, inject_anomalies=True)
        result = run_pipeline(df)
        injected_ids = {f"emp_{i:04d}" for i in range(n - 5, n)}
        injected_scores = [s.anomaly_score for s in result.scores
                           if s.employee_id in injected_ids]
        normal_scores = [s.anomaly_score for s in result.scores
                         if s.employee_id not in injected_ids]
        assert np.mean(injected_scores) > np.mean(normal_scores), \
            "Injected anomalies should have higher average score than normals"

    def test_n_anomalies_matches_contamination(self):
        df = make_df(100)
        result = run_pipeline(df, contamination=0.10)
        # With contamination=0.10 on 100 rows, expect exactly 10 anomalies
        assert result.n_anomalies == 10


# ── Bad input ─────────────────────────────────────────────────────────────────
class TestBadInput:
    def test_empty_df_raises(self):
        with pytest.raises(ValueError, match="empty"):
            run_pipeline(pd.DataFrame())

    def test_missing_feature_col_raises(self):
        df = make_df(20).drop(columns=["permission_count"])
        with pytest.raises(ValueError, match="Missing feature columns"):
            run_pipeline(df)


# ── Imputation documented ─────────────────────────────────────────────────────
class TestImputation:
    def test_imputed_cols_reported(self):
        df = make_df(30)
        df.loc[0, "failed_logins_7d"] = None  # introduce one missing
        result = run_pipeline(df)
        assert "failed_logins_7d" in result.imputed_cols

    def test_no_imputed_cols_when_no_missing(self):
        df = make_df(30)
        result = run_pipeline(df)
        assert result.imputed_cols == []
