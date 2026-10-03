import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { api } from "../api/client";
import { readingPayload } from "../api/contracts";
import { useResource } from "../hooks/useResource";
import {
  Badge,
  PageHead,
  Panel,
  Pipeline,
  Resource,
  Telemetry,
} from "../components/UI";
const GridScene = lazy(() => import("../components/GridScene"));
const localTime = () => {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 19);
};
export default function Simulation() {
  const [offset, setOffset] = useState(0);
  const consumers = useResource(
    useCallback((s) => api.consumers({ limit: 100, offset }, s), [offset]),
    30000,
  );
  const [form, setForm] = useState({
    consumer_id: "",
    ts: localTime(),
    kwh: "",
    voltage: "",
    current: "",
    power_kw: "",
    meter_status: "",
    comm_status: "",
  });
  const [mode, setMode] = useState("Stopped"),
    [interval, setIntervalValue] = useState(10),
    [busy, setBusy] = useState(false),
    [result, setResult] = useState(null),
    [error, setError] = useState(""),
    [pulse, setPulse] = useState(0);
  const latest = useRef({ form, interval }),
    inflight = useRef(false),
    mounted = useRef(true),
    running = useRef(false);
  useEffect(() => {
    latest.current = { form, interval };
  }, [form, interval]);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      running.current = false;
    };
  }, []);
  const send = useCallback(async (automatic) => {
    if (inflight.current) return false;
    inflight.current = true;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const payload = readingPayload(latest.current.form, automatic);
      setPulse((v) => v + 1);
      const ack = await api.reading(payload);
      if (mounted.current) {
        setResult({ ack, payload, at: new Date().toLocaleTimeString() });
        setPulse((v) => v + 1);
      }
      return true;
    } catch (e) {
      if (mounted.current) {
        setError(e.message);
        setMode("Paused");
        running.current = false;
      }
      return false;
    } finally {
      inflight.current = false;
      if (mounted.current) setBusy(false);
    }
  }, []);
  useEffect(() => {
    if (mode !== "Running") return;
    let cancelled = false,
      timer;
    running.current = true;
    async function tick() {
      if (cancelled || !running.current) return;
      if (document.hidden) {
        setMode("Paused");
        running.current = false;
        return;
      }
      await send(true);
      if (!cancelled && running.current)
        timer = setTimeout(tick, latest.current.interval * 1000);
    }
    timer = setTimeout(tick, latest.current.interval * 1000);
    function hide() {
      if (document.hidden) {
        running.current = false;
        setMode("Paused");
        clearTimeout(timer);
      }
    }
    document.addEventListener("visibilitychange", hide);
    return () => {
      cancelled = true;
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", hide);
    };
  }, [mode, send]);
  const id = form.consumer_id;
  function change(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }
  function start() {
    try {
      readingPayload(form, true);
      setError("");
      running.current = true;
      setMode("Running");
    } catch (e) {
      setError(e.message);
    }
  }
  function stop(value) {
    running.current = false;
    setMode(value);
  }
  return (
    <>
      <PageHead
        eyebrow="LIVE INGESTION / INPUT SIMULATION"
        title="A signal becomes a record."
        description="This simulates the same ingestion path that a future real smart meter / IoT device would use."
      >
        <Badge>{mode}</Badge>
      </PageHead>
      <div className="simulation-grid">
        <Panel
          title="Connected grid"
          className="simulation-scene"
          aside={<span>CONCEPTUAL TOPOLOGY</span>}
        >
          <Suspense fallback={<div className="scene" />}>
            <GridScene pulse={pulse} consumer={id} />
          </Suspense>
          <div className="route-legend">
            Consumer → Meter → Feeder → TraceWatt
          </div>
          <p className="muted">
            Nodes illustrate the ingestion path, not actual network topology. A
            moving signal means a request was sent, not that analysis completed.
          </p>
        </Panel>
        <Panel title="Reading controls">
          <Resource
            resource={consumers}
            empty="No consumers available for simulation"
          >
            {() => (
              <p className="muted">
                Select an existing consumer. Inputs are submitted without
                inferred classifications.
              </p>
            )}
          </Resource>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(false);
            }}
          >
            <fieldset
              disabled={busy || mode === "Running" || !!consumers.error}
            >
              <label>
                Real consumer
                <select
                  name="consumer_id"
                  value={id}
                  onChange={change}
                  required
                >
                  <option value="">Select a consumer</option>
                  {(consumers.data || []).map((c) => (
                    <option key={c.consumer_id}>{c.consumer_id}</option>
                  ))}
                </select>
              </label>
              <div className="pagination">
                <button
                  type="button"
                  disabled={!offset}
                  onClick={() => {
                    setOffset(offset - 100);
                    setForm({ ...form, consumer_id: "" });
                  }}
                >
                  ← Previous
                </button>
                <small>Page {offset / 100 + 1}</small>
                <button
                  type="button"
                  disabled={consumers.data?.length !== 100}
                  onClick={() => {
                    setOffset(offset + 100);
                    setForm({ ...form, consumer_id: "" });
                  }}
                >
                  Next →
                </button>
              </div>
              <label>
                Timestamp (local time → UTC)
                <input
                  name="ts"
                  type="datetime-local"
                  step="1"
                  required
                  value={form.ts}
                  onChange={change}
                />
              </label>
              <div className="input-grid">
                {[
                  ["kwh", "Energy · kWh"],
                  ["voltage", "Voltage · V"],
                  ["current", "Current · A"],
                  ["power_kw", "Power · kW"],
                ].map(([name, label]) => (
                  <label key={name}>
                    {label}
                    <input
                      type="number"
                      step="any"
                      min="0"
                      name={name}
                      value={form[name]}
                      placeholder="null"
                      onChange={change}
                    />
                  </label>
                ))}
              </div>
              <div className="input-grid">
                {["meter_status", "comm_status"].map((name) => (
                  <label key={name}>
                    {name.replace("_", " ")}
                    <input
                      name={name}
                      value={form[name]}
                      onChange={change}
                      placeholder="Optional signal"
                    />
                  </label>
                ))}
              </div>
              <label>
                Sampling interval · seconds
                <input
                  type="number"
                  min="5"
                  max="300"
                  value={interval}
                  onChange={(e) =>
                    setIntervalValue(
                      Math.max(5, Math.min(300, Number(e.target.value) || 5)),
                    )
                  }
                />
              </label>
              <button className="primary full" type="submit" disabled={!id}>
                Send one reading ↗
              </button>
            </fieldset>
          </form>
          <div className="actions sim-actions">
            <button
              className="primary"
              disabled={
                !id ||
                busy ||
                mode === "Running" ||
                !!consumers.error ||
                !consumers.data?.some((c) => c.consumer_id === id)
              }
              onClick={start}
            >
              {mode === "Paused" ? "Resume" : "Start"}
            </button>
            <button
              disabled={mode !== "Running"}
              onClick={() => stop("Paused")}
            >
              Pause
            </button>
            <button
              disabled={mode === "Stopped"}
              onClick={() => stop("Stopped")}
            >
              Stop
            </button>
          </div>
          <p className="muted">
            Explicit input simulation. Blank optional fields are sent as null.
            Running repeats these inputs with a fresh timestamp each interval
            and pauses when hidden. It writes real backend records.
          </p>
        </Panel>
      </div>
      <Panel
        title="Latest request acknowledgement"
        aside={
          busy ? (
            <Badge>Sending</Badge>
          ) : result ? (
            <span>{result.at}</span>
          ) : null
        }
      >
        {error && (
          <div className="error" role="alert">
            {error}
          </div>
        )}
        {result ? (
          <div className="notice" role="status">
            <strong>
              {result.ack.stored
                ? "Reading stored successfully."
                : "Reading not stored. A reading with this consumer and timestamp may already exist."}
            </strong>
            <p>
              Consumer: {result.payload.consumer_id} · {result.payload.ts}
            </p>
            <p>
              Stored: {String(result.ack.stored)} · Queued:{" "}
              {String(result.ack.queued)}
            </p>
            <p>
              ML analysis is currently unavailable. Queue acknowledgement does
              not confirm processing or detection.
            </p>
          </div>
        ) : !busy && !error ? (
          <p className="muted">No reading has been sent in this session.</p>
        ) : null}
        <Pipeline ack={result?.ack} health={!!result} />
      </Panel>
      <Panel
        title="Live consumption from backend"
        aside={<Badge>15s polling</Badge>}
      >
        <Telemetry id={id} revision={result?.at || 0} />
      </Panel>
    </>
  );
}
