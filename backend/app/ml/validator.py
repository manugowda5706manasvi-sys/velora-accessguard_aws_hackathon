"""
CSV upload validator for AccessGuard AI.

Validates a CSV file (as bytes or a file-like object) for:
- Required columns and correct dtypes
- No negative numeric values
- No duplicate employee_ids
- No empty file, row limit (5000), size limit (1 MB)
- CSV-formula injection neutralisation
- Reports missing numeric values per-row; never silently imputes

Returns a ValidationResult dataclass.
"""

from __future__ import annotations

import io
import hashlib
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_FILE_BYTES = 1_000_000          # 1 MB
MAX_ROWS = 5_000
REQUIRED_COLUMNS = [
    "employee_id",
    "permission_count",
    "sensitive_access_count",
    "inactive_days",
    "off_hours_access_count",
    "failed_logins_7d",
    "role_mismatch",
]
OPTIONAL_COLUMNS = ["employee_name", "role", "department", "app"]
NUMERIC_COLUMNS = [
    "permission_count",
    "sensitive_access_count",
    "inactive_days",
    "off_hours_access_count",
    "failed_logins_7d",
    "role_mismatch",
]
# role_mismatch must be 0 or 1
BINARY_COLUMNS = ["role_mismatch"]

# Characters that trigger formula injection in spreadsheets
_INJECTION_PREFIX = ("=", "+", "-", "@", "\t", "\r")


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    df: pd.DataFrame | None = None          # cleaned DataFrame, only when valid
    row_count: int = 0
    has_role_column: bool = False

    @property
    def is_valid(self) -> bool:
        return self.valid


def _neutralise_injection(val: str) -> str:
    """Prefix dangerous formula starters with a single quote (display-safe)."""
    if isinstance(val, str) and val and val[0] in _INJECTION_PREFIX:
        return "'" + val
    return val


def validate_csv(data: bytes | io.IOBase, filename: str = "upload.csv") -> ValidationResult:
    """
    Validate and clean a CSV upload.

    Args:
        data: Raw bytes or file-like object of the CSV.
        filename: Original filename (used for extension check).

    Returns:
        ValidationResult with .valid, .errors, .warnings, .df (if valid).
    """
    result = ValidationResult(valid=False)

    # ── 1. Extension check ────────────────────────────────────────────────────
    if not filename.lower().endswith(".csv"):
        result.errors.append(
            f"File must be a .csv file. Received: '{filename}'."
        )
        return result

    # ── 2. Read raw bytes ─────────────────────────────────────────────────────
    if isinstance(data, (bytes, bytearray)):
        raw_bytes = bytes(data)
    else:
        raw_bytes = data.read()

    # ── 3. Size check ─────────────────────────────────────────────────────────
    if len(raw_bytes) == 0:
        result.errors.append("The file is empty.")
        return result

    if len(raw_bytes) > MAX_FILE_BYTES:
        mb = len(raw_bytes) / 1_000_000
        result.errors.append(
            f"File size {mb:.2f} MB exceeds the 1 MB limit."
        )
        return result

    # ── 4. Parse CSV ──────────────────────────────────────────────────────────
    try:
        df = pd.read_csv(
            io.BytesIO(raw_bytes),
            dtype=str,           # read everything as string first
            keep_default_na=False,
        )
    except Exception as exc:
        result.errors.append(f"Could not parse CSV: {exc}")
        return result

    if df.empty:
        result.errors.append("The CSV file has no data rows.")
        return result

    # ── 5. Row limit ──────────────────────────────────────────────────────────
    if len(df) > MAX_ROWS:
        result.errors.append(
            f"File has {len(df):,} rows which exceeds the {MAX_ROWS:,}-row limit."
        )
        return result

    # ── 6. Required columns ───────────────────────────────────────────────────
    df.columns = [c.strip().lower() for c in df.columns]
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        result.errors.append(
            f"Missing required columns: {', '.join(missing_cols)}. "
            f"Required: {', '.join(REQUIRED_COLUMNS)}."
        )
        return result

    result.has_role_column = "role" in df.columns

    # ── 7. Strip whitespace from all string cells & neutralise injection ───────
    # Only apply injection neutralisation to non-numeric columns (preserves "-5" as a number)
    string_cols = [c for c in df.columns if c not in NUMERIC_COLUMNS]
    for col in string_cols:
        df[col] = df[col].apply(lambda v: _neutralise_injection(str(v).strip()) if pd.notna(v) else v)
    # Strip whitespace from numeric columns without injection prefix
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: str(v).strip() if pd.notna(v) else v)

    # ── 8. Duplicate employee_id ───────────────────────────────────────────────
    dupes = df[df["employee_id"].duplicated(keep=False)]["employee_id"].unique()
    if len(dupes):
        result.errors.append(
            f"Duplicate employee_id values found: {', '.join(str(d) for d in dupes[:10])}"
            + (" (and more)" if len(dupes) > 10 else "") + "."
        )
        return result

    # ── 9. Missing numeric values — report per row, never impute ─────────────
    missing_reports: list[str] = []
    for col in NUMERIC_COLUMNS:
        blank_mask = df[col].isin(["", "nan", "NaN", "NULL", "null", "NA", "N/A", "n/a"])
        rows = df.index[blank_mask].tolist()
        if rows:
            row_nos = ", ".join(str(r + 2) for r in rows[:10])  # +2 for header + 1-index
            extra = f" and {len(rows)-10} more" if len(rows) > 10 else ""
            missing_reports.append(
                f"Column '{col}' has missing values at row(s): {row_nos}{extra}."
            )
    if missing_reports:
        result.errors.extend(missing_reports)
        return result

    # ── 10. Type coercion and validation ──────────────────────────────────────
    type_errors: list[str] = []
    for col in NUMERIC_COLUMNS:
        coerced = pd.to_numeric(df[col], errors="coerce")
        bad_rows = df.index[coerced.isna()].tolist()
        if bad_rows:
            row_nos = ", ".join(str(r + 2) for r in bad_rows[:10])
            extra = f" and {len(bad_rows)-10} more" if len(bad_rows) > 10 else ""
            type_errors.append(
                f"Column '{col}' has non-numeric values at row(s): {row_nos}{extra}."
            )
        else:
            df[col] = coerced

    if type_errors:
        result.errors.extend(type_errors)
        return result

    # ── 11. Non-negative constraint ───────────────────────────────────────────
    for col in NUMERIC_COLUMNS:
        neg_mask = df[col] < 0
        neg_rows = df.index[neg_mask].tolist()
        if neg_rows:
            row_nos = ", ".join(str(r + 2) for r in neg_rows[:10])
            result.errors.append(
                f"Column '{col}' has negative values at row(s): {row_nos}. "
                "All numeric columns must be ≥ 0."
            )

    if result.errors:
        return result

    # ── 12. Binary constraint for role_mismatch ───────────────────────────────
    bad_binary = df["role_mismatch"][~df["role_mismatch"].isin([0, 1])].index.tolist()
    if bad_binary:
        row_nos = ", ".join(str(r + 2) for r in bad_binary[:10])
        result.errors.append(
            f"Column 'role_mismatch' must be 0 or 1 at row(s): {row_nos}."
        )
        return result

    # ── 13. Cast to correct types ─────────────────────────────────────────────
    for col in NUMERIC_COLUMNS:
        df[col] = df[col].astype(int)

    # ── 14. All good ─────────────────────────────────────────────────────────
    result.valid = True
    result.df = df
    result.row_count = len(df)
    return result
