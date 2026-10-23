"""
Synthetic access-data generator.
Produces ~250 employee-access records across 5 SaaS apps with ~8-10%
injected risky patterns and 6 labelled showcase employees.

Usage:
    python scripts/generate_data.py            # writes data/sample_access.csv
    python -c "from scripts.generate_data import generate; df = generate()"
"""

import pathlib
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

# ── Role-permission baselines (median expected permission_count per role) ──────
ROLE_BASELINES: dict[str, int] = {
    "engineer":       12,
    "analyst":         8,
    "manager":        10,
    "admin":          20,
    "intern":          4,
    "finance":         7,
    "hr":              6,
    "marketing":       5,
    "security":       18,
    "support":         6,
}

APPS = ["GitHub", "Google Workspace", "AWS Console", "Slack", "Jira"]
DEPARTMENTS = ["Engineering", "Finance", "Marketing", "HR", "Security", "Support"]
ROLES = list(ROLE_BASELINES.keys())


def _base_record(rng: np.random.Generator, emp_id: str, role: str,
                 department: str, app: str) -> dict:
    """Generate a normal (low-risk) record for the given role."""
    baseline = ROLE_BASELINES[role]
    permission_count = int(rng.normal(baseline, baseline * 0.15))
    permission_count = max(1, permission_count)

    sensitive_access_count = int(rng.normal(baseline * 0.2, 1.5))
    sensitive_access_count = max(0, sensitive_access_count)

    inactive_days = int(rng.exponential(15))
    off_hours_access_count = int(rng.poisson(2))
    failed_logins_7d = int(rng.poisson(0.5))
    role_mismatch = 0

    return {
        "employee_id": emp_id,
        "employee_name": emp_id.replace("_", " ").title(),
        "role": role,
        "department": department,
        "app": app,
        "permission_count": permission_count,
        "sensitive_access_count": sensitive_access_count,
        "inactive_days": inactive_days,
        "off_hours_access_count": off_hours_access_count,
        "failed_logins_7d": failed_logins_7d,
        "role_mismatch": role_mismatch,
        "is_injected_risk": False,
        "risk_label": "Low",
    }


def _inject_excessive_permissions(rec: dict, rng: np.random.Generator) -> dict:
    """Pattern: permission_count >> role baseline."""
    baseline = ROLE_BASELINES[rec["role"]]
    rec["permission_count"] = int(baseline * rng.uniform(2.5, 4.0))
    rec["sensitive_access_count"] = int(rec["sensitive_access_count"] * rng.uniform(2, 3))
    rec["is_injected_risk"] = True
    rec["risk_label"] = "High"
    return rec


def _inject_stale_access(rec: dict, rng: np.random.Generator) -> dict:
    """Pattern: long inactivity while holding sensitive access."""
    rec["inactive_days"] = int(rng.uniform(90, 180))
    rec["sensitive_access_count"] = int(rng.uniform(5, 15))
    rec["off_hours_access_count"] = 0
    rec["is_injected_risk"] = True
    rec["risk_label"] = "High"
    return rec


def _inject_off_hours_burst(rec: dict, rng: np.random.Generator) -> dict:
    """Pattern: spike in off-hours logins."""
    rec["off_hours_access_count"] = int(rng.uniform(30, 80))
    rec["failed_logins_7d"] = int(rng.uniform(8, 20))
    rec["is_injected_risk"] = True
    rec["risk_label"] = "Medium"
    return rec


def _inject_failed_login_spike(rec: dict, rng: np.random.Generator) -> dict:
    """Pattern: failed login spike only."""
    rec["failed_logins_7d"] = int(rng.uniform(15, 40))
    rec["is_injected_risk"] = True
    rec["risk_label"] = "Medium"
    return rec


def _inject_role_mismatch(rec: dict, rng: np.random.Generator) -> dict:
    """Pattern: role changed but permissions not cleaned up."""
    rec["role_mismatch"] = 1
    rec["permission_count"] = int(ROLE_BASELINES[rec["role"]] * rng.uniform(1.8, 3.0))
    rec["sensitive_access_count"] = int(rng.uniform(8, 20))
    rec["is_injected_risk"] = True
    rec["risk_label"] = "High"
    return rec


# ── 6 showcase employees (2 High, 2 Medium, 2 Low) ───────────────────────────
def _build_showcase() -> list[dict]:
    return [
        # HIGH-1: Finance→Marketing, still has finance admin
        {
            "employee_id": "showcase_high_001",
            "employee_name": "Jordan Blake",
            "role": "marketing",
            "department": "Marketing",
            "app": "AWS Console",
            "permission_count": 38,
            "sensitive_access_count": 22,
            "inactive_days": 5,
            "off_hours_access_count": 4,
            "failed_logins_7d": 1,
            "role_mismatch": 1,
            "is_injected_risk": True,
            "risk_label": "High",
        },
        # HIGH-2: Intern with admin-level permissions
        {
            "employee_id": "showcase_high_002",
            "employee_name": "Priya Sharma",
            "role": "intern",
            "department": "Engineering",
            "app": "GitHub",
            "permission_count": 45,
            "sensitive_access_count": 18,
            "inactive_days": 0,
            "off_hours_access_count": 12,
            "failed_logins_7d": 3,
            "role_mismatch": 1,
            "is_injected_risk": True,
            "risk_label": "High",
        },
        # MEDIUM-1: Dormant account with lingering access
        {
            "employee_id": "showcase_med_001",
            "employee_name": "Carlos Rivera",
            "role": "analyst",
            "department": "Finance",
            "app": "Jira",
            "permission_count": 9,
            "sensitive_access_count": 7,
            "inactive_days": 120,
            "off_hours_access_count": 0,
            "failed_logins_7d": 0,
            "role_mismatch": 0,
            "is_injected_risk": True,
            "risk_label": "Medium",
        },
        # MEDIUM-2: Off-hours access burst
        {
            "employee_id": "showcase_med_002",
            "employee_name": "Amara Osei",
            "role": "engineer",
            "department": "Engineering",
            "app": "Slack",
            "permission_count": 13,
            "sensitive_access_count": 3,
            "inactive_days": 2,
            "off_hours_access_count": 55,
            "failed_logins_7d": 11,
            "role_mismatch": 0,
            "is_injected_risk": True,
            "risk_label": "Medium",
        },
        # LOW-1: Textbook normal engineer
        {
            "employee_id": "showcase_low_001",
            "employee_name": "Sam Chen",
            "role": "engineer",
            "department": "Engineering",
            "app": "GitHub",
            "permission_count": 12,
            "sensitive_access_count": 2,
            "inactive_days": 3,
            "off_hours_access_count": 1,
            "failed_logins_7d": 0,
            "role_mismatch": 0,
            "is_injected_risk": False,
            "risk_label": "Low",
        },
        # LOW-2: Normal HR user
        {
            "employee_id": "showcase_low_002",
            "employee_name": "Maria Dos Santos",
            "role": "hr",
            "department": "HR",
            "app": "Google Workspace",
            "permission_count": 6,
            "sensitive_access_count": 1,
            "inactive_days": 7,
            "off_hours_access_count": 0,
            "failed_logins_7d": 0,
            "role_mismatch": 0,
            "is_injected_risk": False,
            "risk_label": "Low",
        },
    ]


def generate(seed: int = 42, n_base: int = 244) -> pd.DataFrame:
    """
    Generate a reproducible synthetic dataset.

    Args:
        seed: Random seed for full reproducibility.
        n_base: Number of base (bulk) records; 6 showcase employees are added on top.

    Returns:
        DataFrame with 250 rows total.
    """
    rng = np.random.default_rng(seed)

    records = []
    emp_counter = 1

    # Determine how many risky records to inject (~9% of n_base)
    n_risky = max(1, int(n_base * 0.09))
    risky_indices = set(rng.choice(n_base, size=n_risky, replace=False).tolist())

    inject_fns = [
        _inject_excessive_permissions,
        _inject_stale_access,
        _inject_off_hours_burst,
        _inject_failed_login_spike,
        _inject_role_mismatch,
    ]

    for i in range(n_base):
        role = ROLES[int(rng.integers(0, len(ROLES)))]
        department = DEPARTMENTS[int(rng.integers(0, len(DEPARTMENTS)))]
        app = APPS[int(rng.integers(0, len(APPS)))]
        emp_id = f"emp_{emp_counter:04d}"
        emp_counter += 1

        rec = _base_record(rng, emp_id, role, department, app)

        if i in risky_indices:
            fn = inject_fns[int(rng.integers(0, len(inject_fns)))]
            rec = fn(rec, rng)

        records.append(rec)

    # Add 6 showcase employees
    records.extend(_build_showcase())

    df = pd.DataFrame(records)

    # Ensure non-negative integers
    numeric_cols = [
        "permission_count", "sensitive_access_count", "inactive_days",
        "off_hours_access_count", "failed_logins_7d",
    ]
    for col in numeric_cols:
        df[col] = df[col].clip(lower=0).astype(int)

    df["role_mismatch"] = df["role_mismatch"].astype(int)

    # Column order
    ordered = [
        "employee_id", "employee_name", "role", "department", "app",
        "permission_count", "sensitive_access_count", "inactive_days",
        "off_hours_access_count", "failed_logins_7d", "role_mismatch",
        "is_injected_risk", "risk_label",
    ]
    df = df[ordered].reset_index(drop=True)
    return df


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = generate()
    out = DATA_DIR / "sample_access.csv"
    df.to_csv(out, index=False)
    total = len(df)
    risky = df["is_injected_risk"].sum()
    print(f"Generated {total} records ({risky} injected risk = {risky/total*100:.1f}%)")
    print(f"Saved to {out}")
    # Summary by risk_label
    print(df["risk_label"].value_counts().to_string())


if __name__ == "__main__":
    main()
