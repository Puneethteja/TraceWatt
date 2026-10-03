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
const key = encodeURIComponent;
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
  case: (id, signal) => request(`/cases/${key(id)}`, { signal }),
  updateCase: (id, data) =>
    request(`/cases/${key(id)}/status`, { method: "PATCH", data }),
  consumption: (id, signal) =>
    request(`/consumers/${key(id)}/consumption`, { signal }),
  baseline: (id, signal) =>
    request(`/consumers/${key(id)}/baseline`, { signal }),
  feeders: (signal) => request("/feeders", { signal }),
  feederSummary: (params = {}, signal) =>
    request("/feeders/summary", { params, signal }),
  alerts: (signal) => request("/alerts", { params: { limit: 1000 }, signal }),
  reading: (data) => request("/readings", { method: "POST", data }),
  pdf: (id) =>
    request(`/export/cases/${key(id)}/pdf`, { responseType: "blob" }),
};
export function download(blob, name) {
  const url = URL.createObjectURL(blob),
    a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
