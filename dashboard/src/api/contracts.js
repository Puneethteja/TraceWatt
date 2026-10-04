export const statuses = [
  "New",
  "Under Review",
  "Inspection Scheduled",
  "Confirmed",
  "False Alarm",
  "Closed",
];
export function readingPayload(form, now = false) {
  if (!form.consumer_id) throw new Error("Select a real consumer.");
  const date = now ? new Date() : new Date(form.ts);
  if (!Number.isFinite(date.getTime()))
    throw new Error("Enter a valid timestamp.");
  const result = {
    consumer_id: form.consumer_id,
    ts: date.toISOString(),
    is_simulation: true,
  };
  for (const field of ["kwh", "voltage", "current", "power_kw"]) {
    const value = form[field];
    result[field] = value === "" || value == null ? null : Number(value);
    if (
      result[field] !== null &&
      (!Number.isFinite(result[field]) || result[field] < 0)
    )
      throw new Error(`${field} must be a non-negative number or blank.`);
  }
  for (const field of ["meter_status", "comm_status"])
    result[field] = form[field]?.trim() || null;
  return result;
}
export function joinSeries(actual = [], baseline = []) {
  const rows = new Map();
  for (const p of actual) {
    const time = p.ts ? new Date(p.ts).getTime() : NaN;
    if (Number.isFinite(time)) rows.set(time, { ts: p.ts, kwh: p.kwh });
  }
  for (const p of baseline) {
    const time = p.ts ? new Date(p.ts).getTime() : NaN;
    if (!Number.isFinite(time)) continue;
    rows.set(time, {
      ...(rows.get(time) || { ts: p.ts }),
      expected_kwh: p.expected_kwh,
    });
  }
  return [...rows.entries()].sort((a, b) => a[0] - b[0]).map(([, v]) => v);
}

/**
 * Existing backend Detection contract. This is a type description, not a detector.
 * CaseOut exposes only a subset; unavailable fields must remain absent.
 * @typedef {Object} Detection
 * @property {string} consumer_id
 * @property {number} anomaly_score
 * @property {string} risk_level
 * @property {string} cause
 * @property {number} confidence
 * @property {string} period_start
 * @property {string} period_end
 * @property {number} baseline_kwh
 * @property {number} actual_kwh
 * @property {number} deviation_pct
 * @property {string} evidence
 * @property {string} counter_evidence
 * @property {string} recommended_action
 */
