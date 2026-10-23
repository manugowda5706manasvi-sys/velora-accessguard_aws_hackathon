import React, { useState } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle,
  Info,
  Shield,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { api } from '../api';

export default function UploadData({ onUploadSuccess, onNavigate }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const f = e.dataTransfer.files[0];
      if (f.name.endsWith('.csv')) {
        setFile(f);
        setError('');
        setResult(null);
      } else {
        setError('Please drop a valid .csv file.');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    setResult(null);

    try {
      const res = await api.uploadCsv(file);
      setResult(res);
      if (res.success && onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="card">
        <h2 style={{ fontSize: '18px', fontWeight: 800, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <UploadCloud size={22} color="var(--accent-cyan)" />
          <span>Upload SaaS Access Permissions CSV</span>
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '20px' }}>
          Upload consented SaaS employee access logs. The ingestion pipeline rigorously checks column types, boundaries, spreadsheet formula injections, and row limits before running unsupervised anomaly detection.
        </p>

        {/* ── Dropzone ────────────────────────────────────── */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${dragActive ? 'var(--accent-cyan)' : 'var(--border-color)'}`,
            borderRadius: 'var(--radius-lg)',
            backgroundColor: dragActive ? 'rgba(6, 182, 212, 0.05)' : 'var(--bg-primary)',
            padding: '40px 20px',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            marginBottom: '20px',
          }}
          onClick={() => document.getElementById('csv-upload-input').click()}
        >
          <input
            id="csv-upload-input"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />

          <FileSpreadsheet size={44} style={{ color: file ? 'var(--accent-cyan)' : 'var(--text-muted)', margin: '0 auto 12px' }} />

          {file ? (
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>{file.name}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                {(file.size / 1024).toFixed(1)} KB • Ready for validation &amp; analysis
              </div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Drag &amp; drop your CSV file here, or browse
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>
                Supports standard CSV up to 1 MB (&le; 5,000 employee records)
              </div>
            </div>
          )}
        </div>

        {/* ── Upload button ───────────────────────────────── */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginBottom: '24px' }}>
          {file && (
            <button
              onClick={() => { setFile(null); setResult(null); setError(''); }}
              className="btn btn-secondary"
            >
              Clear
            </button>
          )}
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="btn btn-primary"
            style={{ padding: '10px 24px' }}
          >
            {uploading ? (
              <>
                <RefreshCw size={15} className="spin" />
                <span>Validating &amp; Analysing...</span>
              </>
            ) : (
              <>
                <UploadCloud size={16} />
                <span>Upload &amp; Run Analysis</span>
              </>
            )}
          </button>
        </div>

        {/* ── Results & Error Display ─────────────────────── */}
        {error && (
          <div
            style={{
              padding: '14px 18px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--risk-high-bg)',
              border: '1px solid var(--risk-high-border)',
              color: 'var(--risk-high-text)',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              marginBottom: '20px',
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>Upload Error:</strong> {error}
            </div>
          </div>
        )}

        {result && !result.success && (
          <div
            style={{
              padding: '16px 20px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--risk-high-bg)',
              border: '1px solid var(--risk-high-border)',
              color: 'var(--risk-high-text)',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '14px', marginBottom: '10px' }}>
              <AlertCircle size={18} />
              <span>Validation Rejected ({result.errors.length} Error{result.errors.length > 1 ? 's' : ''})</span>
            </div>
            <ul style={{ paddingLeft: '20px', fontSize: '13px', lineHeight: 1.6 }}>
              {result.errors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          </div>
        )}

        {result && result.success && (
          <div
            style={{
              padding: '16px 20px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.35)',
              color: '#6ee7b7',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '15px' }}>
              <CheckCircle size={18} />
              <span>Analysis Complete: {result.records_processed} Records Processed</span>
            </div>
            <div style={{ fontSize: '13px', color: '#a7f3d0', marginTop: '6px' }}>
              Run ID: <span className="mono" style={{ color: '#fff' }}>{result.run_id}</span> • Machine learning isolation forest &amp; rule engines evaluated.
            </div>
            <div style={{ marginTop: '14px' }}>
              <button
                onClick={() => onNavigate('overview')}
                className="btn btn-primary btn-sm"
              >
                <span>View Dashboard Results</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* ── Strict Schema Guidance ──────────────────────── */}
        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', marginTop: '10px' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Info size={15} color="var(--accent-cyan)" />
            <span>Strict Schema &amp; Security Validation Requirements</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <div style={{ background: 'var(--bg-primary)', padding: '10px 12px', borderRadius: 'var(--radius-sm)' }}>
              <strong style={{ color: '#fff' }}>Required Columns (Numeric):</strong>
              <div className="mono" style={{ marginTop: '4px', color: 'var(--accent-cyan)' }}>
                permission_count, sensitive_access_count, inactive_days, off_hours_access_count, failed_logins_7d, role_mismatch
              </div>
            </div>

            <div style={{ background: 'var(--bg-primary)', padding: '10px 12px', borderRadius: 'var(--radius-sm)' }}>
              <strong style={{ color: '#fff' }}>Security Protections:</strong>
              <div style={{ marginTop: '4px' }}>
                Cells starting with <code className="mono">= + - @ \t \r</code> are display-neutralised to prevent formula execution.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
