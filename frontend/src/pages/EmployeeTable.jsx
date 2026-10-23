import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Eye,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  X,
  FileText,
  UserCheck,
} from 'lucide-react';
import { api } from '../api';

export default function EmployeeTable({ selectedEmployeeId, onCloseDetail, onReviewUpdated }) {
  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [appFilter, setAppFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('anomaly_score');
  const [sortDesc, setSortDesc] = useState(true);

  const [loading, setLoading] = useState(false);
  const [detailRecord, setDetailRecord] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Review form state
  const [reviewStatus, setReviewStatus] = useState('Investigating');
  const [reviewComment, setReviewComment] = useState('');
  const [reviewOutcome, setReviewOutcome] = useState('Access reduced (manual action recorded)');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError, setReviewError] = useState('');
  const [reviewSuccess, setReviewSuccess] = useState('');

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const res = await api.getRecords({
        page,
        page_size: pageSize,
        search,
        risk_level: riskFilter,
        app: appFilter,
        review_status: statusFilter,
        sort_by: sortBy,
        sort_desc: sortDesc,
      });
      setRecords(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to fetch records:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [page, search, riskFilter, appFilter, statusFilter, sortBy, sortDesc]);

  // Handle selectedEmployeeId from parent (e.g. Alerts feed click)
  useEffect(() => {
    if (selectedEmployeeId) {
      openDetail(selectedEmployeeId);
    }
  }, [selectedEmployeeId]);

  const openDetail = async (empId) => {
    setDetailLoading(true);
    setReviewError('');
    setReviewSuccess('');
    try {
      const rec = await api.getRecord(empId);
      setDetailRecord(rec);
      setReviewStatus(rec.review_status === 'Pending Review' ? 'Investigating' : rec.review_status);
      setReviewComment(rec.review_comment || '');
      setReviewOutcome(rec.review_outcome || 'Access reduced (manual action recorded)');
    } catch (err) {
      console.error('Failed to load employee details:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!reviewComment.trim()) {
      setReviewError('A review comment is strictly required for audit tracking.');
      return;
    }
    setReviewSubmitting(true);
    setReviewError('');
    setReviewSuccess('');

    try {
      const payload = {
        status: reviewStatus,
        comment: reviewComment.trim(),
        outcome: reviewStatus === 'Resolved' ? reviewOutcome : null,
      };
      await api.updateReview(detailRecord.employee_id, payload);
      setReviewSuccess('Review decision recorded and committed to audit hash chain.');
      openDetail(detailRecord.employee_id);
      fetchRecords();
      if (onReviewUpdated) onReviewUpdated();
    } catch (err) {
      setReviewError(err.message || 'Failed to submit review');
    } finally {
      setReviewSubmitting(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div>
      {/* ── Filters Bar ──────────────────────────────────── */}
      <div className="card" style={{ padding: '16px 20px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', flex: 1 }}>
            {/* Search */}
            <div style={{ position: 'relative', minWidth: '240px' }}>
              <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search ID, Name, Role..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                style={{ paddingLeft: '32px', width: '100%' }}
              />
            </div>

            {/* Risk filter */}
            <select
              value={riskFilter}
              onChange={(e) => {
                setRiskFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Risk Levels</option>
              <option value="High">High Risk</option>
              <option value="Medium">Medium Risk</option>
              <option value="Low">Low Risk</option>
            </select>

            {/* App filter */}
            <select
              value={appFilter}
              onChange={(e) => {
                setAppFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All SaaS Apps</option>
              <option value="GitHub">GitHub</option>
              <option value="Google Workspace">Google Workspace</option>
              <option value="AWS Console">AWS Console</option>
              <option value="Slack">Slack</option>
              <option value="Jira">Jira</option>
            </select>

            {/* Review Status filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Review Statuses</option>
              <option value="Pending Review">Pending Review</option>
              <option value="Investigating">Investigating</option>
              <option value="Resolved">Resolved</option>
            </select>
          </div>

          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Showing <span className="mono" style={{ color: '#fff', fontWeight: 700 }}>{records.length}</span> of <span className="mono">{total}</span> records
          </div>
        </div>
      </div>

      {/* ── Table ────────────────────────────────────────── */}
      <div className="table-responsive">
        <table>
          <thead>
            <tr>
              <th>Employee ID</th>
              <th>Name</th>
              <th>Role</th>
              <th>App</th>
              <th
                style={{ cursor: 'pointer' }}
                onClick={() => {
                  setSortBy('permission_count');
                  setSortDesc(!sortDesc);
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span>Permissions</span>
                  <ArrowUpDown size={13} />
                </div>
              </th>
              <th>Inactive</th>
              <th>Off-Hours</th>
              <th>Failed Logins</th>
              <th
                style={{ cursor: 'pointer' }}
                onClick={() => {
                  setSortBy('anomaly_score');
                  setSortDesc(!sortDesc);
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span>Anomaly Score</span>
                  <ArrowUpDown size={13} />
                </div>
              </th>
              <th>Risk Level</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="12" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                  Loading employee records...
                </td>
              </tr>
            ) : records.length === 0 ? (
              <tr>
                <td colSpan="12" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                  No matching records found.
                </td>
              </tr>
            ) : (
              records.map((r) => (
                <tr key={r.employee_id}>
                  <td className="mono" style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>
                    {r.employee_id}
                  </td>
                  <td>{r.employee_name || '—'}</td>
                  <td>{r.role || '—'}</td>
                  <td>{r.app || '—'}</td>
                  <td className="mono">{r.permission_count}</td>
                  <td className="mono">{r.inactive_days}d</td>
                  <td className="mono">{r.off_hours_access_count}</td>
                  <td className="mono">{r.failed_logins_7d}</td>
                  <td className="mono" style={{ fontWeight: 700 }}>
                    <span
                      style={{
                        color:
                          r.anomaly_score >= 70
                            ? '#f87171'
                            : r.anomaly_score >= 45
                            ? '#fbbf24'
                            : '#34d399',
                      }}
                    >
                      {r.anomaly_score}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        r.risk_level === 'High'
                          ? 'badge-high'
                          : r.risk_level === 'Medium'
                          ? 'badge-medium'
                          : 'badge-low'
                      }`}
                    >
                      {r.risk_level}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`badge-status ${
                        r.review_status === 'Pending Review'
                          ? 'status-pending'
                          : r.review_status === 'Investigating'
                          ? 'status-investigating'
                          : 'status-resolved'
                      }`}
                    >
                      {r.review_status}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => openDetail(r.employee_id)}
                      className="btn btn-secondary btn-sm"
                      title="Inspect evidence and review"
                    >
                      <Eye size={13} />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Pagination ───────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Page {page} of {totalPages}
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="btn btn-secondary btn-sm"
          >
            <ChevronLeft size={14} />
            <span>Previous</span>
          </button>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="btn btn-secondary btn-sm"
          >
            <span>Next</span>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {/* ── Detail Panel Modal ───────────────────────────── */}
      {detailRecord && (
        <div className="modal-overlay" onClick={() => { setDetailRecord(null); if (onCloseDetail) onCloseDetail(); }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '20px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <h3 style={{ fontSize: '18px', fontWeight: 800 }}>
                    {detailRecord.employee_name || detailRecord.employee_id}
                  </h3>
                  <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                    ({detailRecord.employee_id})
                  </span>
                  <span
                    className={`badge ${
                      detailRecord.risk_level === 'High'
                        ? 'badge-high'
                        : detailRecord.risk_level === 'Medium'
                        ? 'badge-medium'
                        : 'badge-low'
                    }`}
                  >
                    {detailRecord.risk_level} Risk
                  </span>
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  {detailRecord.role || 'No Role'} • {detailRecord.department || 'No Dept'} • {detailRecord.app || 'Unknown SaaS App'}
                </div>
              </div>
              <button
                onClick={() => { setDetailRecord(null); if (onCloseDetail) onCloseDetail(); }}
                style={{ color: 'var(--text-muted)', padding: '4px' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Plain-Language Explanation */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>
                Why Flagged (Explainability Evidence)
              </div>
              <div style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '12px 14px', fontSize: '14px', lineHeight: 1.5 }}>
                {detailRecord.explanation}
              </div>
            </div>

            {/* Recommendation */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>
                Recommendation
              </div>
              <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: 'var(--radius-sm)', padding: '12px 14px', fontSize: '13px', color: '#a7f3d0' }}>
                {detailRecord.recommendation}
              </div>
            </div>

            {/* Feature Contributions & Drift */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
                Top Contributing Outlier Features (Population Median Z-Scores)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
                {detailRecord.top_features && detailRecord.top_features.map((f) => (
                  <div key={f.feature} style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '10px 12px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{f.feature.replace(/_/g, ' ')}</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '4px' }}>
                      <span className="mono" style={{ fontWeight: 700, fontSize: '15px' }}>{f.value}</span>
                      <span className="mono" style={{ fontSize: '12px', color: f.direction === 'above' ? '#f87171' : '#38bdf8' }}>
                        {f.z_score > 0 ? `+${f.z_score}` : f.z_score}σ ({f.direction})
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Triggered Hard Rules */}
            {detailRecord.rule_hits && detailRecord.rule_hits.length > 0 && (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
                  Triggered Deterministic Rules
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {detailRecord.rule_hits.map((r) => (
                    <div key={r.rule_id} style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '10px 12px', display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                      <span className={`badge ${r.severity === 'high' ? 'badge-high' : 'badge-medium'}`} style={{ fontSize: '10px' }}>
                        {r.severity}
                      </span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '13px', fontWeight: 600 }}>{r.description}</div>
                        <div className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{r.details}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── Review Decision Form ────────────────────────── */}
            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '18px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <UserCheck size={16} color="var(--accent-cyan)" />
                <span>Record Administrative Review Decision</span>
              </div>

              {reviewSuccess && (
                <div style={{ background: 'rgba(52, 211, 153, 0.15)', border: '1px solid rgba(52, 211, 153, 0.3)', color: '#6ee7b7', padding: '10px 12px', borderRadius: 'var(--radius-sm)', fontSize: '13px', marginBottom: '12px' }}>
                  {reviewSuccess}
                </div>
              )}

              {reviewError && (
                <div style={{ background: 'var(--risk-high-bg)', border: '1px solid var(--risk-high-border)', color: 'var(--risk-high-text)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', fontSize: '13px', marginBottom: '12px' }}>
                  {reviewError}
                </div>
              )}

              <form onSubmit={handleReviewSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Review Status</label>
                    <select
                      value={reviewStatus}
                      onChange={(e) => setReviewStatus(e.target.value)}
                      style={{ width: '100%' }}
                    >
                      <option value="Investigating">Investigating</option>
                      <option value="Resolved">Resolved</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Outcome</label>
                    <select
                      value={reviewOutcome}
                      disabled={reviewStatus !== 'Resolved'}
                      onChange={(e) => setReviewOutcome(e.target.value)}
                      style={{ width: '100%' }}
                    >
                      <option value="Access reduced (manual action recorded)">Access reduced (manual action recorded)</option>
                      <option value="Accepted risk">Accepted risk</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    Audit Comment <span style={{ color: '#f87171' }}>*</span> (Required)
                  </label>
                  <textarea
                    rows="3"
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                    placeholder="Document your findings, tickets, or reasons for this administrative record..."
                    style={{ width: '100%', resize: 'vertical' }}
                    required
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '6px' }}>
                  <button
                    type="submit"
                    disabled={reviewSubmitting}
                    className="btn btn-primary"
                  >
                    {reviewSubmitting ? 'Recording Decision...' : 'Commit Decision to Audit Chain'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
