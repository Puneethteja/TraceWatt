import axios from 'axios';

// Base API URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000,
});

/**
 * Fetch list of consumers with optional query params (risk_level, category, feeder_id)
 * GET /consumers
 */
export async function getConsumers(params = {}) {
  try {
    const response = await apiClient.get('/consumers', { params });
    return response.data || [];
  } catch (error) {
    console.error('[API Error] getConsumers:', error.message);
    return [];
  }
}

/**
 * Fetch detailed consumer summary by ID
 * GET /consumers/{id}
 */
export async function getConsumerDetail(id) {
  try {
    const response = await apiClient.get(`/consumers/${id}`);
    return response.data || null;
  } catch (error) {
    console.error(`[API Error] getConsumerDetail(${id}):`, error.message);
    return null;
  }
}

/**
 * Fetch case triage and explainability details by consumer ID
 * GET /cases/{id}
 */
export async function getCaseDetail(id) {
  try {
    const response = await apiClient.get(`/cases/${id}`);
    return response.data || null;
  } catch (error) {
    console.error(`[API Error] getCaseDetail(${id}):`, error.message);
    return null;
  }
}

/**
 * Fetch daily telemetry consumption data points
 * GET /consumers/{id}/consumption
 */
export async function getConsumption(id, params = {}) {
  try {
    const response = await apiClient.get(`/consumers/${id}/consumption`, { params });
    return response.data || [];
  } catch (error) {
    console.error(`[API Error] getConsumption(${id}):`, error.message);
    return [];
  }
}

/**
 * Fetch AI model baseline curve and peer bounds
 * GET /consumers/{id}/baseline
 */
export async function getBaseline(id) {
  try {
    const response = await apiClient.get(`/consumers/${id}/baseline`);
    return response.data || null;
  } catch (error) {
    console.error(`[API Error] getBaseline(${id}):`, error.message);
    return null;
  }
}

/**
 * Update case triage status or review notes
 * PATCH /cases/{id}/status
 */
export async function updateCaseStatus(id, payload) {
  try {
    const response = await apiClient.patch(`/cases/${id}/status`, payload);
    return response.data;
  } catch (error) {
    console.error(`[API Error] updateCaseStatus(${id}):`, error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Fetch distribution feeders overview
 * GET /feeders
 */
export async function getFeeders() {
  try {
    const response = await apiClient.get('/feeders');
    return response.data || [];
  } catch (error) {
    console.error('[API Error] getFeeders:', error.message);
    return [];
  }
}

/**
 * Fetch transformer-level energy loss reconciliation series
 * GET /feeders/{id}/losses
 */
export async function getFeederLosses(id) {
  try {
    const response = await apiClient.get(`/feeders/${id}/losses`);
    return response.data || [];
  } catch (error) {
    console.error(`[API Error] getFeederLosses(${id}):`, error.message);
    return [];
  }
}

/**
 * Fetch recent alert notifications
 * GET /alerts
 */
export async function getAlerts() {
  try {
    const response = await apiClient.get('/alerts');
    return response.data || [];
  } catch (error) {
    console.error('[API Error] getAlerts:', error.message);
    return [];
  }
}

/**
 * Trigger export download stream
 * GET /export
 */
export async function getExport(params = {}) {
  try {
    const response = await apiClient.get('/export', {
      params,
      responseType: 'blob',
    });
    return response.data;
  } catch (error) {
    console.error('[API Error] getExport:', error.message);
    throw error;
  }
}

export default apiClient;
