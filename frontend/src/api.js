/**
 * AccessGuard AI API Client.
 * Handles JWT token storage, automatic authorization header injection,
 * and unified error parsing.
 */

const BASE_URL = import.meta.env.VITE_API_URL || '';
const API_BASE = `${BASE_URL}/api`;

export const getStoredToken = () => localStorage.getItem('accessguard_token');
export const setStoredToken = (token) => localStorage.setItem('accessguard_token', token);
export const removeStoredToken = () => localStorage.removeItem('accessguard_token');

async function request(endpoint, options = {}) {
  const token = getStoredToken();
  const headers = {
    Accept: 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Handle FormData (multipart upload) vs JSON body
  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    removeStoredToken();
    window.dispatchEvent(new Event('auth_required'));
  }

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || JSON.stringify(errorJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail);
  }

  // Check if CSV download
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('text/csv')) {
    return response.blob();
  }

  return response.json();
}

export const api = {
  // Public
  getHealth: () => fetch(`${BASE_URL}/health`).then((r) => r.json()),

  // Auth
  login: (username, password) =>
    request('/auth/login', {
      method: 'POST',
      body: { username, password },
    }),

  // Dashboard Stats
  getStats: (runId) => request(`/stats${runId ? `?run_id=${runId}` : ''}`),

  // Records
  getRecords: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        query.append(k, v);
      }
    });
    return request(`/records?${query.toString()}`);
  },

  getRecord: (employeeId, runId) =>
    request(`/records/${employeeId}${runId ? `?run_id=${runId}` : ''}`),

  updateReview: (employeeId, reviewData) =>
    request(`/records/${employeeId}/review`, {
      method: 'PATCH',
      body: reviewData,
    }),

  // Upload & Analyse
  uploadCsv: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/upload', {
      method: 'POST',
      body: formData,
    });
  },

  triggerAnalysis: () =>
    request('/analyse', {
      method: 'POST',
    }),

  // Audit
  getAuditLog: (limit = 200) => request(`/audit?limit=${limit}`),
  verifyAudit: () => request('/audit/verify', { method: 'POST' }),
  exportAuditCsv: () => request('/audit/export'),

  // Demo Reset
  resetDemoData: () => request('/reset', { method: 'POST' }),

  // System Status
  getSystemStatus: () => request('/system/status'),
};
