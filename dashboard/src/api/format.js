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
export function evidenceText(value) {
  if (value == null || value === "") return "Not available in this record.";
  if (typeof value === "string") return value;
  if (typeof value !== "object") return String(value);
  if (Array.isArray(value)) return value.map(evidenceText).join("\n");
  return Object.entries(value)
    .map(([key, item]) => `${key}: ${evidenceText(item)}`)
    .join("\n");
}
