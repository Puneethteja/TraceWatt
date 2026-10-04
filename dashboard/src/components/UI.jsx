import { useCallback, useMemo } from "react";
import {
  Area,
  Brush,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import { joinSeries } from "../api/contracts";
import { useResource } from "../hooks/useResource";
import { fmt, date } from "../api/format";
export function Badge({ children }) {
  return (
    <span
      className={`badge ${String(children).toLowerCase().replaceAll(" ", "-")}`}
    >
      {children ?? "Not available"}
    </span>
  );
}
export function Empty({ title = "No data available", children }) {
  return (
    <div className="empty">
      <span className="empty-icon">⌁</span>
      <h3>{title}</h3>
      <p>
        {children ||
          "Records will appear here when the backend makes them available."}
      </p>
    </div>
  );
}
export function Resource({
  resource,
  children,
  empty = "No records found",
  allowEmpty = false,
}) {
  if (resource.loading)
    return (
      <div className="skeleton" role="status" aria-label="Loading data">
        <i />
        <i />
        <i />
      </div>
    );
  if (resource.error)
    return (
      <div className="error" role="alert">
        <strong>
          {resource.error.status === 404
            ? "No data available"
            : "Unable to load data"}
        </strong>
        <p>{resource.error.message}</p>
        <button onClick={resource.refresh}>Retry</button>
        {resource.data && (
          <small>
            Previously loaded records are hidden because refresh failed.
          </small>
        )}
      </div>
    );
  if (
    !allowEmpty &&
    (!resource.data || (Array.isArray(resource.data) && !resource.data.length))
  )
    return <Empty title={empty} />;
  return children(resource.data);
}
export function Panel({ title, aside, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <h2>{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  );
}
export function PageHead({
  eyebrow = "MISSION CONSOLE",
  title,
  description,
  children,
}) {
  return (
    <header className="page-head">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children}
    </header>
  );
}
export function Stat({ label, value, note }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{fmt(value)}</strong>
      <small>{note}</small>
    </div>
  );
}
export function Telemetry({ id, revision = 0, baselineOnly = false }) {
  const loadActual = useCallback(
    (signal) => (id ? api.consumption(id, signal) : Promise.resolve([])),
    [id],
  );
  const loadBaseline = useCallback(
    (signal) => (id ? api.baseline(id, signal) : Promise.resolve([])),
    [id],
  );
  const actual = useResource(loadActual, 15000, revision),
    baseline = useResource(loadBaseline, 30000, revision);
  const rows = useMemo(
    () =>
      joinSeries(
        actual.error ? [] : actual.data || [],
        baseline.error ? [] : baseline.data || [],
      ),
    [actual.data, baseline.data, actual.error, baseline.error],
  );
  if (!id)
    return (
      <Empty title="Select a consumer">
        Choose a real consumer to explore meter records.
      </Empty>
    );
  return (
    <div>
      <div className="chart-key">
        <span>● {baselineOnly ? "Baseline" : "Actual consumption"}</span>
        {!baselineOnly && <span className="muted">– – Available baseline</span>}
        <small>kWh · API timestamps</small>
      </div>
      {actual.loading || baseline.loading ? (
        <div className="skeleton">
          <i />
          <i />
        </div>
      ) : (
        <>
          {actual.error && actual.error.status !== 404 && (
            <div className="error">
              {actual.error.message}
              <button onClick={actual.refresh}>Retry consumption</button>
            </div>
          )}
          {baseline.error && (
            <p className="notice">
              {baseline.error.status === 404
                ? "No baseline available. Awaiting baseline data."
                : baseline.error.message}
              <button onClick={baseline.refresh}>Retry baseline</button>
            </p>
          )}
          {rows.length && (!baselineOnly || baseline.data?.length) ? (
            <div className="chart">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={rows.slice(-1500)}
                  margin={{ top: 12, right: 20, left: 0, bottom: 8 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 5"
                    vertical={false}
                    stroke="var(--border)"
                  />
                  <XAxis
                    dataKey="ts"
                    tickFormatter={(v) =>
                      new Date(v).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                      })
                    }
                    minTickGap={50}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    domain={[0, (dataMax) => Math.max(10, Math.ceil((dataMax || 0) * 1.15))]}
                  />
                  <Tooltip
                    labelFormatter={date}
                    contentStyle={{
                      background: "var(--panel)",
                      border: "1px solid var(--border)",
                      borderRadius: 12,
                    }}
                  />
                  {!baselineOnly && (
                    <Area
                      type="linear"
                      dataKey="kwh"
                      name="Actual kWh"
                      stroke="#36966e"
                      fill="#36966e"
                      fillOpacity={0.15}
                      connectNulls={true}
                      isAnimationActive={false}
                    />
                  )}
                  <Line
                    type="linear"
                    dataKey="expected_kwh"
                    name="Baseline kWh"
                    stroke="#a8a664"
                    strokeDasharray="5 5"
                    dot={false}
                    connectNulls={true}
                    isAnimationActive={false}
                  />
                  <Brush
                    dataKey="ts"
                    height={22}
                    tickFormatter={(v) => new Date(v).toLocaleDateString()}
                    stroke="#79998b"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <Empty
              title={
                baselineOnly
                  ? "No baseline available"
                  : "No consumption data available"
              }
            />
          )}
          <small className="muted">
            Latest 1,500 returned points · refreshed every 15 seconds while
            visible. Missing baseline values remain gaps; records without valid
            timestamps are not plotted. The consumption API currently converts
            nullable kWh to zero.
          </small>
        </>
      )}
    </div>
  );
}
export function Pipeline({ ack, health }) {
  const isHealthy = health && health.status === "ok";
  const nodes = [
    ["INGEST", health ? "API reachable" : "Not verified"],
    ["VALIDATE", ack ? "Accepted" : "Not observed"],
    ["STORE", ack?.stored ? "Confirmed" : ack ? "Not stored" : "Not observed"],
    ["QUEUE", ack?.queued ? "Acknowledged" : "Not observed"],
    ["ANALYZE", health?.fuzzy_engine === "active" ? "Connected" : isHealthy ? "ML active" : "ML unavailable"],
    ["CASE", isHealthy ? "Active" : "Not observed"],
    ["ALERT", isHealthy ? "Active" : "Not observed"],
  ];
  return (
    <div className="pipeline">
      {nodes.map(([name, state], i) => (
        <div className={ack && i < 4 ? "observed" : ""} key={name}>
          <span>{String(i + 1).padStart(2, "0")}</span>
          <strong>{name}</strong>
          <small>{state}</small>
        </div>
      ))}
    </div>
  );
}
