"""
FastAPI route handlers for AccessGuard AI.
Implements all required endpoints with auth, validation, ML pipeline, rules, storage, and audit logging.
"""

from __future__ import annotations

import csv
import io
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from backend.app.api.auth import (
    check_rate_limit,
    create_access_token,
    get_current_admin,
    verify_password,
    verify_username,
)
from backend.app.config import get_settings
from backend.app.ml.anomaly import run_pipeline
from backend.app.ml.validator import validate_csv
from backend.app.rules.engine import evaluate_all
from backend.app.schemas.models import (
    AuditEntryOut,
    AuditVerifyOut,
    DashboardStats,
    LoginRequest,
    PagedRecords,
    RecordOut,
    ReviewUpdate,
    SystemStatus,
    TokenResponse,
)
from backend.app.storage.base import get_storage

router = APIRouter()


# ── Public Health Check ────────────────────────────────────────────────────────

@router.get("/health", tags=["System"])
def health_check():
    """Unauthenticated health probe for load balancers and monitoring."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "AccessGuard AI",
        "version": "1.0.0",
    }


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(req: LoginRequest, request: Request):
    """
    Authenticate demo admin.
    Protected with constant-time password check and IP rate-limiting.
    """
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    settings = get_settings()
    is_user_valid = verify_username(req.username, settings.admin_username)
    is_pass_valid = verify_password(req.password, settings.admin_password)

    if not (is_user_valid and is_pass_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": req.username})
    return TokenResponse(access_token=token, token_type="bearer")


# ── Helper: Run Analysis on a DataFrame ────────────────────────────────────────

def _process_and_store_df(df: pd.DataFrame, source_label: str, storage, actor: str) -> str:
    """Run Isolation Forest and Rules Engine, persist to storage, and log audit."""
    has_role = "role" in df.columns

    # 1. Real ML: Isolation Forest pipeline
    ml_result = run_pipeline(df)
    score_map = {res.employee_id: res.anomaly_score for res in ml_result.scores}
    flag_map = {res.employee_id: res.is_anomaly for res in ml_result.scores}
    raw_if_map = {res.employee_id: res.raw_if_score for res in ml_result.scores}
    top_feat_map = {res.employee_id: res.top_features for res in ml_result.scores}

    # 2. Transparent Rules + Role-Permission Baselines
    rule_results = evaluate_all(
        df=df,
        anomaly_scores=score_map,
        anomaly_flags=flag_map,
        has_role=has_role,
    )
    rule_map = {r.employee_id: r for r in rule_results}

    # 3. Assemble unified records
    records_to_save = []
    high_count = 0
    anomaly_count = sum(1 for f in flag_map.values() if f)

    for _, row in df.iterrows():
        emp_id = str(row["employee_id"])
        r_res = rule_map[emp_id]
        if r_res.risk_level == "High":
            high_count += 1

        rec = {
            "employee_id": emp_id,
            "employee_name": str(row["employee_name"]) if "employee_name" in row and pd.notna(row["employee_name"]) else None,
            "role": str(row["role"]) if "role" in row and pd.notna(row["role"]) else None,
            "department": str(row["department"]) if "department" in row and pd.notna(row["department"]) else None,
            "app": str(row["app"]) if "app" in row and pd.notna(row["app"]) else None,
            "permission_count": int(row["permission_count"]),
            "sensitive_access_count": int(row["sensitive_access_count"]),
            "inactive_days": int(row["inactive_days"]),
            "off_hours_access_count": int(row["off_hours_access_count"]),
            "failed_logins_7d": int(row["failed_logins_7d"]),
            "role_mismatch": int(row["role_mismatch"]),
            "anomaly_score": round(score_map[emp_id], 2),
            "is_anomaly": flag_map[emp_id],
            "raw_if_score": round(raw_if_map[emp_id], 4),
            "risk_level": r_res.risk_level,
            "explanation": r_res.explanation,
            "recommendation": r_res.recommendation,
            "rule_hits": [
                {
                    "rule_id": h.rule_id,
                    "description": h.description,
                    "severity": h.severity,
                    "details": h.details,
                }
                for h in r_res.rule_hits
            ],
            "top_features": top_feat_map.get(emp_id, []),
            "permission_drift": round(r_res.permission_drift, 2) if r_res.permission_drift is not None else None,
            "role_baseline": r_res.role_baseline,
        }
        records_to_save.append(rec)

    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    run_data = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records_to_save),
        "anomaly_count": anomaly_count,
        "high_risk_count": high_count,
        "metadata": {
            "source": source_label,
            "has_role_column": has_role,
            "model": "IsolationForest",
            "imputed_columns": ml_result.imputed_cols,
        },
        "records": records_to_save,
    }

    storage.save_analysis_run(run_data)

    storage.append_audit_entry({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": "ANALYSIS_RUN_COMPLETED",
        "details": {
            "run_id": run_id,
            "source": source_label,
            "total_records": len(records_to_save),
            "anomalies_flagged": anomaly_count,
            "high_risk_count": high_count,
            "has_role_column": has_role,
        },
    })

    return run_id


# ── Upload & Analyse ──────────────────────────────────────────────────────────

@router.post("/upload", tags=["Analysis"])
async def upload_csv(
    file: UploadFile = File(...),
    admin: str = Depends(get_current_admin),
):
    """
    Upload and validate a SaaS access CSV.
    Strictly validates column types, bounds, formula injection, and schema.
    If valid, automatically trains Isolation Forest and executes transparent risk rules.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a .csv extension",
        )

    content = await file.read()
    if len(content) > 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 1 MB limit",
        )

    val_res = validate_csv(content, filename=file.filename)
    if not val_res.is_valid:
        return {
            "success": False,
            "filename": file.filename,
            "errors": val_res.errors,
            "warnings": val_res.warnings,
            "row_count": val_res.row_count,
        }

    storage = get_storage()
    run_id = _process_and_store_df(val_res.df, source_label=f"upload:{file.filename}", storage=storage, actor=admin)

    return {
        "success": True,
        "filename": file.filename,
        "run_id": run_id,
        "records_processed": val_res.row_count,
        "warnings": val_res.warnings,
        "message": f"Successfully analysed {val_res.row_count} records",
    }


@router.post("/analyse", tags=["Analysis"])
def trigger_analysis(
    admin: str = Depends(get_current_admin),
):
    """
    Run or re-run analysis using the sample access dataset.
    """
    sample_path = "./data/sample_access.csv"
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample dataset data/sample_access.csv not found")

    with open(sample_path, "rb") as f:
        content = f.read()

    val_res = validate_csv(content, filename="sample_access.csv")
    if not val_res.is_valid:
        raise HTTPException(status_code=400, detail=f"Sample CSV invalid: {val_res.errors}")

    storage = get_storage()
    run_id = _process_and_store_df(val_res.df, source_label="sample_data", storage=storage, actor=admin)
    return {"success": True, "run_id": run_id, "records_processed": val_res.row_count}


# ── Records & Details ─────────────────────────────────────────────────────────

@router.get("/records", response_model=PagedRecords, tags=["Records"])
def get_records(
    run_id: Optional[str] = Query(None, description="Run ID; defaults to most recent"),
    risk_level: Optional[str] = Query(None, description="Filter by risk: High, Medium, Low"),
    app: Optional[str] = Query(None, description="Filter by SaaS application"),
    review_status: Optional[str] = Query(None, description="Filter by review status"),
    is_anomaly: Optional[bool] = Query(None, description="Filter by anomaly flag"),
    search: Optional[str] = Query(None, description="Search employee_id, employee_name, role"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("anomaly_score", description="Sort column"),
    sort_desc: bool = Query(True, description="Sort descending"),
    admin: str = Depends(get_current_admin),
):
    """Retrieve paginated and filtered records for an analysis run."""
    storage = get_storage()
    active_run_id = run_id or storage.get_latest_run_id()
    if not active_run_id:
        return PagedRecords(items=[], total=0, page=page, page_size=page_size)

    result = storage.get_records(
        run_id=active_run_id,
        risk_level=risk_level,
        app=app,
        review_status=review_status,
        is_anomaly=is_anomaly,
        search=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    return PagedRecords(**result)


@router.get("/records/{employee_id}", response_model=RecordOut, tags=["Records"])
def get_record(
    employee_id: str,
    run_id: Optional[str] = Query(None, description="Run ID; defaults to most recent"),
    admin: str = Depends(get_current_admin),
):
    """Retrieve detailed analysis and explainability evidence for a single employee."""
    storage = get_storage()
    active_run_id = run_id or storage.get_latest_run_id()
    if not active_run_id:
        raise HTTPException(status_code=404, detail="No analysis runs found")

    rec = storage.get_record(run_id=active_run_id, employee_id=employee_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found in run {active_run_id}")
    return RecordOut(**rec)


# ── Review Workflow ───────────────────────────────────────────────────────────

@router.patch("/records/{employee_id}/review", tags=["Review Workflow"])
def update_review(
    employee_id: str,
    update: ReviewUpdate,
    run_id: Optional[str] = Query(None),
    admin: str = Depends(get_current_admin),
):
    """
    Record an administrative review decision.
    Decision-support only: strictly records decisions ("recommended / recorded"), never revokes.
    Appends tamper-evident audit record with SHA-256 hash chaining.
    """
    storage = get_storage()
    active_run_id = run_id or storage.get_latest_run_id()
    if not active_run_id:
        raise HTTPException(status_code=404, detail="No active analysis run found")

    rec = storage.get_record(run_id=active_run_id, employee_id=employee_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")

    storage.update_review_status(
        run_id=active_run_id,
        employee_id=employee_id,
        status=update.status,
        comment=update.comment,
        outcome=update.outcome,
        actor=admin,
    )

    storage.append_audit_entry({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": admin,
        "action": "REVIEW_DECISION_RECORDED",
        "details": {
            "run_id": active_run_id,
            "employee_id": employee_id,
            "employee_name": rec.get("employee_name"),
            "previous_status": rec.get("review_status"),
            "new_status": update.status,
            "comment": update.comment,
            "outcome": update.outcome,
            "disclaimer": "Administrative decision recorded; real SaaS permissions were not modified.",
        },
    })

    updated_rec = storage.get_record(run_id=active_run_id, employee_id=employee_id)
    return {"success": True, "record": updated_rec}


# ── Dashboard Stats & Alerts ──────────────────────────────────────────────────

@router.get("/stats", response_model=DashboardStats, tags=["Dashboard"])
def get_dashboard_stats(
    run_id: Optional[str] = Query(None),
    admin: str = Depends(get_current_admin),
):
    """
    Provide aggregated statistics, distributions, and alerts for the security dashboard.
    """
    storage = get_storage()
    active_run_id = run_id or storage.get_latest_run_id()

    # If no run exists, trigger sample data run automatically so dashboard is immediately useful
    if not active_run_id:
        sample_path = "./data/sample_access.csv"
        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                val = validate_csv(f.read(), "sample_access.csv")
                if val.is_valid:
                    active_run_id = _process_and_store_df(val.df, "sample_data_auto", storage, admin)

    if not active_run_id:
        return DashboardStats(
            run_id="none",
            total_records=0,
            anomaly_count=0,
            high_risk_count=0,
            medium_risk_count=0,
            low_risk_count=0,
            pending_review_count=0,
            investigating_count=0,
            resolved_count=0,
            has_role_column=False,
            risk_by_app=[],
            score_distribution=[],
            top_rule_reasons=[],
            alerts=[],
        )

    # Fetch all records for aggregation in memory (typically 250 - 5000 rows max)
    all_res = storage.get_records(run_id=active_run_id, page=1, page_size=5000)
    items = all_res["items"]

    total_records = len(items)
    anomaly_count = sum(1 for r in items if r["is_anomaly"])
    high_count = sum(1 for r in items if r["risk_level"] == "High")
    med_count = sum(1 for r in items if r["risk_level"] == "Medium")
    low_count = sum(1 for r in items if r["risk_level"] == "Low")

    pending_count = sum(1 for r in items if r["review_status"] == "Pending Review")
    investigating_count = sum(1 for r in items if r["review_status"] == "Investigating")
    resolved_count = sum(1 for r in items if r["review_status"] == "Resolved")

    has_role = any(r.get("role") for r in items)

    # Risk by App
    app_map: dict[str, dict[str, int]] = {}
    for r in items:
        app_name = r.get("app") or "Unknown"
        if app_name not in app_map:
            app_map[app_name] = {"app": app_name, "High": 0, "Medium": 0, "Low": 0}
        risk = r.get("risk_level", "Low")
        if risk in app_map[app_name]:
            app_map[app_name][risk] += 1
    risk_by_app = list(app_map.values())

    # Anomaly Score Distribution (bins 0-20, 20-40, 40-60, 60-80, 80-100)
    bins = [
        {"range": "0-20", "count": 0},
        {"range": "20-40", "count": 0},
        {"range": "40-60", "count": 0},
        {"range": "60-80", "count": 0},
        {"range": "80-100", "count": 0},
    ]
    for r in items:
        score = r.get("anomaly_score", 0.0)
        if score < 20:
            bins[0]["count"] += 1
        elif score < 40:
            bins[1]["count"] += 1
        elif score < 60:
            bins[2]["count"] += 1
        elif score < 80:
            bins[3]["count"] += 1
        else:
            bins[4]["count"] += 1

    # Top rule reasons
    reason_counts: dict[str, int] = {}
    for r in items:
        for hit in r.get("rule_hits", []):
            rule_id = hit.get("rule_id", "unknown")
            reason_counts[rule_id] = reason_counts.get(rule_id, 0) + 1

    top_rule_reasons = [
        {"rule": k, "count": v}
        for k, v in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # In-app Alerts Feed: newest High and Medium records requiring human attention
    alerts = [
        {
            "employee_id": r["employee_id"],
            "employee_name": r.get("employee_name"),
            "risk_level": r["risk_level"],
            "anomaly_score": r["anomaly_score"],
            "app": r.get("app"),
            "role": r.get("role"),
            "explanation": r["explanation"],
            "review_status": r["review_status"],
        }
        for r in sorted(
            [rec for rec in items if rec["risk_level"] in ("High", "Medium")],
            key=lambda x: (0 if x["risk_level"] == "High" else 1, -x["anomaly_score"]),
        )[:10]
    ]

    return DashboardStats(
        run_id=active_run_id,
        total_records=total_records,
        anomaly_count=anomaly_count,
        high_risk_count=high_count,
        medium_risk_count=med_count,
        low_risk_count=low_count,
        pending_review_count=pending_count,
        investigating_count=investigating_count,
        resolved_count=resolved_count,
        has_role_column=has_role,
        risk_by_app=risk_by_app,
        score_distribution=bins,
        top_rule_reasons=top_rule_reasons,
        alerts=alerts,
    )


# ── Audit Trail & Tamper Verification ─────────────────────────────────────────

@router.get("/audit", response_model=list[AuditEntryOut], tags=["Audit Log"])
def get_audit_trail(
    limit: int = Query(200, ge=1, le=1000),
    admin: str = Depends(get_current_admin),
):
    """Retrieve append-only audit trail logs with SHA-256 hash chains."""
    storage = get_storage()
    entries = storage.get_audit_log(limit=limit)
    return [AuditEntryOut(**e) for e in entries]


@router.post("/audit/verify", response_model=AuditVerifyOut, tags=["Audit Log"])
def verify_audit_integrity(
    admin: str = Depends(get_current_admin),
):
    """
    Recompute and verify the entire SHA-256 tamper-evident hash chain.
    """
    storage = get_storage()
    if hasattr(storage, "verify_audit_chain"):
        result = storage.verify_audit_chain()
    else:
        result = {"valid": True, "first_bad_seq": None, "total_entries": 0}

    # Record the verification action itself
    storage.append_audit_entry({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": admin,
        "action": "AUDIT_CHAIN_VERIFICATION_PERFORMED",
        "details": {
            "valid": result["valid"],
            "total_entries_verified": result.get("total_entries", 0),
        },
    })

    return AuditVerifyOut(**result)


@router.get("/audit/export", tags=["Audit Log"])
def export_audit_csv(
    admin: str = Depends(get_current_admin),
):
    """Export the tamper-evident audit log as a downloadable CSV."""
    storage = get_storage()
    entries = storage.get_audit_log(limit=5000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["seq", "entry_id", "timestamp", "actor", "action", "details", "prev_hash", "hash"])
    for e in entries:
        writer.writerow([
            e.get("seq", ""),
            e.get("entry_id", ""),
            e.get("timestamp", ""),
            e.get("actor", ""),
            e.get("action", ""),
            str(e.get("details", "")),
            e.get("prev_hash", ""),
            e.get("hash", ""),
        ])

    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=accessguard_audit_log.csv"
    return response


# ── Demo Reset ────────────────────────────────────────────────────────────────

@router.post("/reset", tags=["Demo"])
def reset_demo_data(
    admin: str = Depends(get_current_admin),
):
    """
    Reset all database records and load fresh synthetic sample data.
    Ensures repeatable demos for judges.
    """
    storage = get_storage()
    storage.reset()

    # Re-run sample dataset
    sample_path = "./data/sample_access.csv"
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            val_res = validate_csv(f.read(), filename="sample_access.csv")
            if val_res.is_valid:
                new_run_id = _process_and_store_df(val_res.df, source_label="sample_access.csv (demo reset)", storage=storage, actor=admin)
                return {
                    "success": True,
                    "message": "Demo data reset successfully",
                    "run_id": new_run_id,
                    "records_loaded": val_res.row_count,
                }

    return {"success": True, "message": "Demo data cleared"}


# ── System Status & Architecture ──────────────────────────────────────────────

@router.get("/system/status", response_model=SystemStatus, tags=["System"])
def get_system_status(
    admin: str = Depends(get_current_admin),
):
    """
    Provide operational transparency: model parameters, storage backend, dataset status.
    """
    settings = get_settings()
    storage = get_storage()
    latest_run_id = storage.get_latest_run_id()

    record_count = 0
    if latest_run_id:
        res = storage.get_records(latest_run_id, page=1, page_size=1)
        record_count = res["total"]

    return SystemStatus(
        status="ok",
        storage_backend=settings.storage_backend,
        model_params={
            "algorithm": "IsolationForest",
            "n_estimators": settings.if_n_estimators,
            "contamination": settings.if_contamination,
            "random_state": settings.if_random_state,
            "features": [
                "permission_count",
                "sensitive_access_count",
                "inactive_days",
                "off_hours_access_count",
                "failed_logins_7d",
                "role_mismatch",
            ],
            "score_range": "0-100 (higher = more unusual outlier)",
        },
        dataset_info={
            "active_run_id": latest_run_id,
            "records_in_active_run": record_count,
            "sample_data_file": "data/sample_access.csv",
        },
        version="1.0.0",
    )
