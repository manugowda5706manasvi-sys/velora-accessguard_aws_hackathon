"""Tests for the CSV upload validator (Stage 2)."""
import io
import textwrap
import pytest
import pandas as pd

from backend.app.ml.validator import validate_csv, REQUIRED_COLUMNS, MAX_FILE_BYTES, MAX_ROWS

# ── Helpers ───────────────────────────────────────────────────────────────────
GOOD_HEADER = "employee_id,permission_count,sensitive_access_count,inactive_days,off_hours_access_count,failed_logins_7d,role_mismatch"
GOOD_ROW    = "emp_001,12,3,10,2,0,0"
GOOD_CSV    = f"{GOOD_HEADER}\n{GOOD_ROW}\n"


def make_bytes(text: str) -> bytes:
    return text.encode("utf-8")


# ── Happy path ────────────────────────────────────────────────────────────────
class TestHappyPath:
    def test_minimal_valid_csv(self):
        r = validate_csv(make_bytes(GOOD_CSV))
        assert r.valid
        assert r.row_count == 1
        assert r.errors == []

    def test_optional_columns_allowed(self):
        csv = f"{GOOD_HEADER},employee_name,role,department,app\n"
        csv += f"{GOOD_ROW},Alice,engineer,Engineering,GitHub\n"
        r = validate_csv(make_bytes(csv))
        assert r.valid

    def test_has_role_column_flag(self):
        csv = f"{GOOD_HEADER},role\n{GOOD_ROW},engineer\n"
        r = validate_csv(make_bytes(csv))
        assert r.has_role_column is True

    def test_no_role_column_flag(self):
        r = validate_csv(make_bytes(GOOD_CSV))
        assert r.has_role_column is False

    def test_df_returned_on_success(self):
        r = validate_csv(make_bytes(GOOD_CSV))
        assert r.df is not None
        assert "employee_id" in r.df.columns


# ── File-level checks ─────────────────────────────────────────────────────────
class TestFileLevelChecks:
    def test_empty_file_rejected(self):
        r = validate_csv(b"")
        assert not r.valid
        assert any("empty" in e.lower() for e in r.errors)

    def test_oversized_file_rejected(self):
        big = b"x" * (MAX_FILE_BYTES + 1)
        r = validate_csv(big)
        assert not r.valid
        assert any("1 MB" in e for e in r.errors)

    def test_non_csv_extension_rejected(self):
        r = validate_csv(make_bytes(GOOD_CSV), filename="data.xlsx")
        assert not r.valid
        assert any(".csv" in e for e in r.errors)

    def test_too_many_rows_rejected(self):
        rows = [GOOD_HEADER] + [f"emp_{i},{i},0,0,0,0,0" for i in range(MAX_ROWS + 1)]
        r = validate_csv(make_bytes("\n".join(rows)))
        assert not r.valid
        assert any("5,000" in e or "5000" in e for e in r.errors)


# ── Column checks ─────────────────────────────────────────────────────────────
class TestColumnChecks:
    def test_missing_required_column(self):
        csv = "employee_id,permission_count\nemp_001,12\n"
        r = validate_csv(make_bytes(csv))
        assert not r.valid
        assert any("Missing required" in e for e in r.errors)

    def test_duplicate_employee_ids_rejected(self):
        csv = f"{GOOD_HEADER}\n{GOOD_ROW}\n{GOOD_ROW}\n"
        r = validate_csv(make_bytes(csv))
        assert not r.valid
        assert any("Duplicate" in e for e in r.errors)


# ── Type and value checks ─────────────────────────────────────────────────────
class TestTypeAndValueChecks:
    def test_non_numeric_value_rejected(self):
        csv = f"{GOOD_HEADER}\nemp_001,abc,3,10,2,0,0\n"
        r = validate_csv(make_bytes(csv))
        assert not r.valid
        assert any("non-numeric" in e for e in r.errors)

    def test_negative_value_rejected(self):
        csv = f"{GOOD_HEADER}\nemp_001,-5,3,10,2,0,0\n"
        r = validate_csv(make_bytes(csv))
        assert not r.valid
        assert any("negative" in e.lower() for e in r.errors)

    def test_missing_numeric_value_reported_per_row(self):
        csv = f"{GOOD_HEADER}\nemp_001,,3,10,2,0,0\n"
        r = validate_csv(make_bytes(csv))
        assert not r.valid
        assert any("permission_count" in e and "row" in e for e in r.errors)

    def test_role_mismatch_must_be_binary(self):
        csv = f"{GOOD_HEADER}\nemp_001,12,3,10,2,0,5\n"
        r = validate_csv(make_bytes(csv))
        assert not r.valid
        assert any("role_mismatch" in e for e in r.errors)


# ── Injection neutralisation ──────────────────────────────────────────────────
class TestInjectionNeutralisation:
    def test_formula_prefix_neutralised(self):
        # employee_name with formula prefix (optional column)
        csv = f"{GOOD_HEADER},employee_name\n{GOOD_ROW},=SUM(1)\n"
        r = validate_csv(make_bytes(csv))
        assert r.valid
        # The injected cell should be prefixed with '
        assert r.df["employee_name"].iloc[0].startswith("'")

    def test_plus_prefix_neutralised(self):
        csv = f"{GOOD_HEADER},employee_name\n{GOOD_ROW},+CMD\n"
        r = validate_csv(make_bytes(csv))
        assert r.valid
        assert r.df["employee_name"].iloc[0].startswith("'")

    def test_normal_name_unchanged(self):
        csv = f"{GOOD_HEADER},employee_name\n{GOOD_ROW},Alice\n"
        r = validate_csv(make_bytes(csv))
        assert r.valid
        assert r.df["employee_name"].iloc[0] == "Alice"


# ── File-like object support ──────────────────────────────────────────────────
class TestFilelikeInput:
    def test_filelike_accepted(self):
        buf = io.BytesIO(make_bytes(GOOD_CSV))
        r = validate_csv(buf)
        assert r.valid
