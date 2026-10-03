import test from "node:test";
import assert from "node:assert/strict";
import { evidenceText } from "../src/api/format.js";
test("evidence arrays and objects render without inventing explanations", () => {
  assert.equal(
    evidenceText(["meter_status", "comm_status"]),
    "meter_status\ncomm_status",
  );
  assert.equal(evidenceText({ available: false }), "available: false");
});
