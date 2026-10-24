"""
Employee Risk Scanner API module for AccessGuard AI.
Provides synthetic employee profile searching, application permissions breakdown,
role baseline drift evaluation, explainable risk findings, and recommended actions.

NOTE: All records and permission assignments are strictly synthetic test fixtures.
No live identity providers (IdP) or company SaaS systems are connected.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.rules.engine import ROLE_BASELINES
from backend.app.storage.base import get_storage

scanner_router = APIRouter(prefix="/scanner", tags=["Employee Risk Scanner"])


def _permission_terms(name: str) -> list[str]:
    spaced_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return [
        token.casefold()
        for token in spaced_name.replace(".", " ").replace("(", " ").split()
        if len(token) >= 5
    ]


# ── Pydantic Schemas for Scanner ─────────────────────────────────────────────

class AppPermission(BaseModel):
    name: str
    privilege_level: str   # "Critical" | "Elevated" | "Standard" | "Read-Only"
    matches_baseline: bool
    last_used: str         # e.g., "Today", "3 days ago", "120 days ago (Stale)"
    description: str


class AssignedApplication(BaseModel):
    app_name: str
    category: str          # e.g., "Cloud Infrastructure", "Source Code", "Communication"
    account_status: str    # "Active" | "Inactive"
    total_permissions: int
    permissions: list[AppPermission]


class RiskFinding(BaseModel):
    finding_id: str
    severity: str          # "High" | "Medium" | "Low"
    title: str
    description: str
    evidence: str
    app_name: Optional[str] = None
    permission_name: Optional[str] = None
    recommended_action: str


class RecommendedAction(BaseModel):
    priority: str          # "Immediate" | "Review Next Sprint" | "Informational"
    action: str
    target_app: str
    rationale: str


class EmployeeScannerProfile(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    job_title: str
    manager: str
    employment_status: str # "Active (Full-Time)" | "Active (Intern)" | "On Leave"
    role: str
    role_baseline_permissions: int
    total_assigned_permissions: int
    assigned_apps_count: int
    risk_score: int = Field(ge=0, le=100)
    risk_level: str        # "Critical" | "High" | "Medium" | "Low"
    risk_explanation: str
    analysis_timestamp: str
    data_source_status: str
    privileged_applications_count: int
    limitations: list[str]
    is_synthetic: bool = True
    notice: str = (
        "Synthetic test data only. No live identity provider (IdP) or SaaS tenant is connected. "
        "All recommendations are decision-support guidelines requiring human administrative approval."
    )
    assigned_applications: list[AssignedApplication]
    findings: list[RiskFinding]
    recommendations: list[RecommendedAction]


class ScannerSuggestion(BaseModel):
    employee_id: str
    employee_name: str
    job_title: str
    department: str
    risk_level: str
    risk_score: int
    highlight_tag: str


# ── Synthetic Dataset with 6 Varied Realistic Scenarios ────────────────────────

SYNTHETIC_PROFILES: list[dict] = [
    # Scenario 1: Excessive administrator privileges + Role Mismatch (Jordan Blake)
    {
        "employee_id": "EMP-1042",
        "aliases": ["showcase_high_001", "jordan", "blake"],
        "employee_name": "Jordan Blake",
        "department": "Marketing",
        "job_title": "Senior Growth Marketing Manager",
        "manager": "Rachel Green (VP Marketing)",
        "employment_status": "Active (Full-Time)",
        "role": "marketing",
        "assigned_applications": [
            {
                "app_name": "AWS Console",
                "category": "Cloud Infrastructure",
                "account_status": "Active",
                "total_permissions": 22,
                "permissions": [
                    {
                        "name": "AdministratorAccess",
                        "privilege_level": "Critical",
                        "matches_baseline": False,
                        "last_used": "3 days ago",
                        "description": "Provides full access to all AWS cloud resources and IAM policies across the organization.",
                    },
                    {
                        "name": "BillingFullAccess",
                        "privilege_level": "Elevated",
                        "matches_baseline": False,
                        "last_used": "14 days ago",
                        "description": "Allows viewing and editing payment methods, invoices, and budgets (lingering from former Finance role).",
                    },
                    {
                        "name": "IAMReadOnlyAccess",
                        "privilege_level": "Standard",
                        "matches_baseline": False,
                        "last_used": "5 days ago",
                        "description": "Allows listing users, groups, and attached policies.",
                    },
                ],
            },
            {
                "app_name": "Google Workspace",
                "category": "Productivity & Collaboration",
                "account_status": "Active",
                "total_permissions": 8,
                "permissions": [
                    {
                        "name": "GoogleDrive.MarketingShared",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "Access to marketing collateral, campaign assets, and shared drives.",
                    },
                    {
                        "name": "GoogleAnalytics.Admin",
                        "privilege_level": "Elevated",
                        "matches_baseline": True,
                        "last_used": "Yesterday",
                        "description": "Configuration rights for web traffic tracking and campaign goals.",
                    },
                ],
            },
            {
                "app_name": "Slack",
                "category": "Team Communication",
                "account_status": "Active",
                "total_permissions": 4,
                "permissions": [
                    {
                        "name": "Channel.PostAndInvite",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "Standard messaging and channel collaboration.",
                    },
                ],
            },
            {
                "app_name": "Jira",
                "category": "Project Management",
                "account_status": "Active",
                "total_permissions": 4,
                "permissions": [
                    {
                        "name": "Jira.MarketingBoardContributor",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "Yesterday",
                        "description": "Ticket tracking for campaign sprints.",
                    },
                ],
            },
        ],
        "findings": [
            {
                "finding_id": "FIND-1042-1",
                "severity": "High",
                "app_name": "AWS Console",
                "permission_name": "BillingFullAccess",
                "title": "Severe Permission Drift: Lingering Cloud & Billing Admin",
                "description": "Employee transferred from Finance to Marketing 8 months ago but retains AWS AdministratorAccess and Billing privileges.",
                "evidence": "Marketing role baseline allows max 5 permissions; employee currently holds 38 total permissions (660% above baseline).",
            },
            {
                "finding_id": "FIND-1042-2",
                "severity": "High",
                "title": "Excessive Administrator Rights Outside Job Scope",
                "description": "Growth Marketing Manager holds root-level cloud infrastructure modification capabilities.",
                "evidence": "AWS Console policy 'AdministratorAccess' assigned directly to user.",
            },
        ],
        "recommendations": [
            {
                "priority": "Immediate",
                "action": "Deprovision AWS AdministratorAccess and BillingFullAccess",
                "target_app": "AWS Console",
                "rationale": "Marketing responsibilities do not require root cloud administration or financial budget modifications.",
            },
            {
                "priority": "Review Next Sprint",
                "action": "Transition to Least-Privilege S3 Marketing Viewer role",
                "target_app": "AWS Console",
                "rationale": "If marketing assets are stored in S3, grant scoped read-only access to specific marketing buckets only.",
            },
        ],
    },

    # Scenario 2: Intern with administrator-level permissions (Priya Sharma)
    {
        "employee_id": "EMP-1007",
        "aliases": ["showcase_high_002", "priya", "sharma"],
        "employee_name": "Priya Sharma",
        "department": "Engineering",
        "job_title": "Frontend Engineering Intern",
        "manager": "Alex Mercer (Director of Engineering)",
        "employment_status": "Active (Intern)",
        "role": "intern",
        "assigned_applications": [
            {
                "app_name": "GitHub",
                "category": "Source Code Management",
                "account_status": "Active",
                "total_permissions": 28,
                "permissions": [
                    {
                        "name": "Organization.Owner",
                        "privilege_level": "Critical",
                        "matches_baseline": False,
                        "last_used": "Today",
                        "description": "Full administrative ownership over the entire GitHub organization, billing, and member access.",
                    },
                    {
                        "name": "Repository.Admin (Production Repos)",
                        "privilege_level": "Critical",
                        "matches_baseline": False,
                        "last_used": "Yesterday",
                        "description": "Delete branches, bypass branch protection rules, and merge without approvals.",
                    },
                    {
                        "name": "Secrets.ReadWrite",
                        "privilege_level": "Elevated",
                        "matches_baseline": False,
                        "last_used": "Today",
                        "description": "Direct read/write access to CI/CD production deployment tokens.",
                    },
                ],
            },
            {
                "app_name": "AWS Console",
                "category": "Cloud Infrastructure",
                "account_status": "Active",
                "total_permissions": 12,
                "permissions": [
                    {
                        "name": "EC2FullAccess",
                        "privilege_level": "Elevated",
                        "matches_baseline": False,
                        "last_used": "12 days ago",
                        "description": "Provision, modify, and terminate compute instances.",
                    },
                ],
            },
            {
                "app_name": "Slack",
                "category": "Team Communication",
                "account_status": "Active",
                "total_permissions": 3,
                "permissions": [
                    {
                        "name": "Channel.StandardUser",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "General communication within engineering channels.",
                    },
                ],
            },
            {
                "app_name": "Jira",
                "category": "Project Management",
                "account_status": "Active",
                "total_permissions": 2,
                "permissions": [
                    {
                        "name": "Jira.Developer",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "Assign and update engineering sprint tickets.",
                    },
                ],
            },
        ],
        "findings": [
            {
                "finding_id": "FIND-1007-1",
                "severity": "High",
                "title": "Critical Over-Privileged Account: Organization Owner on Intern Account",
                "description": "Contract intern assigned Organization.Owner rights on enterprise GitHub tenant.",
                "evidence": "Intern baseline allows 4 read/write repo permissions; user currently holds 45 permissions including Org Owner.",
            },
            {
                "finding_id": "FIND-1007-2",
                "severity": "Medium",
                "title": "Unusual Off-Hours Activity & Failed Logins",
                "description": "12 off-hours login sessions and 3 failed login attempts recorded within the last 7 days.",
                "evidence": "Off-hours count 12 vs intern peer median of 0; failed login spike.",
            },
        ],
        "recommendations": [
            {
                "priority": "Immediate",
                "action": "Revoke GitHub Organization.Owner and Production Repo Admin",
                "target_app": "GitHub",
                "rationale": "Intern roles require branch-level write access to frontend repositories only, under peer code review.",
            },
            {
                "priority": "Immediate",
                "action": "Deprovision AWS EC2FullAccess",
                "target_app": "AWS Console",
                "rationale": "Direct infrastructure provisioning rights are not required for frontend development tasks.",
            },
        ],
    },

    # Scenario 3: Multiple elevated permissions across systems (Marcus Vance)
    {
        "employee_id": "EMP-1018",
        "aliases": ["marcus", "vance", "devops_lead"],
        "employee_name": "Marcus Vance",
        "department": "Engineering",
        "job_title": "Staff DevOps Engineer",
        "manager": "Devon Brooks (VP Infrastructure)",
        "employment_status": "Active (Full-Time)",
        "role": "engineer",
        "assigned_applications": [
            {
                "app_name": "AWS Console",
                "category": "Cloud Infrastructure",
                "account_status": "Active",
                "total_permissions": 18,
                "permissions": [
                    {
                        "name": "IAM.FullAccess",
                        "privilege_level": "Critical",
                        "matches_baseline": False,
                        "last_used": "Today",
                        "description": "Can create and attach IAM policies with zero approval gate.",
                    },
                    {
                        "name": "KMS.DecryptAll",
                        "privilege_level": "Critical",
                        "matches_baseline": False,
                        "last_used": "Today",
                        "description": "Unrestricted key decryption for production data stores.",
                    },
                ],
            },
            {
                "app_name": "GitHub",
                "category": "Source Code Management",
                "account_status": "Active",
                "total_permissions": 14,
                "permissions": [
                    {
                        "name": "Organization.Owner",
                        "privilege_level": "Critical",
                        "matches_baseline": False,
                        "last_used": "Today",
                        "description": "Full administrative ownership over GitHub repositories.",
                    },
                ],
            },
            {
                "app_name": "Slack",
                "category": "Team Communication",
                "account_status": "Active",
                "total_permissions": 5,
                "permissions": [
                    {
                        "name": "Primary.Owner",
                        "privilege_level": "Critical",
                        "matches_baseline": False,
                        "last_used": "Yesterday",
                        "description": "Can export corporate communication archives and manage billing.",
                    },
                ],
            },
            {
                "app_name": "Google Workspace",
                "category": "Productivity & Collaboration",
                "account_status": "Active",
                "total_permissions": 4,
                "permissions": [
                    {
                        "name": "SuperAdmin.Delegated",
                        "privilege_level": "Critical",
                        "matches_baseline": False,
                        "last_used": "3 days ago",
                        "description": "Full domain administrator privileges over enterprise mail and storage.",
                    },
                ],
            },
        ],
        "findings": [
            {
                "finding_id": "FIND-1018-1",
                "severity": "High",
                "title": "Toxic Combination: Simultaneous Multi-SaaS Root Administration",
                "description": "User holds highest privilege level across AWS (IAM Full), GitHub (Org Owner), Slack (Primary Owner), and Google Workspace (SuperAdmin).",
                "evidence": "Single identity credential represents catastrophic blast radius across identity, code, cloud, and communication.",
            },
        ],
        "recommendations": [
            {
                "priority": "Immediate",
                "action": "Enforce Separation of Duties",
                "target_app": "Multiple SaaS",
                "rationale": "Transfer Slack Primary Owner and Google Workspace SuperAdmin to dedicated Corporate IT; maintain AWS and GitHub for DevOps.",
            },
            {
                "priority": "Review Next Sprint",
                "action": "Migrate standing IAM.FullAccess to Just-In-Time (JIT) Break-Glass Role",
                "target_app": "AWS Console",
                "rationale": "Standing root-equivalent rights should be replaced with time-bound STS assumed sessions requiring MFA.",
            },
        ],
    },

    # Scenario 4: Long-inactive access with sensitive data rights (Carlos Rivera)
    {
        "employee_id": "EMP-1089",
        "aliases": ["showcase_med_001", "carlos", "rivera"],
        "employee_name": "Carlos Rivera",
        "department": "Finance",
        "job_title": "Senior Financial Analyst",
        "manager": "Linda Zhao (Corporate Controller)",
        "employment_status": "On Leave (Parental/Sabbatical)",
        "role": "analyst",
        "assigned_applications": [
            {
                "app_name": "Jira",
                "category": "Project Management",
                "account_status": "Inactive",
                "total_permissions": 4,
                "permissions": [
                    {
                        "name": "FinanceBoard.Admin",
                        "privilege_level": "Elevated",
                        "matches_baseline": True,
                        "last_used": "120 days ago (Stale)",
                        "description": "Manage quarterly financial close ticket workflows.",
                    },
                ],
            },
            {
                "app_name": "Google Workspace",
                "category": "Productivity & Collaboration",
                "account_status": "Inactive",
                "total_permissions": 6,
                "permissions": [
                    {
                        "name": "Drive.PayrollConfidential",
                        "privilege_level": "Elevated",
                        "matches_baseline": True,
                        "last_used": "120 days ago (Stale)",
                        "description": "Full access to company-wide payroll projections and sensitive compensation tiers.",
                    },
                ],
            },
            {
                "app_name": "AWS Console",
                "category": "Cloud Infrastructure",
                "account_status": "Inactive",
                "total_permissions": 4,
                "permissions": [
                    {
                        "name": "CostExplorer.ReadWrite",
                        "privilege_level": "Elevated",
                        "matches_baseline": True,
                        "last_used": "120 days ago (Stale)",
                        "description": "View and export raw AWS cloud billing ledgers.",
                    },
                ],
            },
            {
                "app_name": "Slack",
                "category": "Team Communication",
                "account_status": "Inactive",
                "total_permissions": 2,
                "permissions": [
                    {
                        "name": "Channel.StandardUser",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "120 days ago (Stale)",
                        "description": "Standard messaging permissions.",
                    },
                ],
            },
        ],
        "findings": [
            {
                "finding_id": "FIND-1089-1",
                "severity": "Medium",
                "title": "Dormant Privileged Account on Extended Leave",
                "description": "Account inactive for 120 days while retaining active credentials and sensitive payroll drive access.",
                "evidence": "Inactive days = 120 (threshold: 60 days). Sensitive permission count = 7.",
            },
        ],
        "recommendations": [
            {
                "priority": "Immediate",
                "action": "Place Account on Temporary Administrative Suspension",
                "target_app": "Multiple SaaS",
                "rationale": "Dormant accounts holding sensitive compensation sheets represent an unmonitored target for credential theft.",
            },
            {
                "priority": "Informational",
                "action": "Implement Automated IdP Inactivity Suspension Rule",
                "target_app": "Corporate SSO",
                "rationale": "Automatically disable SSO access after 90 days of zero login events.",
            },
        ],
    },

    # Scenario 5: Low-risk employee matching sample baseline (Sam Chen)
    {
        "employee_id": "EMP-1033",
        "aliases": ["showcase_low_001", "sam", "chen"],
        "employee_name": "Sam Chen",
        "department": "Engineering",
        "job_title": "Software Engineer II",
        "manager": "Alex Mercer (Director of Engineering)",
        "employment_status": "Active (Full-Time)",
        "role": "engineer",
        "assigned_applications": [
            {
                "app_name": "GitHub",
                "category": "Source Code Management",
                "account_status": "Active",
                "total_permissions": 4,
                "permissions": [
                    {
                        "name": "Repository.ReadWrite (Scoped Services)",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "Commit and branch on assigned backend microservices.",
                    },
                    {
                        "name": "PR.ReviewAndApprove",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "Standard peer review rights.",
                    },
                ],
            },
            {
                "app_name": "AWS Console",
                "category": "Cloud Infrastructure",
                "account_status": "Active",
                "total_permissions": 3,
                "permissions": [
                    {
                        "name": "CloudWatch.ReadOnly",
                        "privilege_level": "Read-Only",
                        "matches_baseline": True,
                        "last_used": "Yesterday",
                        "description": "View development environment service logs.",
                    },
                ],
            },
            {
                "app_name": "Slack",
                "category": "Team Communication",
                "account_status": "Active",
                "total_permissions": 2,
                "permissions": [
                    {
                        "name": "Channel.StandardUser",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "General communication within engineering channels.",
                    },
                ],
            },
            {
                "app_name": "Jira",
                "category": "Project Management",
                "account_status": "Active",
                "total_permissions": 2,
                "permissions": [
                    {
                        "name": "Jira.Developer",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "Sprint board tracking and issue resolution.",
                    },
                ],
            },
        ],
        "findings": [
            {
                "finding_id": "FIND-1033-1",
                "severity": "Low",
                "title": "Compliant Access Baseline: No Drift Detected",
                "description": "All 11 assigned permissions across 4 applications match the engineering role baseline expectations.",
                "evidence": "Total permissions (11) aligns with expected engineer baseline (12). 0 unneeded administrator privileges.",
            },
        ],
        "recommendations": [
            {
                "priority": "Informational",
                "action": "Maintain Current Access Profile",
                "target_app": "All Systems",
                "rationale": "Employee adheres to principle of least privilege. Re-evaluate during standard annual access certification.",
            },
        ],
    },

    # Scenario 6: Privileged permission expected for role, but requires review (Elena Rostova)
    {
        "employee_id": "EMP-1004",
        "aliases": ["elena", "rostova", "security_architect"],
        "employee_name": "Elena Rostova",
        "department": "Security",
        "job_title": "Lead Cloud Security Architect",
        "manager": "Vikram Patel (CISO)",
        "employment_status": "Active (Full-Time)",
        "role": "security",
        "assigned_applications": [
            {
                "app_name": "AWS Console",
                "category": "Cloud Infrastructure",
                "account_status": "Active",
                "total_permissions": 9,
                "permissions": [
                    {
                        "name": "SecurityAudit",
                        "privilege_level": "Elevated",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "Full read-only audit capability over all cloud configuration and security groups.",
                    },
                    {
                        "name": "GuardDuty.Admin",
                        "privilege_level": "Elevated",
                        "matches_baseline": True,
                        "last_used": "Yesterday",
                        "description": "Configure intelligent threat detection findings and anomaly response.",
                    },
                    {
                        "name": "AdministratorAccess (Emergency Break-Glass)",
                        "privilege_level": "Critical",
                        "matches_baseline": True,
                        "last_used": "2 days ago",
                        "description": "Permanent standing root administrator permission for incident response.",
                    },
                ],
            },
            {
                "app_name": "GitHub",
                "category": "Source Code Management",
                "account_status": "Active",
                "total_permissions": 5,
                "permissions": [
                    {
                        "name": "SecurityAdvisory.Admin",
                        "privilege_level": "Elevated",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "Review secret scanning alerts and Dependabot CVE remediations.",
                    },
                ],
            },
            {
                "app_name": "Google Workspace",
                "category": "Productivity & Collaboration",
                "account_status": "Active",
                "total_permissions": 3,
                "permissions": [
                    {
                        "name": "SecurityInvestigationTool.Viewer",
                        "privilege_level": "Elevated",
                        "matches_baseline": True,
                        "last_used": "3 days ago",
                        "description": "Audit email routing logs and file sharing security events.",
                    },
                ],
            },
            {
                "app_name": "Slack",
                "category": "Team Communication",
                "account_status": "Active",
                "total_permissions": 3,
                "permissions": [
                    {
                        "name": "SecurityChannel.Admin",
                        "privilege_level": "Standard",
                        "matches_baseline": True,
                        "last_used": "Today",
                        "description": "Manage security operations response channels.",
                    },
                ],
            },
        ],
        "findings": [
            {
                "finding_id": "FIND-1004-1",
                "severity": "Medium",
                "title": "Role-Justified Elevated Privilege (Standing AdministratorAccess)",
                "description": "AdministratorAccess is legitimately expected for the Lead Security Architect role, but standing 24/7 access poses blast radius risk.",
                "evidence": "Standing AWS AdministratorAccess attached directly to user rather than via temporary assumed break-glass role.",
            },
        ],
        "recommendations": [
            {
                "priority": "Review Next Sprint",
                "action": "Convert Standing Admin to Just-In-Time (JIT) Assumed Incident Role",
                "target_app": "AWS Console",
                "rationale": "High-impact administrator rights are expected for this role, but should be activated temporarily during verified security incidents with dual approval.",
            },
            {
                "priority": "Informational",
                "action": "Establish Monthly Peer Access Certification",
                "target_app": "Security Operations",
                "rationale": "High-privilege security roles should be cross-reviewed monthly by the CISO.",
            },
        ],
    },
]


def _risk_level_for_score(score: int) -> str:
    if score >= 90:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def _score_risk(findings: list[dict]) -> tuple[int, str, str]:
    """Score only documented findings; application and permission counts are not score inputs."""
    severity_weights = {"Critical": 90, "High": 75, "Medium": 40, "Low": 10}
    highest_severity = max(
        (finding.get("severity", "") for finding in findings),
        key=lambda severity: severity_weights.get(severity, 0),
        default="",
    )

    if not highest_severity:
        return 0, "Low", (
            "No documented risk findings. Severity weights: Critical 90, High 75, "
            "Medium 40, Low 10; each additional finding at the highest severity adds "
            "5 points, capped at 100. Risk levels: Critical 90-100, High 70-89, "
            "Medium 30-69, Low 0-29. Application count and permission count are not score inputs."
        )

    weight = severity_weights[highest_severity]
    finding_count = sum(
        1 for finding in findings if finding.get("severity") == highest_severity
    )
    score = min(100, weight + max(0, finding_count - 1) * 5)
    risk_level = _risk_level_for_score(score)
    extra_findings = max(0, finding_count - 1)
    explanation = (
        f"{finding_count} {highest_severity.lower()}-severity finding(s): "
        f"base score {weight}"
        + (f" plus {extra_findings} additional finding(s) at 5 points each" if extra_findings else "")
        + f"; capped at 100. Only the highest finding severity contributes to the score. "
        + f"Application count and total permission count are not score inputs. "
        + f"Risk levels: Critical 90-100, High 70-89, Medium 30-69, Low 0-29. "
        f"Evidence: {'; '.join(finding.get('evidence', '') for finding in findings if finding.get('severity') == highest_severity)}"
    )
    return score, risk_level, explanation


def _enrich_findings(raw: dict) -> list[dict]:
    """Attach the most directly supported application and permission evidence to each finding."""
    applications = raw["assigned_applications"]
    recommendations = raw["recommendations"]
    enriched = []

    for finding in raw["findings"]:
        searchable = " ".join(
            str(finding.get(key, "")) for key in ("title", "description", "evidence")
        ).casefold()
        is_multi_app_finding = any(
            phrase in searchable for phrase in ("multi-saas", "multiple saas", "across systems")
        )
        matched_app = None if is_multi_app_finding else next(
            (
                app
                for app in applications
                if app["app_name"].casefold() == finding.get("app_name", "").casefold()
                or app["app_name"].casefold() in searchable
                or (app["app_name"] == "AWS Console" and "aws" in searchable)
            ),
            None,
        )
        matched_permission = None
        if matched_app:
            matched_permission = next(
                (
                    permission
                    for permission in matched_app["permissions"]
                    if permission["name"].casefold()
                    == finding.get("permission_name", "").casefold()
                    or permission["name"].casefold() in searchable
                    or permission["name"].split(" (", 1)[0].casefold() in searchable
                ),
                None,
            )
            if matched_permission is None:
                matched_permission = next(
                    (
                        permission
                        for permission in matched_app["permissions"]
                        if any(
                            token in searchable
                            for token in _permission_terms(permission["name"])
                        )
                    ),
                    None,
                )
            if matched_permission is None:
                matched_permission = next(
                    (
                        permission
                        for permission in matched_app["permissions"]
                        if not permission["matches_baseline"]
                    ),
                    None,
                )
        if matched_app is None and not is_multi_app_finding:
            matched_permission_app = next(
                (
                    (app, permission)
                    for app in applications
                    for permission in app["permissions"]
                    if any(
                        token in searchable
                        for token in _permission_terms(permission["name"])
                    )
                ),
                None,
            )
            if matched_permission_app:
                matched_app, matched_permission = matched_permission_app
            elif any(word in searchable for word in ("dormant", "inactive", "stale")):
                inactive_apps = [
                    app["app_name"]
                    for app in applications
                    if app["account_status"] == "Inactive"
                ]
                if inactive_apps:
                    matched_app = {
                        "app_name": ", ".join(inactive_apps)
                    }
            elif any(word in searchable for word in ("baseline", "compliant")):
                matched_app = {"app_name": "All assigned applications"}

        target_app = (
            "Multiple SaaS"
            if is_multi_app_finding
            else matched_app["app_name"] if matched_app else None
        )
        recommendation = next(
            (
                item
                for item in recommendations
                if target_app
                and (
                    item["target_app"].casefold() == target_app.casefold()
                    or item["target_app"].casefold() == "multiple saas"
                    and "," in target_app
                )
            ),
            None,
        )
        severity = finding["severity"]
        if matched_permission and not matched_permission["matches_baseline"]:
            if matched_permission["privilege_level"] == "Critical":
                severity = "Critical"
            elif matched_permission["privilege_level"] == "Elevated" and severity in {"Low", "Medium"}:
                severity = "High"
        enriched.append(
            {
                **finding,
                "severity": severity,
                "app_name": target_app,
                "permission_name": (
                    matched_permission["name"] if matched_permission else None
                ),
                "recommended_action": (
                    recommendation["action"]
                    if recommendation
                    else "Review the cited evidence with the employee's manager and application owner; do not change access without approval."
                ),
            }
        )
    return enriched


def _compute_profile_summary(raw: dict) -> EmployeeScannerProfile:
    """Calculate scores and compile clean profile."""
    role = raw["role"]
    baseline = ROLE_BASELINES.get(role, 8)
    total_perms = sum(app["total_permissions"] for app in raw["assigned_applications"])
    app_count = len(raw["assigned_applications"])
    findings = _enrich_findings(raw)
    risk_score, risk_level, risk_explanation = _score_risk(findings)

    return EmployeeScannerProfile(
        employee_id=raw["employee_id"],
        employee_name=raw["employee_name"],
        department=raw["department"],
        job_title=raw["job_title"],
        manager=raw["manager"],
        employment_status=raw["employment_status"],
        role=role,
        role_baseline_permissions=baseline,
        total_assigned_permissions=total_perms,
        assigned_apps_count=app_count,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_explanation=risk_explanation,
        analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        data_source_status="Demo data — no live identity provider connected.",
        privileged_applications_count=sum(
            1
            for app in raw["assigned_applications"]
            if any(
                permission["privilege_level"] in {"Critical", "Elevated"}
                for permission in app["permissions"]
            )
        ),
        limitations=[
            "All employee and application records are synthetic demonstration fixtures.",
            "No live identity provider or SaaS platform is connected.",
            "Last-used values and role-baseline comparisons are illustrative sample data.",
            "Permission examples may not enumerate every permission included in the reported total.",
            "Findings are decision-support recommendations and require human review.",
        ],
        assigned_applications=raw["assigned_applications"],
        findings=findings,
        recommendations=raw["recommendations"],
    )


# ── Endpoint Handlers ────────────────────────────────────────────────────────

@scanner_router.get("/suggestions", response_model=list[ScannerSuggestion])
def get_scanner_suggestions():
    """Return available synthetic employees for quick search suggestions."""
    suggestions = []
    tags = {
        "EMP-1042": "Excessive Admin (Role Drift)",
        "EMP-1007": "Intern with Org Owner",
        "EMP-1018": "Multi-SaaS Root Admin",
        "EMP-1089": "Dormant (120d Inactive)",
        "EMP-1033": "Baseline Compliant (Low Risk)",
        "EMP-1004": "Privileged Role (Expected Review)",
    }
    for p in SYNTHETIC_PROFILES:
        res = _compute_profile_summary(p)
        suggestions.append(
            ScannerSuggestion(
                employee_id=res.employee_id,
                employee_name=res.employee_name,
                job_title=res.job_title,
                department=res.department,
                risk_level=res.risk_level,
                risk_score=res.risk_score,
                highlight_tag=tags.get(res.employee_id, "Synthetic Profile"),
            )
        )
    return suggestions


def _lookup_employee(employee_id_or_name: str) -> EmployeeScannerProfile:
    """
    Search and analyze an employee by ID or name.
    Returns assigned SaaS applications, permissions, role baseline comparison,
    explainable findings, and recommended review actions.
    """
    query = employee_id_or_name.strip().lower()

    match = None
    for p in SYNTHETIC_PROFILES:
        if p["employee_id"].lower() == query:
            match = p
            break
        if p["employee_name"].lower() == query:
            match = p
            break
        if any(alias in query for alias in p.get("aliases", [])):
            match = p
            break
        if query in p["employee_name"].lower():
            match = p
            break

    if not match:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Synthetic employee '{employee_id_or_name}' not found. "
                "Available synthetic sample IDs: EMP-1042, EMP-1007, EMP-1018, EMP-1089, EMP-1033, EMP-1004."
            ),
        )

    profile = _compute_profile_summary(match)
    get_storage().append_audit_entry(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "employee_scanner",
            "action": "EMPLOYEE_ACCESS_RISK_ANALYSED",
            "details": {
                "employee_id": profile.employee_id,
                "data_source": "synthetic_demo",
                "risk_score": profile.risk_score,
                "risk_level": profile.risk_level,
            },
        }
    )
    return profile


@scanner_router.get("/employees", response_model=EmployeeScannerProfile)
def search_employee(
    query: str = Query(..., min_length=1, max_length=120, description="Employee ID or name"),
):
    """Search the available employee directory by ID or name."""
    query = query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Search query cannot be blank.")
    return _lookup_employee(query)


@scanner_router.get("/employee/{employee_id_or_name}", response_model=EmployeeScannerProfile)
def scan_employee(employee_id_or_name: str):
    """Compatibility route for existing scanner clients."""
    return _lookup_employee(employee_id_or_name)
