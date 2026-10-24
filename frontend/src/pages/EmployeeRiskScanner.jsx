import React, { useState, useEffect } from 'react';
import {
  Search,
  ShieldAlert,
  AlertTriangle,
  Building,
  Briefcase,
  UserCheck,
  Layers,
  CheckCircle,
  XCircle,
  Clock,
  Info,
  Lock,
} from 'lucide-react';
import { api } from '../api';
import {
  SYNTHETIC_SUGGESTIONS,
  searchSyntheticProfile,
} from '../data/syntheticScannerData';

const isValidSuggestionList = (value) =>
  Array.isArray(value) &&
  value.length > 0 &&
  value.every(
    (item) =>
      item &&
      typeof item.employee_id === 'string' &&
      typeof item.employee_name === 'string' &&
      typeof item.job_title === 'string' &&
      typeof item.department === 'string' &&
      ['Low', 'Medium', 'High', 'Critical'].includes(item.risk_level) &&
      Number.isInteger(item.risk_score) &&
      item.risk_score >= 0 &&
      item.risk_score <= 100
  );

const isValidProfile = (value) =>
  value &&
  typeof value === 'object' &&
  value.is_synthetic === true &&
  typeof value.data_source_status === 'string' &&
  typeof value.analysis_timestamp === 'string' &&
  Number.isInteger(value.privileged_applications_count) &&
  Array.isArray(value.limitations) &&
  typeof value.employee_id === 'string' &&
  typeof value.employee_name === 'string' &&
  typeof value.job_title === 'string' &&
  typeof value.manager === 'string' &&
  typeof value.role === 'string' &&
  typeof value.department === 'string' &&
  typeof value.employment_status === 'string' &&
  typeof value.risk_explanation === 'string' &&
  Number.isInteger(value.risk_score) &&
  value.risk_score >= 0 &&
  value.risk_score <= 100 &&
  ['Low', 'Medium', 'High', 'Critical'].includes(value.risk_level) &&
  Array.isArray(value.assigned_applications) &&
  value.assigned_applications.every(
    (app) =>
      app &&
      typeof app.app_name === 'string' &&
      typeof app.category === 'string' &&
      typeof app.account_status === 'string' &&
      Number.isInteger(app.total_permissions) &&
      Array.isArray(app.permissions) &&
      app.permissions.every(
        (permission) =>
          permission &&
          typeof permission.name === 'string' &&
          typeof permission.privilege_level === 'string' &&
          typeof permission.matches_baseline === 'boolean' &&
          typeof permission.last_used === 'string' &&
          typeof permission.description === 'string'
      )
  ) &&
  Array.isArray(value.findings) &&
  value.findings.every(
    (finding) =>
      finding &&
      typeof finding.finding_id === 'string' &&
      typeof finding.severity === 'string' &&
      typeof finding.title === 'string' &&
      typeof finding.description === 'string' &&
      typeof finding.evidence === 'string' &&
      typeof finding.recommended_action === 'string'
  ) &&
  Array.isArray(value.recommendations) &&
  value.recommendations.every(
    (recommendation) =>
      recommendation &&
      typeof recommendation.priority === 'string' &&
      typeof recommendation.action === 'string' &&
      typeof recommendation.target_app === 'string' &&
      typeof recommendation.rationale === 'string'
  );

export default function EmployeeRiskScanner() {
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState(null);
  const [suggestions, setSuggestions] = useState(SYNTHETIC_SUGGESTIONS);
  const [profileSource, setProfileSource] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    async function fetchSuggestions() {
      try {
        const apiSuggestions = await api.getScannerSuggestions();
        if (isValidSuggestionList(apiSuggestions)) {
          setSuggestions(apiSuggestions);
        }
      } catch (e) {
        setSuggestions(SYNTHETIC_SUGGESTIONS);
      }
    }
    fetchSuggestions();
  }, []);

  const handleSearch = async (queryToUse) => {
    const q = (queryToUse !== undefined ? queryToUse : searchQuery).trim();
    if (!q) {
      setProfile(null);
      setErrorMessage('Please enter an employee ID (e.g. EMP-1042) or employee name.');
      return;
    }

    setLoading(true);
    setShowSuggestions(false);
    setErrorMessage('');

    try {
      const res = await api.scanEmployee(q);
      if (!isValidProfile(res)) {
        throw new Error('The scanner returned an invalid profile response.');
      }
      setProfile(res);
      setProfileSource('Synthetic backend dataset');
    } catch (apiErr) {
      const localMatch = searchSyntheticProfile(q);
      if (localMatch) {
        setProfile(localMatch);
        setProfileSource('Local synthetic fallback');
      } else {
        setProfile(null);
        setProfileSource('Local synthetic fallback');
        setErrorMessage(
          `No synthetic record found matching "${q}". Please try one of the suggested synthetic employee IDs below.`
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!profile) return;
    const quote = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
    const rows = [
      ['Employee Access Risk Report', ''],
      ['Employee ID', profile.employee_id],
      ['Employee name', profile.employee_name],
      ['Department', profile.department],
      ['Job title', profile.job_title],
      ['Manager', profile.manager],
      ['Data source', profile.data_source_status || profile.notice],
      ['Analysis timestamp', profile.analysis_timestamp],
      ['Applications assigned', profile.assigned_apps_count],
      ['Privileged applications', profile.privileged_applications_count],
      ['Risk score', `${profile.risk_score}/100`],
      ['Risk level', profile.risk_level],
      ['Score explanation', profile.risk_explanation],
      [],
      ['Application', 'Access status', 'Permission', 'Privilege level', 'Role baseline match', 'Last used', 'Description'],
      ...profile.assigned_applications.flatMap((app) =>
        app.permissions.map((permission) => [
          app.app_name,
          app.account_status,
          permission.name,
          permission.privilege_level,
          permission.matches_baseline ? 'Yes' : 'No',
          permission.last_used,
          permission.description,
        ])
      ),
      [],
      ['Finding severity', 'Finding', 'Application', 'Permission', 'Evidence', 'Recommended action'],
      ...profile.findings.map((finding) => [
        finding.severity,
        finding.title,
        finding.app_name || '',
        finding.permission_name || '',
        finding.evidence,
        finding.recommended_action,
      ]),
      [],
      ['Recommendation priority', 'Recommended action', 'Target application', 'Rationale'],
      ...profile.recommendations.map((recommendation) => [
        recommendation.priority,
        recommendation.action,
        recommendation.target_app,
        recommendation.rationale,
      ]),
      [],
      ['Limitations'],
      ...(profile.limitations || []).map((limitation) => [limitation]),
    ];
    const csv = rows.map((row) => row.map(quote).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `access-risk-${profile.employee_id}.csv`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const handleSelectSuggestion = (empId) => {
    setSearchQuery(empId);
    setShowSuggestions(false);
    handleSearch(empId);
  };

  const matchingSuggestions = suggestions.filter((suggestion) => {
    const query = searchQuery.trim().toLowerCase();
    return (
      query &&
      `${suggestion.employee_id} ${suggestion.employee_name} ${suggestion.job_title || ''}`
        .toLowerCase()
        .includes(query)
    );
  });

  return (
    <div>
      {/* ── Security & Synthetic Disclaimer Banner ───────── */}
      <div
        className="alert-banner"
        style={{
          borderLeft: '4px solid #f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.08)',
          color: '#fef3c7',
          marginBottom: '22px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <AlertTriangle size={20} style={{ color: '#fbbf24', flexShrink: 0, marginTop: '2px' }} />
          <div style={{ fontSize: '13px', lineHeight: 1.6 }}>
            <strong style={{ color: '#fbbf24' }}>Demo data — no live identity provider connected.</strong>{' '}
            Employee profiles, assignments, and access evidence are synthetic fixtures, not records fetched from Microsoft 365, Slack, GitHub, AWS, Jira, Salesforce, or a live identity provider. Findings are read-only recommendations and require human approval.
          </div>
        </div>
      </div>

      {/* ── Search & Suggestions Card ────────────────────── */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Search size={18} color="var(--accent-cyan)" />
            <span>Search Employee Access Records</span>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Search by employee ID or name
          </span>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}
        >
          <div style={{ position: 'relative', flex: 1 }}>
            <Search
              size={16}
              style={{ position: 'absolute', left: '14px', top: '12px', color: 'var(--text-muted)' }}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              placeholder="Enter an employee ID or name"
              style={{ width: '100%', paddingLeft: '40px', paddingRight: '12px', height: '42px', fontSize: '14px' }}
            />
            {showSuggestions && matchingSuggestions.length > 0 && (
              <div
                role="listbox"
                aria-label="Synthetic employee suggestions"
                style={{
                  position: 'absolute',
                  zIndex: 5,
                  top: '46px',
                  left: 0,
                  right: 0,
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
                }}
              >
                {matchingSuggestions.slice(0, 6).map((suggestion) => (
                  <button
                    key={suggestion.employee_id}
                    type="button"
                    role="option"
                    aria-selected={false}
                    onClick={() => handleSelectSuggestion(suggestion.employee_id)}
                    style={{
                      width: '100%',
                      display: 'flex',
                      justifyContent: 'space-between',
                      gap: '12px',
                      padding: '10px 12px',
                      border: 0,
                      borderBottom: '1px solid var(--border-color)',
                      background: 'transparent',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <span>
                      <strong>{suggestion.employee_name}</strong>{' '}
                      <span className="mono" style={{ color: 'var(--accent-cyan)' }}>
                        {suggestion.employee_id}
                      </span>
                    </span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                      {suggestion.department}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ padding: '0 24px', height: '42px' }}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {/* Suggestion Chips */}
        <div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: 600 }}>
            Quick Sample Profiles for Evaluation:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {suggestions.map((s) => (
              <button
                key={s.employee_id}
                type="button"
                onClick={() => handleSelectSuggestion(s.employee_id)}
                className="btn btn-secondary btn-sm"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  backgroundColor:
                    profile && profile.employee_id === s.employee_id
                      ? 'rgba(6, 182, 212, 0.15)'
                      : 'var(--bg-input)',
                  borderColor:
                    profile && profile.employee_id === s.employee_id
                      ? 'var(--accent-cyan)'
                      : 'var(--border-color)',
                }}
              >
                <span className="mono" style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>
                  {s.employee_id}
                </span>
                <span>{s.employee_name}</span>
                <span
                  style={{
                    fontSize: '10px',
                    padding: '1px 6px',
                    borderRadius: '4px',
                    backgroundColor:
                      s.risk_level === 'Critical' || s.risk_level === 'High'
                        ? 'rgba(239, 68, 68, 0.2)'
                        : s.risk_level === 'Medium'
                        ? 'rgba(245, 158, 11, 0.2)'
                        : 'rgba(16, 185, 129, 0.2)',
                    color:
                      s.risk_level === 'Critical' || s.risk_level === 'High'
                        ? '#f87171'
                        : s.risk_level === 'Medium'
                        ? '#fbbf24'
                        : '#34d399',
                  }}
                >
                  {s.highlight_tag || s.risk_level}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading && (
        <div className="card" role="status" style={{ marginBottom: '24px', color: 'var(--text-secondary)' }}>
          Searching the employee directory and analysing available synthetic access evidence...
        </div>
      )}

      {/* ── Error State ──────────────────────────────────── */}
      {errorMessage && (
        <div
          style={{
            padding: '16px 20px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--risk-high-bg)',
            border: '1px solid var(--risk-high-border)',
            color: 'var(--risk-high-text)',
            marginBottom: '24px',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <XCircle size={20} />
          <span>{errorMessage}</span>
        </div>
      )}

      {!loading && !profile && !errorMessage && (
        <div className="card" style={{ marginBottom: '24px', textAlign: 'center', padding: '30px' }}>
          <Search size={24} color="var(--accent-cyan)" style={{ marginBottom: '10px' }} />
          <h2 style={{ fontSize: '17px', marginBottom: '8px' }}>Search for an employee to begin</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
            Enter an employee ID or name, or select one of the synthetic demo profiles above. No CSV upload is needed.
          </p>
        </div>
      )}

      {/* ── Employee Profile & Findings ──────────────────── */}
      {profile && (
        <div>
          {/* Header Card: Employee Profile & Risk Score */}
          <div className="card" style={{ padding: '22px 24px', marginBottom: '24px' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '24px',
                alignItems: 'center',
              }}
            >
              {/* Profile Details */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                  <h2 style={{ fontSize: '22px', fontWeight: 800 }}>{profile.employee_name}</h2>
                  <span className="mono" style={{ color: 'var(--accent-cyan)', fontSize: '14px', fontWeight: 700 }}>
                    ({profile.employee_id})
                  </span>
                  <span
                    className={`badge ${
                      profile.risk_level === 'Critical' || profile.risk_level === 'High'
                        ? 'badge-high'
                        : profile.risk_level === 'Medium'
                        ? 'badge-medium'
                        : 'badge-low'
                    }`}
                  >
                    {profile.risk_level} Risk
                  </span>
                </div>
                <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-muted)' }}>
                  {profile.data_source_status || profile.notice}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Briefcase size={14} color="var(--text-muted)" />
                    <span style={{ color: '#fff', fontWeight: 600 }}>{profile.job_title}</span>
                    <span>•</span>
                    <Building size={14} color="var(--text-muted)" />
                    <span>{profile.department}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <UserCheck size={14} color="var(--text-muted)" />
                    <span>Manager: {profile.manager}</span>
                    <span>•</span>
                    <span>Role: {profile.role}</span>
                    <span>•</span>
                    <span
                      style={{
                        color: profile.employment_status.includes('Leave') ? '#fbbf24' : '#34d399',
                      }}
                    >
                      {profile.employment_status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Risk Score & Baseline Metrics */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: '20px',
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ textAlign: 'center', background: 'var(--bg-primary)', padding: '12px 18px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Assigned SaaS Apps
                  </div>
                  <div className="mono" style={{ fontSize: '22px', fontWeight: 800, color: '#fff' }}>
                    {profile.assigned_apps_count}
                  </div>
                </div>

                <div style={{ textAlign: 'center', background: 'var(--bg-primary)', padding: '12px 18px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Privileged Apps
                  </div>
                  <div className="mono" style={{ fontSize: '22px', fontWeight: 800, color: '#fbbf24' }}>
                    {profile.privileged_applications_count}
                  </div>
                </div>

                <div style={{ textAlign: 'center', background: 'var(--bg-primary)', padding: '12px 18px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Role Baseline vs Actual
                  </div>
                  <div className="mono" style={{ fontSize: '18px', fontWeight: 700 }}>
                    <span
                      style={{
                        color:
                          profile.total_assigned_permissions > profile.role_baseline_permissions * 1.5
                            ? '#f87171'
                            : '#34d399',
                      }}
                    >
                      {profile.total_assigned_permissions}
                    </span>{' '}
                    <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                      / {profile.role_baseline_permissions} expected
                    </span>
                  </div>
                </div>

                <div style={{ textAlign: 'center', background: 'var(--bg-primary)', padding: '12px 20px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Access Risk Score
                  </div>
                  <div
                    className="mono"
                    style={{
                      fontSize: '26px',
                      fontWeight: 800,
                      color:
                        profile.risk_score >= 70
                          ? '#f87171'
                          : profile.risk_score >= 40
                          ? '#fbbf24'
                          : '#34d399',
                    }}
                  >
                    {profile.risk_score}/100
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
                  <button type="button" onClick={downloadReport} className="btn btn-secondary btn-sm">
                    Download Employee Risk Report (CSV)
                  </button>
                </div>
              </div>
            </div>

            <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Info size={14} color="var(--accent-cyan)" />
              <span>
                Risk evaluation principle: The score uses the severity and count of documented, evidence-backed findings. Assigned application count and total permission count alone are not score inputs; each permission is compared with the synthetic role baseline.
              </span>
            </div>
            <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-muted)' }}>
              Documented synthetic role baselines: Marketing 5, Intern 4, Engineer 12, Analyst 8, and Security 18 total permissions. Individual permission match indicators compare assignments to that role baseline; app count alone is not scored.
            </div>
            <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              <strong>Score explanation:</strong>{' '}
              {profile.risk_explanation || 'Risk score is based on the severity and count of documented findings; assigned application count and total permission count are not score inputs.'}
              <span style={{ marginLeft: '10px', color: 'var(--text-muted)' }}>
                Data source: {profileSource}
              </span>
            </div>
            <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-muted)' }}>
              Analysis timestamp: {profile.analysis_timestamp}
            </div>
          </div>

          {/* ── Section: Explainable Risk Findings & Actions ──────── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px', marginBottom: '24px' }}>
            {/* Risk Findings */}
            <div className="card">
              <div className="card-title">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldAlert size={18} color="#ef4444" />
                  <span>Explainable Risk Findings ({profile.findings.length})</span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {profile.findings.map((f) => (
                  <div
                    key={f.finding_id}
                    style={{
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '14px 16px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 700, fontSize: '14px', color: '#fff' }}>{f.title}</span>
                      <span
                        className={`badge ${
                          f.severity === 'Critical' || f.severity === 'High'
                            ? 'badge-high'
                            : f.severity === 'Medium'
                            ? 'badge-medium'
                            : 'badge-low'
                        }`}
                        style={{ fontSize: '11px' }}
                      >
                        {f.severity}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px', lineHeight: 1.5 }}>
                      {f.description}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--accent-cyan)', marginBottom: '8px' }}>
                      Application: <strong>{f.app_name || 'Not specified by sample evidence'}</strong>
                      {' · '}
                      Permission: <strong>{f.permission_name || 'Not specified by sample evidence'}</strong>
                    </div>
                    <div
                      style={{
                        fontSize: '12px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        padding: '6px 10px',
                        borderRadius: '4px',
                        color: 'var(--text-muted)',
                        borderLeft: '3px solid var(--accent-cyan)',
                      }}
                    >
                      <strong style={{ color: 'var(--text-secondary)' }}>Evidence:</strong> {f.evidence}
                    </div>
                    <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                      <strong>Recommended next action:</strong> {f.recommended_action}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Actions */}
            <div className="card">
              <div className="card-title">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <UserCheck size={18} color="#34d399" />
                  <span>Recommended Review Actions ({profile.recommendations.length})</span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {profile.recommendations.map((rec, i) => (
                  <div
                    key={i}
                    style={{
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '14px 16px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 700, fontSize: '14px', color: '#6ee7b7' }}>{rec.action}</span>
                      <span
                        style={{
                          fontSize: '11px',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontWeight: 600,
                          backgroundColor:
                            rec.priority === 'Immediate'
                              ? 'rgba(239, 68, 68, 0.2)'
                              : rec.priority === 'Review Next Sprint'
                              ? 'rgba(245, 158, 11, 0.2)'
                              : 'rgba(59, 130, 246, 0.2)',
                          color:
                            rec.priority === 'Immediate'
                              ? '#f87171'
                              : rec.priority === 'Review Next Sprint'
                              ? '#fbbf24'
                              : '#60a5fa',
                        }}
                      >
                        {rec.priority}
                      </span>
                    </div>

                    <div style={{ fontSize: '12px', color: 'var(--accent-cyan)', marginBottom: '4px' }}>
                      Target SaaS: <strong>{rec.target_app}</strong>
                    </div>

                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {rec.rationale}
                    </div>
                  </div>
                ))}

                <div
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(16, 185, 129, 0.08)',
                    border: '1px solid rgba(16, 185, 129, 0.2)',
                    fontSize: '12px',
                    color: '#a7f3d0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <Lock size={15} color="#34d399" />
                  <span>
                    Decision-Support Only: Actions must be executed manually by authorized administrators.
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-title">Analysis limitations</div>
            <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '12px', lineHeight: 1.8 }}>
              {(profile.limitations || []).map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </div>

          {/* ── Section: Assigned SaaS Applications & Permissions ─── */}
          <div className="card">
            <div className="card-title">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} color="var(--accent-cyan)" />
                <span>Assigned SaaS Applications &amp; Privilege Breakdown</span>
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Comparing each permission against the {profile.role} baseline
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {profile.assigned_applications.map((app) => (
                <div
                  key={app.app_name}
                  style={{
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-sm)',
                    overflow: 'hidden',
                  }}
                >
                  {/* App Header */}
                  <div
                    style={{
                      padding: '12px 18px',
                      background: 'var(--bg-secondary)',
                      borderBottom: '1px solid var(--border-color)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: '10px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '15px', fontWeight: 800, color: '#fff' }}>
                        {app.app_name}
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        ({app.category})
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span
                        style={{
                          fontSize: '11px',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          backgroundColor:
                            app.account_status === 'Active'
                              ? 'rgba(16, 185, 129, 0.15)'
                              : 'rgba(239, 68, 68, 0.15)',
                          color: app.account_status === 'Active' ? '#34d399' : '#f87171',
                          fontWeight: 600,
                        }}
                      >
                        {app.account_status}
                      </span>
                      <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {app.total_permissions} Permissions Assigned
                      </span>
                    </div>
                  </div>

                  {/* Permissions List */}
                  <div style={{ padding: '12px 18px' }}>
                    <div className="table-responsive" style={{ border: 'none' }}>
                      <table>
                        <thead>
                          <tr>
                            <th>Permission / Role Policy</th>
                            <th>Privilege Level</th>
                            <th>Role Baseline Match</th>
                            <th>Last Used</th>
                            <th>Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          {app.permissions.map((p) => (
                            <tr key={p.name}>
                              <td className="mono" style={{ fontWeight: 700, color: '#fff' }}>
                                {p.name}
                              </td>
                              <td>
                                <span
                                  style={{
                                    fontSize: '11px',
                                    fontWeight: 700,
                                    padding: '2px 8px',
                                    borderRadius: '4px',
                                    backgroundColor:
                                      p.privilege_level === 'Critical'
                                        ? 'rgba(239, 68, 68, 0.2)'
                                        : p.privilege_level === 'Elevated'
                                        ? 'rgba(245, 158, 11, 0.2)'
                                        : p.privilege_level === 'Standard'
                                        ? 'rgba(59, 130, 246, 0.2)'
                                        : 'rgba(148, 163, 184, 0.15)',
                                    color:
                                      p.privilege_level === 'Critical'
                                        ? '#f87171'
                                        : p.privilege_level === 'Elevated'
                                        ? '#fbbf24'
                                        : p.privilege_level === 'Standard'
                                        ? '#60a5fa'
                                        : '#94a3b8',
                                  }}
                                >
                                  {p.privilege_level}
                                </span>
                              </td>
                              <td>
                                {p.matches_baseline ? (
                                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#34d399', fontSize: '12px' }}>
                                    <CheckCircle size={14} />
                                    <span>Matches Baseline</span>
                                  </span>
                                ) : (
                                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#f87171', fontSize: '12px', fontWeight: 600 }}>
                                    <XCircle size={14} />
                                    <span>Baseline Mismatch</span>
                                  </span>
                                )}
                              </td>
                              <td className="mono" style={{ fontSize: '12px', color: p.last_used.includes('Stale') ? '#fbbf24' : 'var(--text-secondary)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                  <Clock size={12} color="var(--text-muted)" />
                                  <span>{p.last_used}</span>
                                </div>
                              </td>
                              <td style={{ fontSize: '12px', color: 'var(--text-secondary)', maxWidth: '300px' }}>
                                {p.description}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
