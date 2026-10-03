import axios from 'axios';
export const apiClient = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api', timeout: 12000 });
export class ApiError extends Error { constructor(message, status) { super(message); this.status = status; } }
export async function request(path, options = {}) {
  try { return (await apiClient({ url: path, ...options })).data; }
  catch (error) {
    if (axios.isCancel(error)) throw error;
    const status = error.response?.status, detail = error.response?.data?.detail;
    const message = status === 422 ? (Array.isArray(detail) ? detail.map(x => `${x.loc?.slice(1).join('.')}: ${x.msg}`).join('; ') : 'Invalid request. Check the input fields.')
      : status === 404 ? (typeof detail === 'string' ? detail : 'No data available.')
      : status >= 500 ? 'The backend could not complete this request. Please retry.'
      : !status ? 'Unable to connect to TraceWatt backend. Check the backend URL and connection.'
      : `Request failed (${status}).`;
    throw new ApiError(message, status);
  }
}
const key = encodeURIComponent;
export const api = {
  health: signal => request('/health', { signal }),
  consumers: (params = {}, signal) => request('/consumers', { params, signal }),
  cases: signal => request('/export/cases', { signal }),
  case: (id, signal) => request(`/cases/${key(id)}`, { signal }),
  updateCase: (id, data) => request(`/cases/${key(id)}/status`, { method: 'PATCH', data }),
  consumption: (id, signal) => request(`/consumers/${key(id)}/consumption`, { signal }),
  baseline: (id, signal) => request(`/consumers/${key(id)}/baseline`, { signal }),
  feeders: signal => request('/feeders', { signal }),
  feederSummary: (params = {}, signal) => request('/feeders/summary', { params, signal }),
  alerts: signal => request('/alerts', { params: { limit: 1000 }, signal }),
  reading: data => request('/readings', { method: 'POST', data }),
  pdf: id => request(`/export/cases/${key(id)}/pdf`, { responseType: 'blob' }),
};
export function download(blob, name) {
  const url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

