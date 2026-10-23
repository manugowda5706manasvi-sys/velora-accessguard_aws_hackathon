"""
Pydantic schemas for AccessGuard AI API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Analysis ──────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    run_id: Optional[str] = None   # use existing run; if None, run on sample data


class FeatureContribution(BaseModel):
    feature: str
    value: float
    z_score: float
    direction: str   # "above" | "below"


class RuleHitSchema(BaseModel):
    rule_id: str
    description: str
    severity: str
    details: str


class RecordOut(BaseModel):
    employee_id: str
    employee_name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    app: Optional[str] = None
    permission_count: int
    sensitive_access_count: int
    inactive_days: int
    off_hours_access_count: int
    failed_logins_7d: int
    role_mismatch: int
    anomaly_score: float
    is_anomaly: bool
    raw_if_score: float
    risk_level: str
    explanation: str
    recommendation: str
    rule_hits: list[dict]
    top_features: list[dict]
    permission_drift: Optional[float] = None
    role_baseline: Optional[int] = None
    review_status: str = "Pending Review"
    review_comment: Optional[str] = None
    review_outcome: Optional[str] = None
    review_actor: Optional[str] = None
    review_at: Optional[str] = None


class PagedRecords(BaseModel):
    items: list[RecordOut]
    total: int
    page: int
    page_size: int


class AnalysisRunOut(BaseModel):
    run_id: str
    created_at: str
    record_count: int
    anomaly_count: int
    high_risk_count: int
    has_role_column: bool
    model_params: dict


# ── Review ────────────────────────────────────────────────────────────────────

class ReviewUpdate(BaseModel):
    status: str          # "Investigating" | "Resolved"
    comment: str         # Required
    outcome: Optional[str] = None   # "Accepted risk" | "Access reduced (manual action recorded)"

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"Investigating", "Resolved"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v

    @field_validator("comment")
    @classmethod
    def non_empty_comment(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("comment must not be empty")
        return v.strip()

    @field_validator("outcome")
    @classmethod
    def valid_outcome(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"Accepted risk", "Access reduced (manual action recorded)"}
        if v not in allowed:
            raise ValueError(f"outcome must be one of {allowed}")
        return v


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditEntryOut(BaseModel):
    entry_id: str
    timestamp: str
    actor: str
    action: str
    details: dict
    prev_hash: str
    hash: str
    seq: int


class AuditVerifyOut(BaseModel):
    valid: bool
    first_bad_seq: Optional[int] = None
    total_entries: int


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    run_id: str
    total_records: int
    anomaly_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    pending_review_count: int
    investigating_count: int
    resolved_count: int
    has_role_column: bool
    risk_by_app: list[dict]
    score_distribution: list[dict]
    top_rule_reasons: list[dict]
    alerts: list[dict]   # newest High/Medium records


# ── System status ─────────────────────────────────────────────────────────────

class SystemStatus(BaseModel):
    status: str          # "ok"
    storage_backend: str
    model_params: dict
    dataset_info: dict
    version: str = "1.0.0"
