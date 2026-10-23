"""Tests for the synthetic data generator (Stage 2)."""
import pathlib
import pandas as pd
import pytest

# Make scripts importable
import sys
# project root / scripts
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
from generate_data import generate, ROLE_BASELINES

REQUIRED_COLUMNS_CHECK = [
    "employee_id", "employee_name", "role", "department", "app",
    "permission_count", "sensitive_access_count", "inactive_days",
    "off_hours_access_count", "failed_logins_7d", "role_mismatch",
    "is_injected_risk", "risk_label",
]


class TestGeneratorBasics:
    def setup_method(self):
        self.df = generate(seed=42)

    def test_row_count(self):
        assert len(self.df) == 250, f"Expected 250 rows, got {len(self.df)}"

    def test_required_columns_present(self):
        for col in REQUIRED_COLUMNS_CHECK:
            assert col in self.df.columns, f"Missing column: {col}"

    def test_no_null_in_required_columns(self):
        required = [
            "employee_id", "permission_count", "sensitive_access_count",
            "inactive_days", "off_hours_access_count", "failed_logins_7d", "role_mismatch"
        ]
        for col in required:
            assert self.df[col].isna().sum() == 0, f"Nulls in {col}"

    def test_unique_employee_ids(self):
        assert self.df["employee_id"].nunique() == len(self.df), "Duplicate employee_ids"

    def test_non_negative_numerics(self):
        for col in ["permission_count", "sensitive_access_count", "inactive_days",
                    "off_hours_access_count", "failed_logins_7d"]:
            assert (self.df[col] >= 0).all(), f"Negative values in {col}"

    def test_role_mismatch_binary(self):
        assert set(self.df["role_mismatch"].unique()).issubset({0, 1}), \
            "role_mismatch must be 0 or 1"

    def test_risk_label_values(self):
        valid_labels = {"Low", "Medium", "High"}
        actual = set(self.df["risk_label"].unique())
        assert actual.issubset(valid_labels), f"Invalid risk labels: {actual - valid_labels}"

    def test_apps_limited_to_five(self):
        valid_apps = {"GitHub", "Google Workspace", "AWS Console", "Slack", "Jira"}
        actual = set(self.df["app"].unique())
        assert actual.issubset(valid_apps), f"Unknown apps: {actual - valid_apps}"

    def test_risky_rate_in_range(self):
        rate = self.df["is_injected_risk"].mean()
        assert 0.07 <= rate <= 0.14, f"Risky injection rate {rate:.2%} outside 7-14%"


class TestReproducibility:
    def test_same_seed_same_data(self):
        df1 = generate(seed=42)
        df2 = generate(seed=42)
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seed_different_data(self):
        df1 = generate(seed=42)
        df2 = generate(seed=99)
        # At least some rows should differ
        assert not df1["permission_count"].equals(df2["permission_count"])


class TestShowcaseEmployees:
    def setup_method(self):
        self.df = generate(seed=42)

    def _get(self, emp_id: str) -> pd.Series:
        row = self.df[self.df["employee_id"] == emp_id]
        assert len(row) == 1, f"Showcase employee {emp_id} not found"
        return row.iloc[0]

    def test_showcase_high_001_role_mismatch(self):
        row = self._get("showcase_high_001")
        assert row["role_mismatch"] == 1
        assert row["risk_label"] == "High"
        assert row["is_injected_risk"]

    def test_showcase_high_002_intern_overpermissioned(self):
        row = self._get("showcase_high_002")
        assert row["role"] == "intern"
        assert row["permission_count"] > ROLE_BASELINES["intern"] * 3
        assert row["risk_label"] == "High"

    def test_showcase_med_001_stale_access(self):
        row = self._get("showcase_med_001")
        assert row["inactive_days"] >= 90
        assert row["risk_label"] == "Medium"

    def test_showcase_med_002_off_hours(self):
        row = self._get("showcase_med_002")
        assert row["off_hours_access_count"] >= 30
        assert row["risk_label"] == "Medium"

    def test_showcase_low_001_normal(self):
        row = self._get("showcase_low_001")
        assert not row["is_injected_risk"]
        assert row["risk_label"] == "Low"

    def test_showcase_low_002_normal(self):
        row = self._get("showcase_low_002")
        assert not row["is_injected_risk"]
        assert row["risk_label"] == "Low"


class TestCSVOutput:
    def test_csv_written_and_loadable(self, tmp_path):
        df = generate(seed=42)
        out = tmp_path / "test.csv"
        df.to_csv(out, index=False)
        df2 = pd.read_csv(out)
        assert len(df2) == len(df)
        assert list(df2.columns) == list(df.columns)
