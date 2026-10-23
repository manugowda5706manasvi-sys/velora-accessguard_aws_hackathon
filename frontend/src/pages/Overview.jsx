import React from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  Clock,
  HelpCircle,
  Database,
  ArrowRight,
  TrendingUp,
  Cpu,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

export default function Overview({ stats, loading, onSelectRecord, onNavigate }) {
  if (loading || !stats) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-secondary)' }}>
        <div style={{ fontSize: '18px', fontWeight: 600 }}>Loading Dashboard Intelligence...</div>
      </div>
    );
  }

  const riskPieData = [
    { name: 'High Risk', value: stats.high_risk_count, color: '#ef4444' },
    { name: 'Medium Risk', value: stats.medium_risk_count, color: '#f59e0b' },
    { name: 'Low Risk', value: stats.low_risk_count, color: '#10b981' },
  ];

  return (
    <div>
      {/* ── Security & Explanatory Notice ────────────────── */}
      <div className="alert-banner" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <HelpCircle size={20} style={{ flexShrink: 0, color: 'var(--accent-cyan)' }} />
        <div>
          <strong>AI Decision-Support Principle:</strong> Isolation Forest identifies statistical outliers, not confirmed security attacks. Permission drift requires baseline evidence. Decisions recorded here are administrative recommendations and never execute automated revocations.
        </div>
      </div>

      {/* ── Stats Grid ───────────────────────────────────── */}
      <div className="stats-grid">
        <div className="stat-card" style={{ '--card-accent': '#06b6d4' }}>
          <div className="stat-header">
            <span>Total Records</span>
            <Database size={16} color="var(--accent-cyan)" />
          </div>
          <div className="stat-value">{stats.total_records}</div>
          <div className="stat-sub">Active Run: {stats.run_id}</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': '#6366f1' }}>
          <div className="stat-header">
            <span>Anomalies Flagged</span>
            <Cpu size={16} color="var(--accent-indigo)" />
          </div>
          <div className="stat-value" style={{ color: '#818cf8' }}>{stats.anomaly_count}</div>
          <div className="stat-sub">IsolationForest outliers (decision &lt; 0)</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': '#ef4444' }}>
          <div className="stat-header">
            <span>High Risk Access</span>
            <ShieldAlert size={16} color="#ef4444" />
          </div>
          <div className="stat-value" style={{ color: '#f87171' }}>{stats.high_risk_count}</div>
          <div className="stat-sub">Anomaly + Hard Rule Evidence</div>
        </div>

        <div className="stat-card" style={{ '--card-accent': '#f59e0b' }}>
          <div className="stat-header">
            <span>Pending Review</span>
            <Clock size={16} color="#f59e0b" />
          </div>
          <div className="stat-value" style={{ color: '#fbbf24' }}>{stats.pending_review_count}</div>
          <div className="stat-sub">{stats.investigating_count} investigating, {stats.resolved_count} resolved</div>
        </div>
      </div>

      {/* ── Charts Row 1 ─────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Risk by SaaS Application */}
        <div className="card">
          <div className="card-title">
            <span>Access Risk by SaaS Application</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Consented SaaS Accounts</span>
          </div>
          <div style={{ height: '260px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.risk_by_app}>
                <XAxis dataKey="app" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#101623', borderColor: '#222f47', borderRadius: '8px' }}
                />
                <Legend />
                <Bar dataKey="High" stackId="a" fill="#ef4444" radius={[0, 0, 0, 0]} />
                <Bar dataKey="Medium" stackId="a" fill="#f59e0b" radius={[0, 0, 0, 0]} />
                <Bar dataKey="Low" stackId="a" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Anomaly Score Distribution */}
        <div className="card">
          <div className="card-title">
            <span>Isolation Forest Anomaly Score Distribution</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>0-100 Score</span>
          </div>
          <div style={{ height: '260px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.score_distribution}>
                <XAxis dataKey="range" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#101623', borderColor: '#222f47', borderRadius: '8px' }}
                />
                <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── Charts Row 2 ─────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Risk Breakdown Pie */}
        <div className="card">
          <div className="card-title">
            <span>Overall Risk Distribution</span>
          </div>
          <div style={{ height: '240px', display: 'flex', alignItems: 'center' }}>
            <ResponsiveContainer width="60%" height="100%">
              <PieChart>
                <Pie
                  data={riskPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {riskPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#101623', borderColor: '#222f47', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {riskPieData.map((item) => (
                <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px' }}>
                  <div style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: item.color }} />
                  <span style={{ color: 'var(--text-secondary)' }}>{item.name}:</span>
                  <span style={{ fontWeight: 700 }} className="mono">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Triggered Rules */}
        <div className="card">
          <div className="card-title">
            <span>Top Triggered Risk Rules</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
            {stats.top_rule_reasons && stats.top_rule_reasons.length > 0 ? (
              stats.top_rule_reasons.slice(0, 5).map((r) => (
                <div key={r.rule} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{r.rule.replace(/_/g, ' ')}</span>
                  <span className="badge badge-medium mono">{r.count} hits</span>
                </div>
              ))
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No rule triggers in active run.</div>
            )}
          </div>
        </div>
      </div>

      {/* ── In-App Alerts Feed ────────────────────────────── */}
      <div className="card">
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} color="#f59e0b" />
            <span>Early Warning Alerts Feed</span>
          </div>
          <button
            onClick={() => onNavigate('employees')}
            className="btn btn-secondary btn-sm"
          >
            <span>View All Records</span>
            <ArrowRight size={14} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {stats.alerts && stats.alerts.length > 0 ? (
            stats.alerts.map((alert) => (
              <div
                key={alert.employee_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  gap: '16px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                  <span className={`badge ${alert.risk_level === 'High' ? 'badge-high' : 'badge-medium'}`}>
                    {alert.risk_level}
                  </span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '14px' }}>
                      {alert.employee_name || alert.employee_id}
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: '8px' }}>
                        ({alert.role || 'No Role'} • {alert.app || 'Unknown App'})
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {alert.explanation}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Score</div>
                    <div className="mono" style={{ fontWeight: 700, fontSize: '14px', color: 'var(--accent-cyan)' }}>
                      {alert.anomaly_score}
                    </div>
                  </div>
                  <button
                    onClick={() => onSelectRecord(alert.employee_id)}
                    className="btn btn-secondary btn-sm"
                  >
                    Investigate
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px 0' }}>
              No critical alerts detected in the current run.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
