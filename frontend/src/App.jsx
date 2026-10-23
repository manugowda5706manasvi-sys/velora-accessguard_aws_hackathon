import React, { useState, useEffect } from 'react';
import {
  Shield,
  LayoutDashboard,
  Users,
  ShieldCheck,
  UploadCloud,
  Server,
  LogOut,
  LogIn,
  RefreshCw,
  Lock,
} from 'lucide-react';
import { api, getStoredToken, removeStoredToken, setStoredToken } from './api';
import Overview from './pages/Overview';
import EmployeeTable from './pages/EmployeeTable';
import ReviewQueue from './pages/ReviewQueue';
import UploadData from './pages/UploadData';
import SystemStatus from './pages/SystemStatus';
import LoginModal from './components/LoginModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(!!getStoredToken());
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null);

  // Auto-login demo admin if not logged in (to ensure seamless local hackathon demo experience)
  const initAuth = async () => {
    if (!getStoredToken()) {
      try {
        const res = await api.login('admin', 'DemoAdmin2026!');
        setStoredToken(res.access_token);
        setIsLoggedIn(true);
      } catch (e) {
        // Fall back to opening modal if default credentials differ
        setShowLoginModal(true);
      }
    } else {
      setIsLoggedIn(true);
    }
  };

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await api.getStats();
      setStats(data);
    } catch (err) {
      console.error('Error fetching dashboard statistics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    initAuth().then(() => {
      loadStats();
    });

    const handleAuthRequired = () => {
      setIsLoggedIn(false);
      setShowLoginModal(true);
    };

    window.addEventListener('auth_required', handleAuthRequired);
    return () => window.removeEventListener('auth_required', handleAuthRequired);
  }, []);

  const handleLogout = () => {
    removeStoredToken();
    setIsLoggedIn(false);
    setShowLoginModal(true);
  };

  const handleSelectRecordFromAlert = (employeeId) => {
    setSelectedEmployeeId(employeeId);
    setActiveTab('employees');
  };

  return (
    <div className="app-container">
      {/* ── Left Sidebar ─────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-icon">
            <Shield size={20} />
          </div>
          <div>
            <div className="brand-title">AccessGuard AI</div>
            <div className="brand-sub">REVA • Team Velora</div>
          </div>
        </div>

        <nav className="nav-menu">
          <button
            onClick={() => { setActiveTab('overview'); setSelectedEmployeeId(null); }}
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
          >
            <LayoutDashboard size={18} />
            <span>Overview &amp; Alerts</span>
          </button>

          <button
            onClick={() => setActiveTab('employees')}
            className={`nav-item ${activeTab === 'employees' ? 'active' : ''}`}
          >
            <Users size={18} />
            <span>Employee Access</span>
          </button>

          <button
            onClick={() => { setActiveTab('review'); setSelectedEmployeeId(null); }}
            className={`nav-item ${activeTab === 'review' ? 'active' : ''}`}
          >
            <ShieldCheck size={18} />
            <span>Review &amp; Audit Log</span>
          </button>

          <button
            onClick={() => { setActiveTab('upload'); setSelectedEmployeeId(null); }}
            className={`nav-item ${activeTab === 'upload' ? 'active' : ''}`}
          >
            <UploadCloud size={18} />
            <span>Upload Data</span>
          </button>

          <button
            onClick={() => { setActiveTab('status'); setSelectedEmployeeId(null); }}
            className={`nav-item ${activeTab === 'status' ? 'active' : ''}`}
          >
            <Server size={18} />
            <span>System Status</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }} />
            <span>Backend: Connected</span>
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
            v1.0.0 • IMPULSE '26 Hackathon
          </div>
        </div>
      </aside>

      {/* ── Main Workspace ───────────────────────────────── */}
      <div className="main-content">
        <header className="top-bar">
          <div className="page-title">
            {activeTab === 'overview' && 'SaaS Access Risk Dashboard'}
            {activeTab === 'employees' && 'Consented SaaS Employee Access Table'}
            {activeTab === 'review' && 'Tamper-Evident Audit & Review Workflow'}
            {activeTab === 'upload' && 'Upload Access Permissions CSV'}
            {activeTab === 'status' && 'Operational Transparency & Architecture'}
          </div>

          <div className="top-actions">
            <button
              onClick={loadStats}
              title="Refresh intelligence"
              className="btn btn-secondary btn-sm"
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>

            {isLoggedIn ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span className="badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                  Demo Admin
                </span>
                <button
                  onClick={handleLogout}
                  className="btn btn-secondary btn-sm"
                  title="Sign out"
                >
                  <LogOut size={14} />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowLoginModal(true)}
                className="btn btn-primary btn-sm"
              >
                <LogIn size={14} />
                <span>Admin Login</span>
              </button>
            )}
          </div>
        </header>

        <main className="content-body">
          {activeTab === 'overview' && (
            <Overview
              stats={stats}
              loading={loading}
              onSelectRecord={handleSelectRecordFromAlert}
              onNavigate={(tab) => setActiveTab(tab)}
            />
          )}

          {activeTab === 'employees' && (
            <EmployeeTable
              selectedEmployeeId={selectedEmployeeId}
              onCloseDetail={() => setSelectedEmployeeId(null)}
              onReviewUpdated={loadStats}
            />
          )}

          {activeTab === 'review' && (
            <ReviewQueue
              onSelectRecord={handleSelectRecordFromAlert}
            />
          )}

          {activeTab === 'upload' && (
            <UploadData
              onUploadSuccess={loadStats}
              onNavigate={(tab) => setActiveTab(tab)}
            />
          )}

          {activeTab === 'status' && (
            <SystemStatus
              onResetSuccess={loadStats}
            />
          )}
        </main>
      </div>

      {/* ── Login Modal ──────────────────────────────────── */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onLoginSuccess={() => {
          setIsLoggedIn(true);
          loadStats();
        }}
      />
    </div>
  );
}
