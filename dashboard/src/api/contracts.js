export const statuses = ['New', 'Under Review', 'Inspection Scheduled', 'Confirmed', 'False Alarm', 'Closed'];
export function readingPayload(form, now = false) {
  if (!form.consumer_id) throw new Error('Select a real consumer.');
  const date = now ? new Date() : new Date(form.ts);
  if (!Number.isFinite(date.getTime())) throw new Error('Enter a valid timestamp.');
  const result = { consumer_id: form.consumer_id, ts: date.toISOString() };
  for (const field of ['kwh', 'voltage', 'current', 'power_kw']) {
    const value = form[field];
    result[field] = value === '' || value == null ? null : Number(value);
    if (result[field] !== null && (!Number.isFinite(result[field]) || result[field] < 0)) throw new Error(`${field} must be a non-negative number or blank.`);
  }
  for (const field of ['meter_status', 'comm_status']) result[field] = form[field]?.trim() || null;
  return result;
}
export function joinSeries(actual = [], baseline = []) {
  const rows = new Map();
  for (const p of actual) rows.set(new Date(p.ts).getTime(), { ts: p.ts, kwh: p.kwh });
  for (const p of baseline) {
    const time = new Date(p.ts).getTime();
    rows.set(time, { ...(rows.get(time) || { ts: p.ts }), expected_kwh: p.expected_kwh });
  }
  return [...rows.entries()].sort((a,b) => a[0]-b[0]).map(([,v]) => v);
}

