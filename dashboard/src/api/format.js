export const fmt = (value) =>
  value == null
    ? "—"
    : typeof value === "number"
      ? new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(
          value,
        )
      : String(value);
export const date = (value) =>
  value ? new Date(value).toLocaleString() : "Not exposed";


export function parseEvidence(value) {
  if (value == null || value === "") return [];
  if (Array.isArray(value)) return value.map(v => typeof v === "object" ? JSON.stringify(v) : String(v));
  if (typeof value === "object" && value !== null) {
    return Object.entries(value).map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : v}`);
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    if ((trimmed.startsWith("[") && trimmed.endsWith("]")) || (trimmed.startsWith("{") && trimmed.endsWith("}"))) {
      try {
        const parsed = JSON.parse(trimmed);
        if (Array.isArray(parsed)) return parsed.map(v => typeof v === "object" ? JSON.stringify(v) : String(v));
        if (typeof parsed === "object" && parsed !== null) {
          return Object.entries(parsed).map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : v}`);
        }
      } catch {
        // fallback to plain string
      }
    }
    return [value];
  }
  return [String(value)];
}

export function evidenceText(value) {
  const items = parseEvidence(value);
  if (!items.length) return "Not available in this record.";
  return items.join("\n");
}

