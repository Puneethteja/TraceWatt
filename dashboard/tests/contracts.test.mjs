import test from "node:test";
import assert from "node:assert/strict";
import { readingPayload, joinSeries, statuses } from "../src/api/contracts.js";

test("reading form emits only ReadingIn fields, preserving null optional values", () => {
  const value = readingPayload({
    consumer_id: "contract-test",
    ts: "2026-01-01T00:00:00Z",
    kwh: "",
    voltage: "",
    current: "",
    power_kw: "",
    meter_status: "",
    comm_status: "",
  });
  assert.deepEqual(Object.keys(value).sort(), [
    "comm_status",
    "consumer_id",
    "current",
    "kwh",
    "meter_status",
    "power_kw",
    "ts",
    "voltage",
  ]);
  assert.equal(value.kwh, null);
  assert.equal(value.meter_status, null);
});
test("zero energy is preserved and numeric inputs are parsed", () => {
  const value = readingPayload({
    consumer_id: "contract-test",
    ts: "2026-01-01T00:00:00Z",
    kwh: "0",
    voltage: "230",
  });
  assert.equal(value.kwh, 0);
  assert.equal(value.voltage, 230);
});
test("invalid consumer, time, negative and non-finite input are rejected", () => {
  assert.throws(() => readingPayload({}), /consumer/);
  assert.throws(
    () => readingPayload({ consumer_id: "contract-test", ts: "invalid" }),
    /timestamp/,
  );
  for (const kwh of ["-1", "abc", "Infinity"])
    assert.throws(
      () =>
        readingPayload({ consumer_id: "contract-test", ts: "2026-01-01", kwh }),
      /non-negative/,
    );
});
test("baseline-only timestamps survive; missing values never become zero", () => {
  const rows = joinSeries(
    [{ ts: "2026-01-02T00:00:00Z", kwh: null }],
    [{ ts: "2026-01-01T00:00:00Z", expected_kwh: 0 }],
  );
  assert.equal(rows.length, 2);
  assert.equal(rows[0].kwh, undefined);
  assert.equal(rows[1].kwh, null);
  assert.equal(rows[1].expected_kwh, undefined);
});
test("equivalent timestamps merge without interpolating baseline", () => {
  const rows = joinSeries(
    [{ ts: "2026-01-01T00:00:00Z", kwh: 0 }],
    [{ ts: "2026-01-01T05:30:00+05:30", expected_kwh: 0 }],
  );
  assert.equal(rows.length, 1);
  assert.equal(rows[0].expected_kwh, 0);
});
test("empty datasets stay empty and status options match requested workflow", () => {
  assert.deepEqual(joinSeries(), []);
  assert.deepEqual(statuses, [
    "New",
    "Under Review",
    "Inspection Scheduled",
    "Confirmed",
    "False Alarm",
    "Closed",
  ]);
});
