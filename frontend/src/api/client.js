import axios from 'axios';

// Dynamic URL: works with Vite proxy (dev) and FastAPI static serving (prod/Tailscale)
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Error interceptor: report ALL API errors to backend log + show toast ---
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config || {};
    const url = config.url || '';

    if (error.response && error.response.status >= 400) {
      const { status } = error.response;
      let errorDetail = '';
      let userMessage = '';
      try {
        // Handle blob responses (e.g. file translate)
        if (error.response.data instanceof Blob) {
          errorDetail = await error.response.data.text();
        } else if (typeof error.response.data === 'object') {
          errorDetail = JSON.stringify(error.response.data).slice(0, 500);
        } else {
          errorDetail = String(error.response.data).slice(0, 500);
        }
        // Extract user-friendly message
        try {
          const parsed = JSON.parse(errorDetail);
          if (parsed.detail) {
            userMessage = Array.isArray(parsed.detail)
              ? parsed.detail.map(e => e.msg || e).join('; ')
              : String(parsed.detail);
          }
        } catch { userMessage = errorDetail.slice(0, 150); }
      } catch { /* ignore */ }

      // Show toast notification (skip health checks and log endpoints)
      if (!url.includes('/api/log/frontend') && !url.includes('/api/diagnostics') && !url.includes('/api/health')) {
        const shortUrl = url.replace('/api/', '').split('?')[0];
        const msg = userMessage || `Eroare ${status}`;
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('global-toast', {
            detail: {
              message: `${shortUrl}: ${msg}`,
              type: 'error',
              duration: 5000,
              id: Date.now(),
            },
          }));
        }

        // Fire-and-forget error report to backend
        axios.post(`${API_BASE_URL}/api/log/frontend`, {
          level: 'error',
          message: `API ${status}: ${config.method?.toUpperCase()} ${url}`,
          page: window.location.pathname,
          details: {
            status,
            method: config.method,
            url,
            response_body: errorDetail.slice(0, 300),
            type: 'api_error',
          },
        }).catch(() => {});
      }
    } else if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK' || !error.response) {
      // Network errors, timeouts, server unreachable — no response object
      const isTimeout = error.code === 'ECONNABORTED';
      const msg = isTimeout
        ? `Timeout — serverul nu a raspuns la timp (${config.url || 'unknown'})`
        : `Eroare retea — serverul nu este accesibil`;

      if (!url.includes('/api/log/frontend') && !url.includes('/api/health')) {
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('global-toast', {
            detail: {
              message: msg,
              type: 'error',
              duration: 7000,
              id: Date.now(),
            },
          }));
        }

        // Try to report (may fail if server is down)
        axios.post(`${API_BASE_URL}/api/log/frontend`, {
          level: 'error',
          message: `Network: ${error.code || 'ERR_UNKNOWN'} ${config.method?.toUpperCase()} ${url}`,
          page: window.location.pathname,
          details: {
            code: error.code,
            method: config.method,
            url,
            message: error.message?.slice(0, 200),
            type: 'network_error',
          },
        }).catch(() => {});
      }
    }
    return Promise.reject(error);
  }
);

// Extended timeout for long operations (file upload, translate, AI)
const LONG_TIMEOUT = 300000; // 5 minutes

// Upload a file (multipart/form-data)
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: LONG_TIMEOUT,
  });
  return response.data;
}

// Calculate price for an uploaded file
export async function calculatePrice(uploadId) {
  const response = await apiClient.post('/api/calculate', { upload_id: uploadId });
  return response.data;
}

// Get calculation history
export async function getHistory() {
  const response = await apiClient.get('/api/history');
  return response.data;
}

// Delete a history entry
export async function deleteHistoryEntry(id) {
  const response = await apiClient.delete(`/api/history/${id}`);
  return response.data;
}

// Trigger calibration
export async function triggerCalibration() {
  const response = await apiClient.post('/api/calibrate');
  return response.data;
}

// Get calibration status
export async function getCalibrationStatus() {
  const response = await apiClient.get('/api/calibration-status');
  return response.data;
}

// Revert calibration to previous backup
export async function revertCalibration() {
  const response = await apiClient.post('/api/calibrate/revert');
  return response.data;
}

// Reset calibration to defaults
export async function resetCalibration() {
  const response = await apiClient.post('/api/calibrate/reset');
  return response.data;
}

// List files in a directory
export async function listFiles(path = '') {
  const response = await apiClient.get('/api/files', { params: { path } });
  return response.data;
}

// Get file content
export async function getFileContent(path) {
  const response = await apiClient.get('/api/files/content', { params: { path } });
  return response.data;
}

// Get settings
export async function getSettings() {
  const response = await apiClient.get('/api/settings');
  return response.data;
}

// Update settings
export async function updateSettings(settings) {
  const response = await apiClient.put('/api/settings', settings);
  return response.data;
}

// Get competitor comparison
export async function getCompetitorComparison(price) {
  const response = await apiClient.get('/api/competitors/compare', { params: { price } });
  return response.data;
}

// Validate price for self-learning
export async function validatePrice(uploadId, price) {
  const response = await apiClient.post('/api/validate-price', { upload_id: uploadId, validated_price: price });
  return response.data;
}

// Get activity log
export async function getActivityLog(limit = 50, action = null) {
  const params = { limit };
  if (action) params.action = action;
  const response = await apiClient.get('/api/activity-log', { params });
  return response.data;
}

// Check backend connectivity
export async function checkHealth() {
  try {
    const response = await apiClient.get('/api/settings');
    return response.status === 200;
  } catch {
    return false;
  }
}

// WebSocket helper for progress tracking
export function createProgressWebSocket(taskId, onMessage, onClose, onError) {
  // Dynamic protocol + host: works on localhost (dev) and Tailscale HTTPS (prod)
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = window.location.host;
  const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/progress/${taskId}`);

  ws.onopen = () => {
    console.log(`WebSocket connected for task: ${taskId}`);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) onMessage(data);
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err);
    }
  };

  ws.onclose = () => {
    if (onClose) onClose();
  };

  ws.onerror = (err) => {
    console.error('WebSocket error:', err);
    if (onError) onError(err);
  };

  return ws;
}

// --- Frontend Logging ---

// Report page view to backend (fire-and-forget)
export function logPageView(page) {
  apiClient.post('/api/log/frontend', {
    level: 'pageview',
    page,
    details: { timestamp: new Date().toISOString() },
  }).catch(() => {}); // silently ignore errors
}

// Report frontend error to backend (fire-and-forget)
export function logFrontendError(message, details = {}, page = '') {
  apiClient.post('/api/log/frontend', {
    level: 'error',
    message: String(message).slice(0, 500),
    page: page || window.location.pathname,
    details,
  }).catch(() => {});
}

// Global unhandled error catcher
if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    logFrontendError(event.message, {
      source: event.filename,
      line: event.lineno,
      col: event.colno,
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    logFrontendError(`Unhandled Promise: ${event.reason}`, {
      type: 'unhandledrejection',
    });
  });
}

export default apiClient;
