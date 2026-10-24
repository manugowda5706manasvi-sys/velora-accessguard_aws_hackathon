"""
Tests for Employee Risk Scanner API endpoint.
Verifies search by ID/name, baseline comparison, risk scoring,
and explainability findings for synthetic profiles.
"""

from __future__ import annotations

import os
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient

os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "TestPassword123!"
os.environ["SECRET_KEY"] = "supersecretkeyfortestingpurposesonly32chars"
os.environ["STORAGE_BACKEND"] = "sqlite"
os.environ["SQLITE_DB_PATH"] = "./data/test_accessguard.db"

from backend.app.api.scanner import (
    SYNTHETIC_PROFILES,
    _compute_profile_summary,
    _risk_level_for_score,
    _score_risk,
)
from backend.app.main import app
from backend.app.storage.base import get_storage


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_scanner_suggestions(client):
    res = client.get("/api/scanner/suggestions")
    assert res.status_code == 200
    suggestions = res.json()
    assert len(suggestions) >= 6
    ids = [s["employee_id"] for s in suggestions]
    assert "EMP-1042" in ids
    assert "EMP-1007" in ids
    assert "EMP-1033" in ids
    assert "EMP-1004" in ids
    assert all(0 <= item["risk_score"] <= 100 for item in suggestions)
    assert {item["employee_id"]: item["risk_score"] for item in suggestions} == {
        profile["employee_id"]: _compute_profile_summary(profile).risk_score
        for profile in SYNTHETIC_PROFILES
    }
    raw_profiles = {profile["employee_id"]: profile for profile in SYNTHETIC_PROFILES}
    assert all(
        item["employee_name"] == raw_profiles[item["employee_id"]]["employee_name"]
        and item["job_title"] == raw_profiles[item["employee_id"]]["job_title"]
        for item in suggestions
    )


def test_scan_employee_by_id_excessive_admin(client):
    res = client.get("/api/scanner/employee/EMP-1042")
    assert res.status_code == 200
    data = res.json()
    assert data["employee_id"] == "EMP-1042"
    assert data["employee_name"] == "Jordan Blake"
    assert data["department"] == "Marketing"
    assert data["risk_level"] == "Critical"
    assert data["risk_score"] >= 75
    assert "critical-severity" in data["risk_explanation"]
    assert "permission count are not score inputs" in data["risk_explanation"]
    assert data["is_synthetic"] is True
    assert "AWS Console" in [a["app_name"] for a in data["assigned_applications"]]
    # Has findings and recommendations
    assert len(data["findings"]) > 0
    assert len(data["recommendations"]) > 0


def test_scan_employee_by_name_search(client):
    res = client.get("/api/scanner/employee/jordan")
    assert res.status_code == 200
    data = res.json()
    assert data["employee_id"] == "EMP-1042"
    assert "Jordan" in data["employee_name"]


def test_scan_employee_by_full_name(client):
    res = client.get("/api/scanner/employee/Jordan%20Blake")
    assert res.status_code == 200
    assert res.json()["employee_id"] == "EMP-1042"


def test_employee_search_endpoint_returns_specific_inventory_and_report_metadata(client):
    jordan = client.get("/api/scanner/employees", params={"query": "EMP-1042"})
    priya = client.get("/api/scanner/employees", params={"query": "Priya Sharma"})
    assert jordan.status_code == 200
    assert priya.status_code == 200
    jordan_data = jordan.json()
    priya_data = priya.json()
    assert jordan_data["employee_id"] == "EMP-1042"
    assert priya_data["employee_id"] == "EMP-1007"
    assert jordan_data["assigned_applications"] != priya_data["assigned_applications"]
    assert jordan_data["data_source_status"] == "Demo data — no live identity provider connected."
    assert jordan_data["analysis_timestamp"]
    assert jordan_data["privileged_applications_count"] > 0
    assert jordan_data["limitations"]
    assert all(
        finding["recommended_action"]
        for finding in jordan_data["findings"]
    )
    assert any(
        finding["app_name"] == "AWS Console"
        and finding["permission_name"] == "AdministratorAccess"
        for finding in jordan_data["findings"]
    )
    assert any(finding["severity"] == "Critical" for finding in jordan_data["findings"])
    assert any(
        finding["app_name"] == "Google Workspace"
        and finding["permission_name"] == "Drive.PayrollConfidential"
        for finding in client.get(
            "/api/scanner/employees", params={"query": "EMP-1089"}
        ).json()["findings"]
    )


def test_employee_search_rejects_blank_query(client):
    assert client.get("/api/scanner/employees", params={"query": "   "}).status_code == 422
    assert client.get("/api/scanner/employees").status_code == 422


def test_employee_analysis_is_recorded_in_audit_log(client):
    res = client.get("/api/scanner/employees", params={"query": "EMP-1042"})
    assert res.status_code == 200
    entries = get_storage().get_audit_log(limit=10)
    assert any(
        entry["action"] == "EMPLOYEE_ACCESS_RISK_ANALYSED"
        and entry["details"]["employee_id"] == "EMP-1042"
        for entry in entries
    )


def test_scan_employee_intern_elevated(client):
    res = client.get("/api/scanner/employee/EMP-1007")
    assert res.status_code == 200
    data = res.json()
    assert data["employee_name"] == "Priya Sharma"
    assert data["role"] == "intern"
    assert data["risk_level"] == "Critical"
    # Find github org owner
    github_app = next(a for a in data["assigned_applications"] if a["app_name"] == "GitHub")
    perms = [p["name"] for p in github_app["permissions"]]
    assert "Organization.Owner" in perms


def test_scan_employee_baseline_compliant_low_risk(client):
    res = client.get("/api/scanner/employee/EMP-1033")
    assert res.status_code == 200
    data = res.json()
    assert data["employee_name"] == "Sam Chen"
    assert data["risk_level"] == "Low"
    assert data["risk_score"] <= 30


def test_scan_employee_privileged_expected_review(client):
    res = client.get("/api/scanner/employee/EMP-1004")
    assert res.status_code == 200
    data = res.json()
    assert data["employee_name"] == "Elena Rostova"
    assert data["role"] == "security"
    assert data["risk_level"] == "Medium"


def test_scan_employee_not_found(client):
    res = client.get("/api/scanner/employee/unknown_user_9999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
    query_res = client.get(
        "/api/scanner/employees", params={"query": "unknown_user_9999"}
    )
    assert query_res.status_code == 404
    assert "not found" in query_res.json()["detail"].lower()


@pytest.mark.parametrize(
    ("findings", "score", "risk_level"),
    [
        ([], 0, "Low"),
        ([{"severity": "Low", "evidence": "baseline aligned"}], 10, "Low"),
        ([{"severity": "Medium", "evidence": "stale account"}], 40, "Medium"),
        ([{"severity": "High", "evidence": "unexpected admin"}], 75, "High"),
        ([{"severity": "Critical", "evidence": "unexpected admin"}], 90, "Critical"),
        ([{"severity": "High", "evidence": "admin"}] * 6, 100, "Critical"),
    ],
)
def test_risk_score_boundaries_and_explanation(findings, score, risk_level):
    actual_score, actual_level, explanation = _score_risk(findings)
    assert actual_score == score
    assert actual_level == risk_level
    assert 0 <= actual_score <= 100
    if findings:
        assert findings[0]["evidence"] in explanation
    assert "application count" in explanation.lower()


@pytest.mark.parametrize(
    ("score", "risk_level"),
    [
        (0, "Low"),
        (29, "Low"),
        (30, "Medium"),
        (69, "Medium"),
        (70, "High"),
        (89, "High"),
        (90, "Critical"),
        (100, "Critical"),
    ],
)
def test_risk_level_threshold_boundaries(score, risk_level):
    assert _risk_level_for_score(score) == risk_level


def test_only_highest_finding_severity_contributes_to_score():
    score, risk_level, explanation = _score_risk(
        [
            {"severity": "High", "evidence": "unexpected administrator"},
            {"severity": "Medium", "evidence": "stale account"},
        ]
    )
    assert (score, risk_level) == (75, "High")
    assert "only the highest finding severity contributes" in explanation.lower()


def test_risk_score_is_independent_of_application_count():
    profile = deepcopy(SYNTHETIC_PROFILES[0])
    original_score = _compute_profile_summary(profile).risk_score
    profile["assigned_applications"].append(
        {
            "app_name": "Additional Sample App",
            "category": "Synthetic test",
            "account_status": "Active",
            "total_permissions": 1000,
            "permissions": [],
        }
    )
    assert _compute_profile_summary(profile).risk_score == original_score


def test_synthetic_profiles_have_consistent_totals_and_role_baselines():
    expected_baselines = {
        "marketing": 5,
        "intern": 4,
        "engineer": 12,
        "analyst": 8,
        "security": 18,
    }
    for raw in SYNTHETIC_PROFILES:
        profile = _compute_profile_summary(raw)
        assert profile.role_baseline_permissions == expected_baselines[profile.role]
        assert profile.total_assigned_permissions == sum(
            app["total_permissions"] for app in raw["assigned_applications"]
        )
        assert profile.employee_id == raw["employee_id"]
        assert profile.employee_name == raw["employee_name"]
        assert profile.risk_score <= 100
