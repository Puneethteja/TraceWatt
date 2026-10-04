import axios from "axios";
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  timeout: 12000,
});
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}
export async function request(path, options = {}) {
  try {
    const response = await apiClient({ url: path, ...options });
    if (options.responseType !== "blob" && typeof response.data === "string") {
      throw new ApiError(
        "The backend returned an unexpected response. Check the API URL and reverse proxy.",
        response.status,
      );
    }
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (axios.isCancel(error)) throw error;
    const status = error.response?.status,
      detail = error.response?.data?.detail;
    const message =
      status === 422
        ? Array.isArray(detail)
          ? detail
              .map((x) => `${x.loc?.slice(1).join(".")}: ${x.msg}`)
              .join("; ")
          : "Invalid request. Check the input fields."
        : status === 404
          ? typeof detail === "string"
            ? detail
            : "No data available."
          : status >= 500
            ? "The backend could not complete this request. Please retry."
            : !status
              ? "Unable to connect to TraceWatt backend. Check the backend URL and connection."
              : `Request failed (${status}).`;
    throw new ApiError(message, status);
  }
}
export function normalizeConsumerId(id) {
  if (!id) return id;
  const str = String(id).trim();
  if (/^\d+$/.test(str)) {
    return `CUS_${str.padStart(3, "0")}`;
  }
  if (/^cus_?\d+$/i.test(str)) {
    const num = str.replace(/\D/g, "");
    return `CUS_${num.padStart(3, "0")}`;
  }
  return str;
}

function key(id) {
  return encodeURIComponent(id);
}

export const api = {
  health: (signal) => request("/health", { signal }),
  consumers: async (params = {}, signal) => {
    const [rows, assessments] = await Promise.all([
      request("/consumers", { params, signal }),
      request("/export/cases", { signal }).catch((error) => {
        if (signal?.aborted) throw error;
        return null;
      }),
    ]);
    const cases = new Map((assessments || []).map((c) => [c.consumer_id, c]));
    // Incoming consumer APIs synthesize Low/Closed/0.1 for consumers with no case.
    // Only persisted case records establish analysis, never those defaults.
    return rows.map((c) => {
      const stored = cases.get(c.consumer_id);
      return {
        ...c,
        risk_level: stored?.risk_level ?? null,
        status: stored?.status ?? null,
        cause: stored?.cause ?? null,
        anomaly_score: stored?.anomaly_score ?? null,
        confidence: stored?.confidence ?? null,
        estimated_loss: stored?.estimated_loss ?? null,
        analysis_unavailable: assessments === null,
      };
    });
  },
  cases: async (signal) => {
    // /cases became available in the incoming merge. Retain compatibility with
    // the original API, where /export/cases is the only case-list endpoint.
    const rows = [];
    for (let offset = 0; ; offset += 1000) {
      let page;
      try {
        page = await request("/cases", {
          params: { limit: 1000, offset },
          signal,
        });
      } catch (error) {
        if (error.status === 404 && offset === 0)
          return request("/export/cases", { signal });
        throw error;
      }
      rows.push(...page);
      if (page.length < 1000) return rows;
    }
  },
  case: (id, signal) => request(`/cases/${key(normalizeConsumerId(id))}`, { signal }),
  updateCase: (id, data) =>
    request(`/cases/${key(normalizeConsumerId(id))}/status`, { method: "PATCH", data }),
  consumption: (id, signal) =>
    request(`/consumers/${key(normalizeConsumerId(id))}/consumption`, { signal }),
  baseline: (id, signal) =>
    request(`/consumers/${key(normalizeConsumerId(id))}/baseline`, { signal }),
  feeders: (signal) => request("/feeders", { signal }),
  feederSummary: (params = {}, signal) =>
    request("/feeders/summary", { params, signal }),
  alerts: (signal) => request("/alerts", { params: { limit: 1000 }, signal }),
  updateAlert: (id, is_read = true) =>
    request(`/alerts/${key(id)}`, { method: "PATCH", data: { is_read } }),
  markAllAlertsRead: () =>
    request("/alerts/mark-all-read", { method: "POST" }),
  reading: (data) => request("/readings", { method: "POST", data }),
  pdf: (id) =>
    request(`/export/cases/${key(normalizeConsumerId(id))}/pdf`, { responseType: "blob" }),
  evaluation: (signal) => request("/evaluation", { signal }),
  report: (id, signal) =>
    request(`/export/cases/${key(normalizeConsumerId(id))}/report`, { signal }).catch(() => null),
};
export function download(blob, name) {
  const url = URL.createObjectURL(blob),
    a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const getDashboardSummary = () => request("/dashboard/summary");
export const getConsumptionTrend = () => request("/dashboard/consumption-trend");
export const getRiskDistribution = () => request("/dashboard/risk-distribution");
export const getRecentAlerts = (limit = 10) => request("/alerts", { params: { limit } });
export const getConsumerDetail = (id) => request(`/consumers/${key(normalizeConsumerId(id))}`);
export const getCaseDetail = (id) => request(`/cases/${key(normalizeConsumerId(id))}`);
export const updateCaseStatus = (id, data) => request(`/cases/${key(normalizeConsumerId(id))}/status`, { method: "PATCH", data });
export const getConsumerReport = (id) => request(`/export/cases/${key(normalizeConsumerId(id))}/report`);
export const getEvaluationMetrics = () => request("/dashboard/evaluation");

