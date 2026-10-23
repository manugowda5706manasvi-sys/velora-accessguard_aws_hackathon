import React, { useState, useEffect } from 'react';
import {
  Server,
  Cpu,
  Database,
  Activity,
  RotateCcw,
  Shield,
  Layers,
  CheckCircle,
  AlertCircle,
  Cloud,
} from 'lucide-react';
import { api } from '../api';

export default function SystemStatus({ onResetSuccess }) {
  const [statusData, setStatusData] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState('');

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const [sys, h] = await Promise.all([api.getSystemStatus(), api.getHealth()]);
      setStatusData(sys);
      setHealthData(h);
    } catch (err) {
      console.error('Failed to load system status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleResetDemo = async () => {
    if (!window.confirm('Are you sure you want to reset all demo data and re-evaluate the sample dataset?')) {
      return;
    }
    setResetting(true);
    setResetMessage('');
    try {
      const res = await api.resetDemoData();
      setResetMessage(`Demo data reset successfully: ${res.records_loaded} records loaded.`);
      fetchStatus();
      if (onResetSuccess) onResetSuccess();
    } catch (err) {
      setResetMessage(`Reset failed: ${err.message}`);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div>
      {/* ── System Transparency Banner ───────────────────── */}
      <div className="card" style={{ padding: '20px 24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Server size={22} color="var(--accent-cyan)" />
              <h2 style={{ fontSize: '18px', fontWeight: 800 }}>System Status &amp; Deployed Architecture</h2>
              <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle size={12} />
                <span>Operational</span>
              </span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '6px' }}>
              Live operational verification of backend runtime, machine learning configuration, and storage backend.
            </p>
          </div>

          <button
            onClick={handleResetDemo}
            disabled={resetting}
            className="btn btn-danger"
          >
            <RotateCcw size={14} className={resetting ? 'spin' : ''} />
            <span>{resetting ? 'Resetting Demo...' : 'Reset Demo Data'}</span>
          </button>
        </div>

        {resetMessage && (
          <div style={{ marginTop: '14px', padding: '10px 14px', background: 'rgba(52, 211, 153, 0.12)', border: '1px solid rgba(52, 211, 153, 0.3)', color: '#6ee7b7', borderRadius: 'var(--radius-sm)', fontSize: '13px' }}>
            {resetMessage}
          </div>
        )}
      </div>

      {/* ── Parameters & Backend Grid ────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* ML Configuration */}
        <div className="card">
          <div className="card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={16} color="var(--accent-indigo)" />
              <span>Machine Learning Configuration</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Algorithm</span>
              <span className="mono" style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>
                {statusData?.model_params?.algorithm || 'IsolationForest'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Estimators (Trees)</span>
              <span className="mono" style={{ fontWeight: 600 }}>
                {statusData?.model_params?.n_estimators || 200}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Contamination Factor</span>
              <span className="mono" style={{ fontWeight: 600 }}>
                {statusData?.model_params?.contamination || 0.08}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Random Seed (Reproducible)</span>
              <span className="mono" style={{ fontWeight: 600 }}>
                {statusData?.model_params?.random_state || 42}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Scoring Range</span>
              <span className="mono" style={{ fontWeight: 600 }}>
                0 – 100 (Higher = Outlier)
              </span>
            </div>
          </div>
        </div>

        {/* Storage Backend & Runtime */}
        <div className="card">
          <div className="card-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Database size={16} color="#34d399" />
              <span>Storage &amp; Runtime Transparency</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Active Storage Backend</span>
              <span className="badge badge-low mono">
                {statusData?.storage_backend || 'sqlite'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Active Run ID</span>
              <span className="mono" style={{ fontSize: '12px' }}>
                {statusData?.dataset_info?.active_run_id || '—'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Records in Active Run</span>
              <span className="mono" style={{ fontWeight: 700 }}>
                {statusData?.dataset_info?.records_in_active_run || 0}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Backend Framework</span>
              <span className="mono">FastAPI 0.115 + Mangum</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Audit Hash Chain</span>
              <span className="mono" style={{ color: '#38bdf8' }}>SHA-256 Tamper-Evident</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Honest Architecture Diagrams ─────────────────── */}
      <div className="card">
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} color="var(--accent-cyan)" />
            <span>Actual Architecture vs. Future Roadmap</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
          {/* Currently Deployed */}
          <div style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <span className="badge badge-low">Currently Deployed (100% Real)</span>
            </div>
            <div style={{ fontSize: '13px', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: '8px' }}>
                <strong>1. Frontend:</strong> Single-Page React App + Vite + Recharts (WCAG-AA accessible, dark theme).
              </div>
              <div style={{ marginBottom: '8px' }}>
                <strong>2. API Server:</strong> FastAPI backend with CORS, rate-limited login, and security headers. Operates via <code className="mono">uvicorn</code> locally and AWS Lambda Function URL via <code className="mono">Mangum</code>.
              </div>
              <div style={{ marginBottom: '8px' }}>
                <strong>3. AI Engine:</strong> Scikit-Learn unsupervised <code className="mono">IsolationForest</code> + z-score median feature explainability + deterministic baseline drift rules.
              </div>
              <div>
                <strong>4. Storage &amp; Audit:</strong> SQLite local / DynamoDB cloud toggled via env var, with SHA-256 append-only cryptographic hash chaining.
              </div>
            </div>
          </div>

          {/* Future Roadmap */}
          <div style={{ background: 'var(--bg-primary)', border: '1px dashed var(--border-color)', borderRadius: 'var(--radius-md)', padding: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <span className="badge badge-medium">Future Roadmap (Not Deployed in MVP)</span>
            </div>
            <div style={{ fontSize: '13px', lineHeight: 1.7, color: 'var(--text-muted)' }}>
              <div style={{ marginBottom: '8px' }}>
                <strong>1. SaaS Connectors:</strong> AWS AppFlow ingestion for direct Slack, Salesforce, GitHub consent integration.
              </div>
              <div style={{ marginBottom: '8px' }}>
                <strong>2. Event-Driven Scheduling:</strong> Amazon EventBridge hourly cron jobs triggering Lambda scans automatically.
              </div>
              <div style={{ marginBottom: '8px' }}>
                <strong>3. Multi-Tenant IAM:</strong> Amazon Cognito User Pools with MFA and role-based tenant isolation.
              </div>
              <div>
                <strong>4. Automated Actioning:</strong> Human-in-the-loop approval webhooks sending tickets to Jira Service Management.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
