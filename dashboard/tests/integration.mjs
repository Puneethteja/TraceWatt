import assert from "node:assert/strict";
const base = process.env.TRACEWATT_TEST_API_URL || "http://127.0.0.1:8000";
let failed = 0;
for (const path of [
  "/health",
  "/consumers",
  "/cases",
  "/export/cases",
  "/feeders",
  "/feeders/summary",
  "/alerts",
]) {
  try {
    const result = await fetch(base + path);
    console.log(result.ok ? "PASS" : "BLOCKED", path, result.status);
    if (!result.ok) failed++;
  } catch (e) {
    failed++;
    console.log("BLOCKED", path, e.message);
  }
}
const result = await fetch(base + "/readings", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: "{}",
});
assert.equal(result.status, 422);
console.log("PASS POST /readings invalid payload: 422");
console.log(
  "Stored/queued success and duplicate-reading checks require an existing real consumer and compatible schema. No valid readings submitted.",
);
process.exitCode = failed ? 1 : 0;
