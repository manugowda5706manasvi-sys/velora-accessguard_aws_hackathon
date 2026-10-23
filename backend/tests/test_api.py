"""
Tests for AccessGuard AI FastAPI endpoints.
Tests authentication, validation, rate limiting, review workflow,
audit verification, and dashboard statistics.
"""

from __future__ import annotations

import io
import os
import pytest
from fastapi.testclient import TestClient

# Ensure test env vars before importing app
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "TestPassword123!"
os.environ["SECRET_KEY"] = "supersecretkeyfortestingpurposesonly32chars"
os.environ["STORAGE_BACKEND"] = "sqlite"
os.environ["SQLITE_DB_PATH"] = "./data/test_accessguard.db"

from backend.app.main import app
from backend.app.config import get_settings

get_settings.cache_clear()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_token(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "TestPassword123!"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ── Public Endpoints ──────────────────────────────────────────────────────────

def test_health_check_unauthenticated(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["service"] == "AccessGuard AI"


# ── Auth & Rate Limiting ──────────────────────────────────────────────────────

def test_login_invalid_credentials(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "WrongPassword"})
    assert res.status_code == 401
    assert "Incorrect username or password" in res.json()["detail"]


def test_login_success(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "TestPassword123!"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_protected_routes_require_auth(client):
    # Without token
    res = client.get("/api/records")
    assert res.status_code == 401

    res = client.get("/api/stats")
    assert res.status_code == 401

    res = client.get("/api/audit")
    assert res.status_code == 401


# ── Analysis & Records ────────────────────────────────────────────────────────

def test_analyse_sample_data(client, auth_headers):
    res = client.post("/api/analyse", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "run_id" in data
    assert data["records_processed"] >= 200


def test_get_records_pagination(client, auth_headers):
    res = client.get("/api/records?page=1&page_size=10", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) <= 10
    assert data["total"] >= 200
    assert data["page"] == 1


def test_get_records_filter_by_risk(client, auth_headers):
    res = client.get("/api/records?risk_level=High", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["risk_level"] == "High"


def test_get_single_record_detail(client, auth_headers):
    # Get first record ID
    list_res = client.get("/api/records?page=1&page_size=1", headers=auth_headers)
    assert list_res.status_code == 200
    first_emp = list_res.json()["items"][0]["employee_id"]

    res = client.get(f"/api/records/{first_emp}", headers=auth_headers)
    assert res.status_code == 200
    rec = res.json()
    assert rec["employee_id"] == first_emp
    assert "anomaly_score" in rec
    assert "risk_level" in rec
    assert "explanation" in rec
    assert "recommendation" in rec


# ── Review Workflow ───────────────────────────────────────────────────────────

def test_review_workflow_and_audit(client, auth_headers):
    # Pick first employee
    list_res = client.get("/api/records?page=1&page_size=1", headers=auth_headers)
    emp_id = list_res.json()["items"][0]["employee_id"]

    # Submit review
    review_payload = {
        "status": "Investigating",
        "comment": "Flagged for manual permission audit with team lead.",
        "outcome": None,
    }
    patch_res = client.patch(
        f"/api/records/{emp_id}/review",
        json=review_payload,
        headers=auth_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["success"] is True
    assert patch_res.json()["record"]["review_status"] == "Investigating"

    # Resolve review
    resolve_payload = {
        "status": "Resolved",
        "comment": "Confirmed stale access; manual action recorded in IAM console.",
        "outcome": "Access reduced (manual action recorded)",
    }
    resolve_res = client.patch(
        f"/api/records/{emp_id}/review",
        json=resolve_payload,
        headers=auth_headers,
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["record"]["review_status"] == "Resolved"
    assert resolve_res.json()["record"]["review_outcome"] == "Access reduced (manual action recorded)"


# ── Dashboard Statistics ──────────────────────────────────────────────────────

def test_dashboard_stats(client, auth_headers):
    res = client.get("/api/stats", headers=auth_headers)
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_records"] >= 200
    assert stats["anomaly_count"] > 0
    assert "score_distribution" in stats
    assert len(stats["score_distribution"]) == 5
    assert "risk_by_app" in stats
    assert "alerts" in stats
    assert len(stats["alerts"]) > 0


# ── Audit Trail & Tamper Verification ─────────────────────────────────────────

def test_audit_log_and_verification(client, auth_headers):
    # Fetch audit log
    audit_res = client.get("/api/audit", headers=auth_headers)
    assert audit_res.status_code == 200
    entries = audit_res.json()
    assert len(entries) > 0
    assert "hash" in entries[0]
    assert "prev_hash" in entries[0]

    # Verify SHA-256 hash chain
    verify_res = client.post("/api/audit/verify", headers=auth_headers)
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["valid"] is True
    assert verify_data["first_bad_seq"] is None
    assert verify_data["total_entries"] > 0


def test_audit_csv_export(client, auth_headers):
    res = client.get("/api/audit/export", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "seq,entry_id,timestamp,actor,action" in res.text


# ── CSV Upload Validation ─────────────────────────────────────────────────────

def test_upload_invalid_csv_rejected(client, auth_headers):
    # Missing required column
    bad_csv = "employee_id,permission_count\nEMP001,5\n"
    res = client.post(
        "/api/upload",
        files={"file": ("bad.csv", io.BytesIO(bad_csv.encode()), "text/csv")},
        headers=auth_headers,
    )
    assert res.status_code == 200  # API returns JSON with success: False and human-readable errors
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) > 0


def test_upload_valid_csv(client, auth_headers):
    # Upload sample CSV
    with open("./data/sample_access.csv", "rb") as f:
        content = f.read()
    res = client.post(
        "/api/upload",
        files={"file": ("uploaded_sample.csv", io.BytesIO(content), "text/csv")},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["records_processed"] >= 200
    assert "run_id" in data


# ── Demo Reset ────────────────────────────────────────────────────────────────

def test_demo_reset(client, auth_headers):
    res = client.post("/api/reset", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["records_loaded"] >= 200


# ── System Status ─────────────────────────────────────────────────────────────

def test_system_status(client, auth_headers):
    res = client.get("/api/system/status", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["storage_backend"] == "sqlite"
    assert data["model_params"]["algorithm"] == "IsolationForest"
