/**
 * Synthetic Test Data Fixture for Employee Risk Scanner.
 *
 * Used directly as an ultra-resilient fallback so the feature works smoothly
 * in static/demo environments (such as Vercel) even if the backend is on cold-sleep.
 *
 * DISCLAIMER: All records, roles, and applications are synthetic test scenarios.
 * No real enterprise IdP or SaaS systems are connected.
 */

export const SYNTHETIC_SUGGESTIONS = [
  {
    employee_id: "EMP-1042",
    employee_name: "Jordan Blake",
    job_title: "Senior Growth Marketing Manager",
    department: "Marketing",
    risk_level: "Critical",
    risk_score: 90,
    highlight_tag: "Excessive Admin (Role Drift)",
  },
  {
    employee_id: "EMP-1007",
    employee_name: "Priya Sharma",
    job_title: "Frontend Engineering Intern",
    department: "Engineering",
    risk_level: "Critical",
    risk_score: 90,
    highlight_tag: "Intern with Org Owner",
  },
  {
    employee_id: "EMP-1018",
    employee_name: "Marcus Vance",
    job_title: "Staff DevOps Engineer",
    department: "Engineering",
    risk_level: "High",
    risk_score: 75,
    highlight_tag: "Multi-SaaS Root Admin",
  },
  {
    employee_id: "EMP-1089",
    employee_name: "Carlos Rivera",
    job_title: "Senior Financial Analyst",
    department: "Finance",
    risk_level: "Medium",
    risk_score: 40,
    highlight_tag: "Dormant (120d Inactive)",
  },
  {
    employee_id: "EMP-1033",
    employee_name: "Sam Chen",
    job_title: "Software Engineer II",
    department: "Engineering",
    risk_level: "Low",
    risk_score: 10,
    highlight_tag: "Baseline Compliant (Low Risk)",
  },
  {
    employee_id: "EMP-1004",
    employee_name: "Elena Rostova",
    job_title: "Lead Cloud Security Architect",
    department: "Security",
    risk_level: "Medium",
    risk_score: 40,
    highlight_tag: "Privileged Role (Expected Review)",
  },
];

export const SYNTHETIC_PROFILES_MAP = {
  "EMP-1042": {
    employee_id: "EMP-1042",
    employee_name: "Jordan Blake",
    department: "Marketing",
    job_title: "Senior Growth Marketing Manager",
    manager: "Rachel Green (VP Marketing)",
    employment_status: "Active (Full-Time)",
    role: "marketing",
    role_baseline_permissions: 5,
    total_assigned_permissions: 38,
    assigned_apps_count: 4,
    risk_score: 80,
    risk_level: "High",
    risk_explanation: "2 high-severity findings: base score 75 plus 1 additional finding at 5 points; application count and total permission count are not score inputs.",
    is_synthetic: true,
    notice: "Synthetic test data only. No live identity provider (IdP) or SaaS tenant is connected. All recommendations are decision-support guidelines requiring human administrative approval.",
    assigned_applications: [
      {
        app_name: "AWS Console",
        category: "Cloud Infrastructure",
        account_status: "Active",
        total_permissions: 22,
        permissions: [
          {
            name: "AdministratorAccess",
            privilege_level: "Critical",
            matches_baseline: false,
            last_used: "3 days ago",
            description: "Provides full access to all AWS cloud resources and IAM policies across the organization.",
          },
          {
            name: "BillingFullAccess",
            privilege_level: "Elevated",
            matches_baseline: false,
            last_used: "14 days ago",
            description: "Allows viewing and editing payment methods, invoices, and budgets (lingering from former Finance role).",
          },
          {
            name: "IAMReadOnlyAccess",
            privilege_level: "Standard",
            matches_baseline: false,
            last_used: "5 days ago",
            description: "Allows listing users, groups, and attached policies.",
          },
        ],
      },
      {
        app_name: "Google Workspace",
        category: "Productivity & Collaboration",
        account_status: "Active",
        total_permissions: 8,
        permissions: [
          {
            name: "GoogleDrive.MarketingShared",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "Today",
            description: "Access to marketing collateral, campaign assets, and shared drives.",
          },
          {
            name: "GoogleAnalytics.Admin",
            privilege_level: "Elevated",
            matches_baseline: true,
            last_used: "Yesterday",
            description: "Configuration rights for web traffic tracking and campaign goals.",
          },
        ],
      },
      {
        app_name: "Slack",
        category: "Team Communication",
        account_status: "Active",
        total_permissions: 4,
        permissions: [
          {
            name: "Channel.PostAndInvite",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "Today",
            description: "Standard messaging and channel collaboration.",
          },
        ],
      },
      {
        app_name: "Jira",
        category: "Project Management",
        account_status: "Active",
        total_permissions: 4,
        permissions: [
          {
            name: "Jira.MarketingBoardContributor",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "Yesterday",
            description: "Ticket tracking for campaign sprints.",
          },
        ],
      },
    ],
    findings: [
      {
        finding_id: "FIND-1042-1",
        severity: "High",
        app_name: "AWS Console",
        permission_name: "BillingFullAccess",
        title: "Severe Permission Drift: Lingering Cloud & Billing Admin",
        description: "Employee transferred from Finance to Marketing 8 months ago but retains AWS AdministratorAccess and Billing privileges.",
        evidence: "Marketing role baseline allows max 5 permissions; employee currently holds 38 total permissions (660% above baseline).",
      },
      {
        finding_id: "FIND-1042-2",
        severity: "High",
        title: "Excessive Administrator Rights Outside Job Scope",
        description: "Growth Marketing Manager holds root-level cloud infrastructure modification capabilities.",
        evidence: "AWS Console policy 'AdministratorAccess' assigned directly to user.",
      },
    ],
    recommendations: [
      {
        priority: "Immediate",
        action: "Deprovision AWS AdministratorAccess and BillingFullAccess",
        target_app: "AWS Console",
        rationale: "Marketing responsibilities do not require root cloud administration or financial budget modifications.",
      },
      {
        priority: "Review Next Sprint",
        action: "Transition to Least-Privilege S3 Marketing Viewer role",
        target_app: "AWS Console",
        rationale: "If marketing assets are stored in S3, grant scoped read-only access to specific marketing buckets only.",
      },
    ],
  },

  "EMP-1007": {
    employee_id: "EMP-1007",
    employee_name: "Priya Sharma",
    department: "Engineering",
    job_title: "Frontend Engineering Intern",
    manager: "Alex Mercer (Director of Engineering)",
    employment_status: "Active (Intern)",
    role: "intern",
    role_baseline_permissions: 4,
    total_assigned_permissions: 45,
    assigned_apps_count: 4,
    risk_score: 75,
    risk_level: "High",
    risk_explanation: "1 high-severity finding: base score 75; application count and total permission count are not score inputs.",
    is_synthetic: true,
    notice: "Synthetic test data only. No live identity provider (IdP) or SaaS tenant is connected. All recommendations are decision-support guidelines requiring human administrative approval.",
    assigned_applications: [
      {
        app_name: "GitHub",
        category: "Source Code Management",
        account_status: "Active",
        total_permissions: 28,
        permissions: [
          {
            name: "Organization.Owner",
            privilege_level: "Critical",
            matches_baseline: false,
            last_used: "Today",
            description: "Full administrative ownership over the entire GitHub organization, billing, and member access.",
          },
          {
            name: "Repository.Admin (Production Repos)",
            privilege_level: "Critical",
            matches_baseline: false,
            last_used: "Yesterday",
            description: "Delete branches, bypass branch protection rules, and merge without approvals.",
          },
          {
            name: "Secrets.ReadWrite",
            privilege_level: "Elevated",
            matches_baseline: false,
            last_used: "Today",
            description: "Direct read/write access to CI/CD production deployment tokens.",
          },
        ],
      },
      {
        app_name: "AWS Console",
        category: "Cloud Infrastructure",
        account_status: "Active",
        total_permissions: 12,
        permissions: [
          {
            name: "EC2FullAccess",
            privilege_level: "Elevated",
            matches_baseline: false,
            last_used: "12 days ago",
            description: "Provision, modify, and terminate compute instances.",
          },
        ],
      },
      {
        app_name: "Slack",
        category: "Team Communication",
        account_status: "Active",
        total_permissions: 3,
        permissions: [
          {
            name: "Channel.StandardUser",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "Today",
            description: "General communication within engineering channels.",
          },
        ],
      },
      {
        app_name: "Jira",
        category: "Project Management",
        account_status: "Active",
        total_permissions: 2,
        permissions: [
          {
            name: "Jira.Developer",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "Today",
            description: "Assign and update engineering sprint tickets.",
          },
        ],
      },
    ],
    findings: [
      {
        finding_id: "FIND-1007-1",
        severity: "High",
        title: "Critical Over-Privileged Account: Organization Owner on Intern Account",
        description: "Contract intern assigned Organization.Owner rights on enterprise GitHub tenant.",
        evidence: "Intern baseline allows 4 read/write repo permissions; user currently holds 45 permissions including Org Owner.",
      },
      {
        finding_id: "FIND-1007-2",
        severity: "Medium",
        title: "Unusual Off-Hours Activity & Failed Logins",
        description: "12 off-hours login sessions and 3 failed login attempts recorded within the last 7 days.",
        evidence: "Off-hours count 12 vs intern peer median of 0; failed login spike.",
      },
    ],
    recommendations: [
      {
        priority: "Immediate",
        action: "Revoke GitHub Organization.Owner and Production Repo Admin",
        target_app: "GitHub",
        rationale: "Intern roles require branch-level write access to frontend repositories only, under peer code review.",
      },
      {
        priority: "Immediate",
        action: "Deprovision AWS EC2FullAccess",
        target_app: "AWS Console",
        rationale: "Direct infrastructure provisioning rights are not required for frontend development tasks.",
      },
    ],
  },

  "EMP-1018": {
    employee_id: "EMP-1018",
    employee_name: "Marcus Vance",
    department: "Engineering",
    job_title: "Staff DevOps Engineer",
    manager: "Devon Brooks (VP Infrastructure)",
    employment_status: "Active (Full-Time)",
    role: "engineer",
    role_baseline_permissions: 12,
    total_assigned_permissions: 41,
    assigned_apps_count: 4,
    risk_score: 75,
    risk_level: "High",
    risk_explanation: "1 high-severity finding: base score 75; application count and total permission count are not score inputs.",
    is_synthetic: true,
    notice: "Synthetic test data only. No live identity provider (IdP) or SaaS tenant is connected. All recommendations are decision-support guidelines requiring human administrative approval.",
    assigned_applications: [
      {
        app_name: "AWS Console",
        category: "Cloud Infrastructure",
        account_status: "Active",
        total_permissions: 18,
        permissions: [
          {
            name: "IAM.FullAccess",
            privilege_level: "Critical",
            matches_baseline: false,
            last_used: "Today",
            description: "Can create and attach IAM policies with zero approval gate.",
          },
          {
            name: "KMS.DecryptAll",
            privilege_level: "Critical",
            matches_baseline: false,
            last_used: "Today",
            description: "Unrestricted key decryption for production data stores.",
          },
        ],
      },
      {
        app_name: "GitHub",
        category: "Source Code Management",
        account_status: "Active",
        total_permissions: 14,
        permissions: [
          {
            name: "Organization.Owner",
            privilege_level: "Critical",
            matches_baseline: false,
            last_used: "Today",
            description: "Full administrative ownership over GitHub repositories.",
          },
        ],
      },
      {
        app_name: "Slack",
        category: "Team Communication",
        account_status: "Active",
        total_permissions: 5,
        permissions: [
          {
            name: "Primary.Owner",
            privilege_level: "Critical",
            matches_baseline: false,
            last_used: "Yesterday",
            description: "Can export corporate communication archives and manage billing.",
          },
        ],
      },
      {
        app_name: "Google Workspace",
        category: "Productivity & Collaboration",
        account_status: "Active",
        total_permissions: 4,
        permissions: [
          {
            name: "SuperAdmin.Delegated",
            privilege_level: "Critical",
            matches_baseline: false,
            last_used: "3 days ago",
            description: "Full domain administrator privileges over enterprise mail and storage.",
          },
        ],
      },
    ],
    findings: [
      {
        finding_id: "FIND-1018-1",
        severity: "High",
        title: "Toxic Combination: Simultaneous Multi-SaaS Root Administration",
        description: "User holds highest privilege level across AWS (IAM Full), GitHub (Org Owner), Slack (Primary Owner), and Google Workspace (SuperAdmin).",
        evidence: "Single identity credential represents catastrophic blast radius across identity, code, cloud, and communication.",
      },
    ],
    recommendations: [
      {
        priority: "Immediate",
        action: "Enforce Separation of Duties",
        target_app: "Multiple SaaS",
        rationale: "Transfer Slack Primary Owner and Google Workspace SuperAdmin to dedicated Corporate IT; maintain AWS and GitHub for DevOps.",
      },
      {
        priority: "Review Next Sprint",
        action: "Migrate standing IAM.FullAccess to Just-In-Time (JIT) Break-Glass Role",
        target_app: "AWS Console",
        rationale: "Standing root-equivalent rights should be replaced with time-bound STS assumed sessions requiring MFA.",
      },
    ],
  },

  "EMP-1089": {
    employee_id: "EMP-1089",
    employee_name: "Carlos Rivera",
    department: "Finance",
    job_title: "Senior Financial Analyst",
    manager: "Linda Zhao (Corporate Controller)",
    employment_status: "On Leave (Parental/Sabbatical)",
    role: "analyst",
    role_baseline_permissions: 8,
    total_assigned_permissions: 16,
    assigned_apps_count: 4,
    risk_score: 40,
    risk_level: "Medium",
    risk_explanation: "1 medium-severity finding: base score 40; application count and total permission count are not score inputs.",
    is_synthetic: true,
    notice: "Synthetic test data only. No live identity provider (IdP) or SaaS tenant is connected. All recommendations are decision-support guidelines requiring human administrative approval.",
    assigned_applications: [
      {
        app_name: "Jira",
        category: "Project Management",
        account_status: "Inactive",
        total_permissions: 4,
        permissions: [
          {
            name: "FinanceBoard.Admin",
            privilege_level: "Elevated",
            matches_baseline: true,
            last_used: "120 days ago (Stale)",
            description: "Manage quarterly financial close ticket workflows.",
          },
        ],
      },
      {
        app_name: "Google Workspace",
        category: "Productivity & Collaboration",
        account_status: "Inactive",
        total_permissions: 6,
        permissions: [
          {
            name: "Drive.PayrollConfidential",
            privilege_level: "Elevated",
            matches_baseline: true,
            last_used: "120 days ago (Stale)",
            description: "Full access to company-wide payroll projections and sensitive compensation tiers.",
          },
        ],
      },
      {
        app_name: "AWS Console",
        category: "Cloud Infrastructure",
        account_status: "Inactive",
        total_permissions: 4,
        permissions: [
          {
            name: "CostExplorer.ReadWrite",
            privilege_level: "Elevated",
            matches_baseline: true,
            last_used: "120 days ago (Stale)",
            description: "View and export raw AWS cloud billing ledgers.",
          },
        ],
      },
      {
        app_name: "Slack",
        category: "Team Communication",
        account_status: "Inactive",
        total_permissions: 2,
        permissions: [
          {
            name: "Channel.StandardUser",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "120 days ago (Stale)",
            description: "Standard messaging permissions.",
          },
        ],
      },
    ],
    findings: [
      {
        finding_id: "FIND-1089-1",
        severity: "Medium",
        title: "Dormant Privileged Account on Extended Leave",
        description: "Account inactive for 120 days while retaining active credentials and sensitive payroll drive access.",
        evidence: "Inactive days = 120 (threshold: 60 days). Sensitive permission count = 7.",
      },
    ],
    recommendations: [
      {
        priority: "Immediate",
        action: "Place Account on Temporary Administrative Suspension",
        target_app: "Multiple SaaS",
        rationale: "Dormant accounts holding sensitive compensation sheets represent an unmonitored target for credential theft.",
      },
      {
        priority: "Informational",
        action: "Implement Automated IdP Inactivity Suspension Rule",
        target_app: "Corporate SSO",
        rationale: "Automatically disable SSO access after 90 days of zero login events.",
      },
    ],
  },

  "EMP-1033": {
    employee_id: "EMP-1033",
    employee_name: "Sam Chen",
    department: "Engineering",
    job_title: "Software Engineer II",
    manager: "Alex Mercer (Director of Engineering)",
    employment_status: "Active (Full-Time)",
    role: "engineer",
    role_baseline_permissions: 12,
    total_assigned_permissions: 11,
    assigned_apps_count: 4,
    risk_score: 10,
    risk_level: "Low",
    risk_explanation: "1 low-severity finding: base score 10; application count and total permission count are not score inputs.",
    is_synthetic: true,
    notice: "Synthetic test data only. No live identity provider (IdP) or SaaS tenant is connected. All recommendations are decision-support guidelines requiring human administrative approval.",
    assigned_applications: [
      {
        app_name: "GitHub",
        category: "Source Code Management",
        account_status: "Active",
        total_permissions: 4,
        permissions: [
          {
            name: "Repository.ReadWrite (Scoped Services)",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "Today",
            description: "Commit and branch on assigned backend microservices.",
          },
          {
            name: "PR.ReviewAndApprove",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "Today",
            description: "Standard peer review rights.",
          },
        ],
      },
      {
        app_name: "AWS Console",
        category: "Cloud Infrastructure",
        account_status: "Active",
        total_permissions: 3,
        permissions: [
          {
            name: "CloudWatch.ReadOnly",
            privilege_level: "Read-Only",
            matches_baseline: true,
            last_used: "Yesterday",
            description: "View development environment service logs.",
          },
        ],
      },
      {
        app_name: "Slack",
        category: "Team Communication",
        account_status: "Active",
        total_permissions: 2,
        permissions: [
          {
            name: "Channel.StandardUser",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "Today",
            description: "General communication within engineering channels.",
          },
        ],
      },
      {
        app_name: "Jira",
        category: "Project Management",
        account_status: "Active",
        total_permissions: 2,
        permissions: [
          {
            name: "Jira.Developer",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "Today",
            description: "Sprint board tracking and issue resolution.",
          },
        ],
      },
    ],
    findings: [
      {
        finding_id: "FIND-1033-1",
        severity: "Low",
        title: "Compliant Access Baseline: No Drift Detected",
        description: "All 11 assigned permissions across 4 applications match the engineering role baseline expectations.",
        evidence: "Total permissions (11) aligns with expected engineer baseline (12). 0 unneeded administrator privileges.",
      },
    ],
    recommendations: [
      {
        priority: "Informational",
        action: "Maintain Current Access Profile",
        target_app: "All Systems",
        rationale: "Employee adheres to principle of least privilege. Re-evaluate during standard annual access certification.",
      },
    ],
  },

  "EMP-1004": {
    employee_id: "EMP-1004",
    employee_name: "Elena Rostova",
    department: "Security",
    job_title: "Lead Cloud Security Architect",
    manager: "Vikram Patel (CISO)",
    employment_status: "Active (Full-Time)",
    role: "security",
    role_baseline_permissions: 18,
    total_assigned_permissions: 20,
    assigned_apps_count: 4,
    risk_score: 40,
    risk_level: "Medium",
    risk_explanation: "1 medium-severity finding: base score 40; application count and total permission count are not score inputs.",
    is_synthetic: true,
    notice: "Synthetic test data only. No live identity provider (IdP) or SaaS tenant is connected. All recommendations are decision-support guidelines requiring human administrative approval.",
    assigned_applications: [
      {
        app_name: "AWS Console",
        category: "Cloud Infrastructure",
        account_status: "Active",
        total_permissions: 9,
        permissions: [
          {
            name: "SecurityAudit",
            privilege_level: "Elevated",
            matches_baseline: true,
            last_used: "Today",
            description: "Full read-only audit capability over all cloud configuration and security groups.",
          },
          {
            name: "GuardDuty.Admin",
            privilege_level: "Elevated",
            matches_baseline: true,
            last_used: "Yesterday",
            description: "Configure intelligent threat detection findings and anomaly response.",
          },
          {
            name: "AdministratorAccess (Emergency Break-Glass)",
            privilege_level: "Critical",
            matches_baseline: true,
            last_used: "2 days ago",
            description: "Permanent standing root administrator permission for incident response.",
          },
        ],
      },
      {
        app_name: "GitHub",
        category: "Source Code Management",
        account_status: "Active",
        total_permissions: 5,
        permissions: [
          {
            name: "SecurityAdvisory.Admin",
            privilege_level: "Elevated",
            matches_baseline: true,
            last_used: "Today",
            description: "Review secret scanning alerts and Dependabot CVE remediations.",
          },
        ],
      },
      {
        app_name: "Google Workspace",
        category: "Productivity & Collaboration",
        account_status: "Active",
        total_permissions: 3,
        permissions: [
          {
            name: "SecurityInvestigationTool.Viewer",
            privilege_level: "Elevated",
            matches_baseline: true,
            last_used: "3 days ago",
            description: "Audit email routing logs and file sharing security events.",
          },
        ],
      },
      {
        app_name: "Slack",
        category: "Team Communication",
        account_status: "Active",
        total_permissions: 3,
        permissions: [
          {
            name: "SecurityChannel.Admin",
            privilege_level: "Standard",
            matches_baseline: true,
            last_used: "Today",
            description: "Manage security operations response channels.",
          },
        ],
      },
    ],
    findings: [
      {
        finding_id: "FIND-1004-1",
        severity: "Medium",
        title: "Role-Justified Elevated Privilege (Standing AdministratorAccess)",
        description: "AdministratorAccess is legitimately expected for the Lead Security Architect role, but standing 24/7 access poses blast radius risk.",
        evidence: "Standing AWS AdministratorAccess attached directly to user rather than via temporary assumed break-glass role.",
      },
    ],
    recommendations: [
      {
        priority: "Review Next Sprint",
        action: "Convert Standing Admin to Just-In-Time (JIT) Assumed Incident Role",
        target_app: "AWS Console",
        rationale: "High-impact administrator rights are expected for this role, but should be activated temporarily during verified security incidents with dual approval.",
      },
      {
        priority: "Informational",
        action: "Establish Monthly Peer Access Certification",
        target_app: "Security Operations",
        rationale: "High-privilege security roles should be cross-reviewed monthly by the CISO.",
      },
    ],
  },
};

/**
 * Client-side query search function to ensure instantaneous fallback
 */
function scoreSyntheticProfile(profile) {
  const severityWeights = { Critical: 90, High: 75, Medium: 40, Low: 10 };
  const findings = profile.findings.map((finding) => {
    const searchable = [finding.title, finding.description, finding.evidence]
      .join(' ')
      .toLowerCase();
    const multiApp = ['multi-saas', 'multiple saas', 'across systems'].some((phrase) =>
      searchable.includes(phrase)
    );
    let app = multiApp
      ? null
      : profile.assigned_applications.find(
          (candidate) =>
            candidate.app_name.toLowerCase() === (finding.app_name || '').toLowerCase() ||
            searchable.includes(candidate.app_name.toLowerCase()) ||
            (candidate.app_name === 'AWS Console' && searchable.includes('aws'))
        );
    let permission;
    if (app) {
      permission =
        app.permissions.find(
          (candidate) =>
            candidate.name.toLowerCase() === (finding.permission_name || '').toLowerCase()
        ) ||
        app.permissions.find((candidate) =>
          searchable.includes(candidate.name.toLowerCase()) ||
          searchable.includes(candidate.name.split(' (', 1)[0].toLowerCase())
        ) ||
        app.permissions.find((candidate) => {
          const tokens = candidate.name
            .replace(/([a-z])([A-Z])/g, '$1 $2')
            .replace(/[.(]/g, ' ')
            .split(/\s+/)
            .filter((token) => token.length >= 5);
          return tokens.some((token) => searchable.includes(token.toLowerCase()));
        }) ||
        app.permissions.find((candidate) => !candidate.matches_baseline);
    }
    if (!app && !multiApp) {
      for (const candidate of profile.assigned_applications) {
        const matchingPermission = candidate.permissions.find((entry) => {
          const tokens = entry.name
            .replace(/([a-z])([A-Z])/g, '$1 $2')
            .replace(/[.(]/g, ' ')
            .split(/\s+/)
            .filter((token) => token.length >= 5);
          return tokens.some((token) => searchable.includes(token.toLowerCase()));
        });
        if (matchingPermission) {
          app = candidate;
          permission = matchingPermission;
          break;
        }
      }
    }
    if (!app && !multiApp && /(dormant|inactive|stale)/.test(searchable)) {
      const inactiveApps = profile.assigned_applications
        .filter((candidate) => candidate.account_status === 'Inactive')
        .map((candidate) => candidate.app_name);
      if (inactiveApps.length) app = { app_name: inactiveApps.join(', ') };
    } else if (!app && !multiApp && /(baseline|compliant)/.test(searchable)) {
      app = { app_name: 'All assigned applications' };
    }
    const appName = multiApp ? 'Multiple SaaS' : app?.app_name || null;
    const recommendation = profile.recommendations.find(
      (candidate) =>
        appName &&
        (candidate.target_app.toLowerCase() === appName.toLowerCase() ||
          (candidate.target_app.toLowerCase() === 'multiple saas' && appName.includes(',')))
    );
    let severity = finding.severity;
    if (permission && !permission.matches_baseline) {
      if (permission.privilege_level === 'Critical') severity = 'Critical';
      else if (
        permission.privilege_level === 'Elevated' &&
        ['Low', 'Medium'].includes(severity)
      ) {
        severity = 'High';
      }
    }
    return {
      ...finding,
      severity,
      app_name: appName,
      permission_name: permission?.name || null,
      recommended_action:
        recommendation?.action ||
        "Review the cited evidence with the employee's manager and application owner; do not change access without approval.",
    };
  });
  const highestSeverity = findings.reduce(
    (highest, finding) =>
      (severityWeights[finding.severity] || 0) > (severityWeights[highest] || 0)
        ? finding.severity
        : highest,
    ''
  );
  const matchingFindings = findings.filter(
    (finding) => finding.severity === highestSeverity
  );
  const weight = severityWeights[highestSeverity] || 0;
  const extraFindings = Math.max(0, matchingFindings.length - 1);
  const risk_score = Math.min(100, weight + extraFindings * 5);
  const risk_level =
    risk_score >= 90
      ? 'Critical'
      : risk_score >= 70
      ? 'High'
      : risk_score >= 30
      ? 'Medium'
      : 'Low';
  const explanation = highestSeverity
    ? `${matchingFindings.length} ${highestSeverity.toLowerCase()}-severity finding(s): ` +
      `base score ${weight}` +
      (extraFindings ? ` plus ${extraFindings} additional finding(s) at 5 points each` : '') +
      `; capped at 100. Only the highest finding severity contributes to the score. ` +
      `Application count and total permission count are not score inputs. ` +
      `Risk levels: Critical 90-100, High 70-89, Medium 30-69, Low 0-29. ` +
      `Evidence: ${matchingFindings.map((finding) => finding.evidence).join('; ')}`
    : 'No documented risk findings. Severity weights: Critical 90, High 75, Medium 40, Low 10; each additional finding at the highest severity adds 5 points, capped at 100. Risk levels: Critical 90-100, High 70-89, Medium 30-69, Low 0-29. Application count and permission count are not score inputs.';

  return {
    ...profile,
    risk_score,
    risk_level,
    risk_explanation: explanation,
    analysis_timestamp: new Date().toISOString(),
    data_source_status: 'Demo data — no live identity provider connected.',
    privileged_applications_count: profile.assigned_applications.filter((app) =>
      app.permissions.some((permission) =>
        ['Critical', 'Elevated'].includes(permission.privilege_level)
      )
    ).length,
    limitations: [
      'All employee and application records are synthetic demonstration fixtures.',
      'No live identity provider or SaaS platform is connected.',
      'Last-used values and role-baseline comparisons are illustrative sample data.',
      'Permission examples may not enumerate every permission included in the reported total.',
      'Findings are decision-support recommendations and require human review.',
    ],
    findings,
  };
}

export function searchSyntheticProfile(query) {
  if (!query) return null;
  const q = query.trim().toLowerCase();

  // Direct match by ID
  for (const [id, profile] of Object.entries(SYNTHETIC_PROFILES_MAP)) {
    if (id.toLowerCase() === q) return scoreSyntheticProfile(profile);
  }

  // Match by Name
  for (const profile of Object.values(SYNTHETIC_PROFILES_MAP)) {
    if (profile.employee_name.toLowerCase().includes(q)) return scoreSyntheticProfile(profile);
  }

  // Match showcase / alias
  if (q.includes("jordan") || q.includes("blake") || q.includes("high_001")) return scoreSyntheticProfile(SYNTHETIC_PROFILES_MAP["EMP-1042"]);
  if (q.includes("priya") || q.includes("sharma") || q.includes("high_002")) return scoreSyntheticProfile(SYNTHETIC_PROFILES_MAP["EMP-1007"]);
  if (q.includes("marcus") || q.includes("vance") || q.includes("devops")) return scoreSyntheticProfile(SYNTHETIC_PROFILES_MAP["EMP-1018"]);
  if (q.includes("carlos") || q.includes("rivera") || q.includes("med_001")) return scoreSyntheticProfile(SYNTHETIC_PROFILES_MAP["EMP-1089"]);
  if (q.includes("sam") || q.includes("chen") || q.includes("low_001")) return scoreSyntheticProfile(SYNTHETIC_PROFILES_MAP["EMP-1033"]);
  if (q.includes("elena") || q.includes("rostova") || q.includes("architect")) return scoreSyntheticProfile(SYNTHETIC_PROFILES_MAP["EMP-1004"]);

  return null;
}
