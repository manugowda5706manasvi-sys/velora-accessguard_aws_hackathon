import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Download,
  AlertTriangle,
  FileCheck,
  CheckCircle,
  Hash,
  Clock,
  User,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { api } from '../api';

export default function ReviewQueue({ onSelectRecord }) {
  const [auditEntries, setAuditEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);

  const [pendingRecords, setPendingRecords] = useState([]);
  const [pendingLoading, setPendingLoading] = useState(false);

  const fetchAudit = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLog(100);
      setAuditEntries(data || []);
    } catch (err) {
      console.error('Failed to load audit entries:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPendingQueue = async () => {
    setPendingLoading(true);
    try {
      const res = await api.getRecords({ review_status: 'Pending Review', page_size: 20 });
      setPendingRecords(res.items || []);
    } catch (err) {
      console.error('Failed to load pending queue:', err);
    } finally {
      setPendingLoading(false);
    }
  };

  useEffect(() => {
    fetchAudit();
    fetchPendingQueue();
  }, []);

  const handleVerify = async () => {
    setVerifying(true);
    setVerifyResult(null);
    try {
      const res = await api.verifyAudit();
      setVerifyResult(res);
      fetchAudit(); // Refresh audit log to show the verification entry itself
    } catch (err) {
      console.error('Failed to verify audit chain:', err);
    } finally {
      setVerifying(false);
    }
  };

  const handleExportCsv = async () => {
    try {
      const blob = await api.exportAuditCsv();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `accessguard_audit_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error('Failed to export audit CSV:', err);
    }
  };

  return (
    <div>
      {/* ── Action Header ────────────────────────────────── */}
      <div className="card" style={{ padding: '18px 24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={20} color="var(--accent-cyan)" />
              <span>Tamper-Evident Audit Trail &amp; Review Workflow</span>
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '4px' }}>
              Every analysis run, file upload, and administrative decision is cryptographically chained using SHA-256 hashes.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleVerify}
              disabled={verifying}
              className="btn btn-primary"
            >
              <RefreshCw size={14} className={verifying ? 'spin' : ''} />
              <span>{verifying ? 'Recomputing Hashes...' : 'Verify Audit Integrity'}</span>
            </button>

            <button
              onClick={handleExportCsv}
              className="btn btn-secondary"
            >
              <Download size={14} />
              <span>Export Audit CSV</span>
            </button>
          </div>
        </div>

        {/* Verification Result Banner */}
        {verifyResult && (
          <div
            style={{
              marginTop: '16px',
              padding: '12px 16px',
              borderRadius: 'var(--radius-sm)',
              background: verifyResult.valid ? 'rgba(16, 185, 129, 0.1)' : 'var(--risk-high-bg)',
              border: `1px solid ${verifyResult.valid ? 'rgba(16, 185, 129, 0.3)' : 'var(--risk-high-border)'}`,
              color: verifyResult.valid ? '#34d399' : '#f87171',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '13px',
            }}
          >
            {verifyResult.valid ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
            <div>
              <strong>{verifyResult.valid ? 'Cryptographic Integrity Verified:' : 'Integrity Failure Detected:'}</strong>{' '}
              {verifyResult.valid
                ? `Recomputed all ${verifyResult.total_entries} audit entries from root hash. Chain is intact with zero tampering.`
                : `Hash mismatch at sequence #${verifyResult.first_bad_seq}! The audit history has been tampered with.`}
            </div>
          </div>
        )}
      </div>

      {/* ── Pending Review Queue ──────────────────────────── */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={16} color="#fbbf24" />
            <span>Pending Review Queue ({pendingRecords.length})</span>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>High &amp; Medium Risk Access Needing Review</span>
        </div>

        {pendingLoading ? (
          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>Loading queue...</div>
        ) : pendingRecords.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
            All detected access risks have been reviewed or resolved.
          </div>
        ) : (
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Employee ID</th>
                  <th>Name</th>
                  <th>Role</th>
                  <th>App</th>
                  <th>Score</th>
                  <th>Risk</th>
                  <th>Explanation</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {pendingRecords.slice(0, 8).map((r) => (
                  <tr key={r.employee_id}>
                    <td className="mono" style={{ color: 'var(--accent-cyan)' }}>{r.employee_id}</td>
                    <td>{r.employee_name || '—'}</td>
                    <td>{r.role || '—'}</td>
                    <td>{r.app || '—'}</td>
                    <td className="mono" style={{ fontWeight: 700 }}>{r.anomaly_score}</td>
                    <td>
                      <span className={`badge ${r.risk_level === 'High' ? 'badge-high' : 'badge-medium'}`}>
                        {r.risk_level}
                      </span>
                    </td>
                    <td style={{ maxWidth: '280px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {r.explanation}
                    </td>
                    <td>
                      <button
                        onClick={() => onSelectRecord(r.employee_id)}
                        className="btn btn-primary btn-sm"
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Audit Trail Table ─────────────────────────────── */}
      <div className="card">
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Hash size={16} color="var(--accent-indigo)" />
            <span>Cryptographic SHA-256 Hash Chain Log</span>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Newest entries first</span>
        </div>

        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Seq #</th>
                <th>Timestamp (UTC)</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Details</th>
                <th>Previous Hash (prev_hash)</th>
                <th>Entry Hash (hash)</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                    Loading audit trail...
                  </td>
                </tr>
              ) : auditEntries.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                    No audit records logged yet.
                  </td>
                </tr>
              ) : (
                auditEntries.map((entry) => (
                  <tr key={entry.entry_id}>
                    <td className="mono" style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      #{entry.seq}
                    </td>
                    <td className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                      {new Date(entry.timestamp).toLocaleString()}
                    </td>
                    <td>
                      <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#a5b4fc', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
                        {entry.actor}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{entry.action}</td>
                    <td style={{ maxWidth: '240px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                      <pre className="mono" style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                        {JSON.stringify(entry.details, null, 1)}
                      </pre>
                    </td>
                    <td className="mono" style={{ fontSize: '10px', color: 'var(--text-muted)' }} title={entry.prev_hash}>
                      {entry.prev_hash ? `${entry.prev_hash.slice(0, 10)}...${entry.prev_hash.slice(-6)}` : '0000000000...'}
                    </td>
                    <td className="mono" style={{ fontSize: '10px', color: '#38bdf8' }} title={entry.hash}>
                      {entry.hash ? `${entry.hash.slice(0, 10)}...${entry.hash.slice(-6)}` : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
