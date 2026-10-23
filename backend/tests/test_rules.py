"""Tests for the risk rules engine and combiner (Stage 4)."""
import pathlib
import sys
import pytest
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from backend.app.rules.engine import (
    evaluate_record, evaluate_all, compute_role_baselines,
    ROLE_BASELINES, RULE_CONFIG,
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def make_normal_row(emp_id: str = "emp_001") -> pd.Series:
    return pd.Series({
        "employee_id": emp_id,
        "role": "engineer",
        "permission_count": 12,
        "sensitive_access_count": 2,
        "inactive_days": 5,
        "off_hours_access_count": 2,
        "failed_logins_7d": 0,
        "role_mismatch": 0,
    })


BASE_RL = dict(ROLE_BASELINES)
P90_NORMAL = 25.0


# ── Normal record ─────────────────────────────────────────────────────────────
class TestNormalRecord:
    def test_normal_is_low(self):
        row = make_normal_row()
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 10.0, False)
        assert r.risk_level == "Low"
        assert r.rule_hits == []

    def test_explanation_present(self):
        row = make_normal_row()
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 10.0, False)
        assert isinstance(r.explanation, str)
        assert len(r.explanation) > 10

    def test_recommendation_present(self):
        row = make_normal_row()
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 10.0, False)
        assert isinstance(r.recommendation, str)


# ── Rule: excessive permissions ───────────────────────────────────────────────
class TestExcessivePermissions:
    def test_excessive_perm_hits_rule(self):
        row = make_normal_row()
        row["permission_count"] = int(ROLE_BASELINES["engineer"]
                                      * RULE_CONFIG["excessive_permission_multiplier"] + 5)
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 20.0, False)
        rule_ids = [h.rule_id for h in r.rule_hits]
        assert "excessive_permissions" in rule_ids

    def test_p90_fallback_when_no_role(self):
        row = make_normal_row()
        row["permission_count"] = 30  # above P90_NORMAL=25
        r = evaluate_record(row, {}, P90_NORMAL, False, 20.0, False)
        rule_ids = [h.rule_id for h in r.rule_hits]
        assert "excessive_permissions_p90" in rule_ids


# ── Rule: stale access ────────────────────────────────────────────────────────
class TestStaleAccess:
    def test_stale_access_rule(self):
        row = make_normal_row()
        row["inactive_days"] = RULE_CONFIG["stale_inactive_days"] + 10
        row["sensitive_access_count"] = RULE_CONFIG["stale_sensitive_min"] + 2
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 30.0, False)
        assert any(h.rule_id == "stale_access" for h in r.rule_hits)

    def test_stale_inactive_but_low_sensitive_no_rule(self):
        row = make_normal_row()
        row["inactive_days"] = RULE_CONFIG["stale_inactive_days"] + 10
        row["sensitive_access_count"] = 0
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 5.0, False)
        assert not any(h.rule_id == "stale_access" for h in r.rule_hits)


# ── Rule: role drift ──────────────────────────────────────────────────────────
class TestRoleDrift:
    def test_role_mismatch_with_sensitive_hits_rule(self):
        row = make_normal_row()
        row["role_mismatch"] = 1
        row["sensitive_access_count"] = RULE_CONFIG["role_mismatch_sensitive_min"] + 2
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 40.0, False)
        assert any(h.rule_id == "role_drift" for h in r.rule_hits)

    def test_role_mismatch_low_sensitive_no_rule(self):
        row = make_normal_row()
        row["role_mismatch"] = 1
        row["sensitive_access_count"] = 0
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 5.0, False)
        assert not any(h.rule_id == "role_drift" for h in r.rule_hits)


# ── Rule: unusual activity ────────────────────────────────────────────────────
class TestUnusualActivity:
    def test_off_hours_spike_hits_rule(self):
        row = make_normal_row()
        row["off_hours_access_count"] = RULE_CONFIG["off_hours_threshold"] + 5
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 50.0, True)
        assert any(h.rule_id == "unusual_activity" for h in r.rule_hits)

    def test_failed_login_spike_hits_rule(self):
        row = make_normal_row()
        row["failed_logins_7d"] = RULE_CONFIG["failed_logins_threshold"] + 5
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 50.0, True)
        assert any(h.rule_id == "unusual_activity" for h in r.rule_hits)


# ── Risk level logic ──────────────────────────────────────────────────────────
class TestRiskLevelLogic:
    def test_anomaly_only_capped_at_medium(self):
        row = make_normal_row()
        # No rule hits, but is_anomaly=True with high score
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 80.0, True)
        assert r.risk_level in ("Low", "Medium")
        assert r.risk_level != "High", \
            "Anomaly alone (no rule) must not produce High risk"

    def test_high_rule_plus_anomaly_is_high(self):
        row = make_normal_row()
        row["permission_count"] = 100     # triggers excessive_permissions
        row["role_mismatch"] = 1
        row["sensitive_access_count"] = 10  # triggers role_drift
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 90.0, True)
        assert r.risk_level == "High"

    def test_low_anomaly_score_no_rule_stays_low(self):
        row = make_normal_row()
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 40.0, True)
        # anomaly score 40 < cutoff 60, no rules → Low
        assert r.risk_level == "Low"


# ── Recommendation never says "revoke" ───────────────────────────────────────
class TestRecommendationLanguage:
    def test_no_revoke_in_recommendation(self):
        row = make_normal_row()
        row["permission_count"] = 100
        row["role_mismatch"] = 1
        row["sensitive_access_count"] = 15
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 90.0, True)
        assert "revoke" not in r.recommendation.lower(), \
            "Recommendation must not use the word 'revoke'"

    def test_recommendation_says_recommended_or_recorded(self):
        row = make_normal_row()
        row["permission_count"] = 100
        r = evaluate_record(row, BASE_RL, P90_NORMAL, True, 90.0, True)
        text = r.recommendation.lower()
        assert "recommend" in text or "recorded" in text or "review" in text


# ── evaluate_all ──────────────────────────────────────────────────────────────
class TestEvaluateAll:
    def test_evaluate_all_returns_one_per_row(self):
        df = pd.DataFrame([{
            "employee_id": f"e{i}",
            "role": "engineer",
            "permission_count": 12,
            "sensitive_access_count": 2,
            "inactive_days": 5,
            "off_hours_access_count": 2,
            "failed_logins_7d": 0,
            "role_mismatch": 0,
        } for i in range(20)])
        scores  = {f"e{i}": 10.0 for i in range(20)}
        flags   = {f"e{i}": False for i in range(20)}
        results = evaluate_all(df, scores, flags, has_role=True)
        assert len(results) == 20

    def test_no_role_column_skips_baseline_rules(self):
        df = pd.DataFrame([{
            "employee_id": "e0",
            "permission_count": 100,  # would trigger rule if role known
            "sensitive_access_count": 2,
            "inactive_days": 5,
            "off_hours_access_count": 2,
            "failed_logins_7d": 0,
            "role_mismatch": 0,
        }])
        # With no role, only p90 fallback applies
        results = evaluate_all(df, {"e0": 20.0}, {"e0": False}, has_role=False)
        assert len(results) == 1
        # p90 is also 100 (single row), so no rule triggered
        rule_ids = [h.rule_id for h in results[0].rule_hits]
        assert "excessive_permissions" not in rule_ids


# ── compute_role_baselines ────────────────────────────────────────────────────
class TestRoleBaselines:
    def test_baselines_computed_from_data(self):
        df = pd.DataFrame({
            "role": ["engineer", "engineer", "analyst"],
            "permission_count": [10, 14, 8],
        })
        bl = compute_role_baselines(df)
        assert "engineer" in bl
        assert bl["engineer"] == pytest.approx(12.0)  # median of [10, 14]

    def test_fallback_for_unknown_role(self):
        df = pd.DataFrame({
            "role": ["engineer"],
            "permission_count": [12],
        })
        bl = compute_role_baselines(df)
        # Other roles should fall back to ROLE_BASELINES defaults
        assert "admin" in bl
        assert bl["admin"] == ROLE_BASELINES["admin"]
