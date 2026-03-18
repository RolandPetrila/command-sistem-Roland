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

// Upload a file (multipart/form-data)
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
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

export default apiClient;
