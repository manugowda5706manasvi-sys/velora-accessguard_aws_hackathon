"""
Risk rules, role-permission baselines, and risk combiner for AccessGuard AI.

All thresholds are in one place — edit this file to tune them.
Rules are transparent and configurable (see RULE_CONFIG below).

Risk level assignment (documented table):
  - High:   ≥1 hard rule hit AND anomaly flag
  - Medium: (≥1 rule hit) OR (anomaly flag alone with score ≥60)
  - Low:    no rule hit and not anomaly (or anomaly score < 60 with no rule)

Anomaly alone (no rule): capped at Medium, labelled "Anomaly — investigate".
High requires rule evidence. This is clearly explained in the UI and docs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

# ── Configurable thresholds ────────────────────────────────────────────────────
RULE_CONFIG = {
    # Permissions above role baseline (multiplier): flag as excessive
    "excessive_permission_multiplier": 1.5,
    # Fallback: flag if permission_count above this percentile (when no role)
    "excessive_permission_percentile": 90,
    # Inactive days threshold for stale-access rule
    "stale_inactive_days": 60,
    # Minimum sensitive_access_count to apply stale-access rule
    "stale_sensitive_min": 3,
    # Off-hours count threshold for unusual-activity rule
    "off_hours_threshold": 20,
    # Failed logins threshold for unusual-activity rule
    "failed_logins_threshold": 10,
    # Role mismatch + sensitive access threshold for role-drift rule
    "role_mismatch_sensitive_min": 5,
    # Unused-privilege combo: high permissions + low activity
    "unused_privilege_permission_min": 15,
    "unused_privilege_inactive_min": 30,
    # Anomaly score cutoff for Medium promotion (anomaly only, no rule)
    "anomaly_score_medium_cutoff": 60,
}

# ── Hardcoded role-permission baselines (per-role median expected permission_count)
# These are overridden by data-computed medians when a 'role' column exists.
ROLE_BASELINES: dict[str, int] = {
    "engineer":   12,
    "analyst":     8,
    "manager":    10,
    "admin":      20,
    "intern":      4,
    "finance":     7,
    "hr":          6,
    "marketing":   5,
    "security":   18,
    "support":     6,
}


@dataclass
class RuleHit:
    rule_id: str
    description: str
    severity: str   # "high" | "medium"
    details: str


@dataclass
class RecordRiskResult:
    employee_id: str
    rule_hits: list[RuleHit]
    risk_level: str           # "Low" | "Medium" | "High"
    explanation: str          # plain-language, 1-2 sentences
    recommendation: str       # "Review permissions" | "Investigate unusual activity" | etc.
    permission_drift: Optional[float] = None   # excess permissions above baseline
    role_baseline: Optional[int] = None        # baseline used (None if no role)


def compute_role_baselines(df: pd.DataFrame) -> dict[str, float]:
    """
    Compute per-role median permission_count from the data.
    Returns a dict mapping role → median (float).
    Falls back to the ROLE_BASELINES table for any role not in data.
    """
    if "role" not in df.columns:
        return {}
    data_medians = df.groupby("role")["permission_count"].median().to_dict()
    merged: dict[str, float] = {**ROLE_BASELINES}
    merged.update({k: float(v) for k, v in data_medians.items()})
    return merged


def _build_explanation(hits: list[RuleHit], is_anomaly: bool,
                        anomaly_score: float, drift: Optional[float]) -> str:
    """Compose a plain-language explanation from rule hits and anomaly flag."""
    parts: list[str] = []
    if hits:
        parts.append(f"{len(hits)} policy rule(s) triggered: "
                     + "; ".join(h.description for h in hits[:3])
                     + ("." if not hits[0].description.endswith(".") else ""))
    if is_anomaly:
        parts.append(
            f"Statistical model flagged this record as unusual "
            f"(anomaly score {anomaly_score:.0f}/100). "
            "An anomaly is a statistical outlier, not confirmed evidence of a threat — "
            "a human should review."
        )
    if drift is not None and drift > 0:
        parts.append(
            f"Permission count is {drift:.0f} above the expected baseline for this role."
        )
    if not parts:
        parts.append("No policy rules triggered and not flagged as a statistical anomaly.")
    return " ".join(parts)


def _build_recommendation(hits: list[RuleHit], is_anomaly: bool, risk: str) -> str:
    """Return a plain-language recommendation (never says 'revoke')."""
    if risk == "High":
        return (
            "High-risk access detected. Recommended action: review this employee's "
            "permissions, verify whether their current role requires this access level, "
            "and record a decision in the review queue. Consider reducing unnecessary access "
            "(manual action required — this tool does not change real permissions)."
        )
    if risk == "Medium":
        if any(h.rule_id == "stale_access" for h in hits):
            return (
                "Stale access detected. Recommended: verify whether this employee still "
                "needs access, and if not, record that access should be reduced."
            )
        if any(h.rule_id == "unusual_activity" for h in hits):
            return (
                "Unusual activity pattern detected. Recommended: investigate recent "
                "access logs and confirm legitimacy with the employee's manager."
            )
        if is_anomaly:
            return (
                "Statistical anomaly detected with no specific rule hit. "
                "Recommended: investigate — this may be normal behaviour "
                "or may warrant closer review."
            )
    return (
        "No immediate action required. Access appears within expected parameters. "
        "Continue routine periodic access reviews."
    )


def evaluate_record(
    row: pd.Series,
    role_baselines: dict[str, float],
    p90_permissions: float,
    has_role: bool,
    anomaly_score: float,
    is_anomaly: bool,
) -> RecordRiskResult:
    """
    Apply all rules to a single record and compute its risk level.

    Args:
        row: A row from the validated DataFrame.
        role_baselines: per-role median permission_count (may be empty).
        p90_permissions: 90th-percentile permission_count across the dataset.
        has_role: whether the 'role' column exists in the data.
        anomaly_score: 0-100 score from the ML pipeline.
        is_anomaly: True if IsolationForest labelled as outlier.
    """
    hits: list[RuleHit] = []
    emp_id = str(row.get("employee_id", "unknown"))
    perm   = int(row.get("permission_count", 0))
    sens   = int(row.get("sensitive_access_count", 0))
    inact  = int(row.get("inactive_days", 0))
    ohrs   = int(row.get("off_hours_access_count", 0))
    fails  = int(row.get("failed_logins_7d", 0))
    mismatch = int(row.get("role_mismatch", 0))
    role   = str(row.get("role", "")) if has_role else ""

    permission_drift: Optional[float] = None
    role_baseline: Optional[int] = None

    # ── Rule 1: Excessive permissions ─────────────────────────────────────────
    if has_role and role and role in role_baselines:
        baseline = role_baselines[role]
        role_baseline = int(baseline)
        threshold = baseline * RULE_CONFIG["excessive_permission_multiplier"]
        if perm > threshold:
            permission_drift = perm - baseline
            hits.append(RuleHit(
                rule_id="excessive_permissions",
                description=(
                    f"Permission count ({perm}) is {permission_drift:.0f} above the "
                    f"expected baseline for role '{role}' ({role_baseline})"
                ),
                severity="high",
                details=f"baseline={role_baseline}, actual={perm}, threshold_multiplier="
                        f"{RULE_CONFIG['excessive_permission_multiplier']}",
            ))
    elif perm > p90_permissions:
        permission_drift = perm - p90_permissions
        hits.append(RuleHit(
            rule_id="excessive_permissions_p90",
            description=(
                f"Permission count ({perm}) exceeds the 90th-percentile threshold "
                f"({p90_permissions:.0f}) for this dataset"
            ),
            severity="high",
            details=f"p90={p90_permissions:.1f}, actual={perm}",
        ))

    # ── Rule 2: Stale / outdated access ───────────────────────────────────────
    if (inact >= RULE_CONFIG["stale_inactive_days"]
            and sens >= RULE_CONFIG["stale_sensitive_min"]):
        hits.append(RuleHit(
            rule_id="stale_access",
            description=(
                f"Account inactive for {inact} days while holding "
                f"{sens} sensitive access permissions"
            ),
            severity="high",
            details=f"inactive_threshold={RULE_CONFIG['stale_inactive_days']}, "
                    f"sensitive_min={RULE_CONFIG['stale_sensitive_min']}",
        ))

    # ── Rule 3: Role mismatch with sensitive access ───────────────────────────
    if mismatch == 1 and sens >= RULE_CONFIG["role_mismatch_sensitive_min"]:
        hits.append(RuleHit(
            rule_id="role_drift",
            description=(
                f"Role mismatch flag set with {sens} sensitive access permissions — "
                "permissions may not match the current role"
            ),
            severity="high",
            details=f"role_mismatch=1, sensitive_access={sens}, "
                    f"min_sensitive={RULE_CONFIG['role_mismatch_sensitive_min']}",
        ))

    # ── Rule 4: Unusual activity (off-hours or failed-login spike) ────────────
    off_hours_triggered = ohrs >= RULE_CONFIG["off_hours_threshold"]
    failed_login_triggered = fails >= RULE_CONFIG["failed_logins_threshold"]
    if off_hours_triggered or failed_login_triggered:
        desc_parts = []
        if off_hours_triggered:
            desc_parts.append(f"off-hours access count {ohrs} ≥ threshold "
                              f"{RULE_CONFIG['off_hours_threshold']}")
        if failed_login_triggered:
            desc_parts.append(f"failed logins {fails} ≥ threshold "
                              f"{RULE_CONFIG['failed_logins_threshold']}")
        hits.append(RuleHit(
            rule_id="unusual_activity",
            description="Unusual activity: " + "; ".join(desc_parts),
            severity="medium",
            details=f"off_hours={ohrs}, failed_logins={fails}",
        ))

    # ── Rule 5: Unused-privilege combination ──────────────────────────────────
    if (perm >= RULE_CONFIG["unused_privilege_permission_min"]
            and inact >= RULE_CONFIG["unused_privilege_inactive_min"]):
        hits.append(RuleHit(
            rule_id="unused_privilege",
            description=(
                f"High permission count ({perm}) combined with {inact} inactive days "
                "— privileges may be unused and should be reviewed"
            ),
            severity="medium",
            details=f"perm_min={RULE_CONFIG['unused_privilege_permission_min']}, "
                    f"inactive_min={RULE_CONFIG['unused_privilege_inactive_min']}",
        ))

    # ── Risk level assignment ──────────────────────────────────────────────────
    has_high_rule = any(h.severity == "high" for h in hits)
    has_any_rule = len(hits) > 0

    if has_high_rule and is_anomaly:
        risk = "High"
    elif has_high_rule or (has_any_rule and is_anomaly):
        risk = "High"
    elif has_any_rule or (is_anomaly and anomaly_score >= RULE_CONFIG["anomaly_score_medium_cutoff"]):
        risk = "Medium"
    else:
        risk = "Low"

    explanation = _build_explanation(hits, is_anomaly, anomaly_score, permission_drift)
    recommendation = _build_recommendation(hits, is_anomaly, risk)

    return RecordRiskResult(
        employee_id=emp_id,
        rule_hits=hits,
        risk_level=risk,
        explanation=explanation,
        recommendation=recommendation,
        permission_drift=permission_drift,
        role_baseline=role_baseline,
    )


def evaluate_all(
    df: pd.DataFrame,
    anomaly_scores: dict[str, float],      # employee_id → score 0-100
    anomaly_flags: dict[str, bool],        # employee_id → True/False
    has_role: bool,
) -> list[RecordRiskResult]:
    """
    Run rules evaluation for every row in df.

    Args:
        df: Validated DataFrame.
        anomaly_scores: Map from employee_id to anomaly score.
        anomaly_flags: Map from employee_id to is_anomaly bool.
        has_role: Whether a 'role' column is present.
    """
    role_baselines = compute_role_baselines(df) if has_role else {}
    p90 = float(df["permission_count"].quantile(0.90))

    results: list[RecordRiskResult] = []
    for _, row in df.iterrows():
        emp_id = str(row.get("employee_id", ""))
        score  = anomaly_scores.get(emp_id, 0.0)
        flag   = anomaly_flags.get(emp_id, False)
        results.append(
            evaluate_record(
                row=row,
                role_baselines=role_baselines,
                p90_permissions=p90,
                has_role=has_role,
                anomaly_score=score,
                is_anomaly=flag,
            )
        )
    return results
