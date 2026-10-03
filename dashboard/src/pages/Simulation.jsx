import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import { Badge, PageHead, Panel, Resource, Pipeline } from "../components/UI";

const GridScene = lazy(() => import("../components/GridScene"));

function formatTimeAgo(date) {
  if (!date) return "Never";
  const seconds = Math.floor((new Date() - date) / 1000);
  if (seconds < 2) return "Just now";
  if (seconds < 60) return `${seconds} sec ago`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes} min ago`;
}

export default function Simulation() {
  const consumers = useResource(
    useCallback((s) => api.consumers({ limit: 50 }, s), []),
    60000,
  );

  const [mode, setMode] = useState("Stopped");
  const [intervalMs, setIntervalMs] = useState(1000); // 1 reading/sec
  
  const [stats, setStats] = useState({
    generated: 0,
    ingested: 0,
    rejected: 0,
    lastReadingAt: null,
  });

  const [lastResult, setLastResult] = useState(null);
  const [pulse, setPulse] = useState(0);
  const [recentErrors, setRecentErrors] = useState([]);

  const running = useRef(false);
  const mounted = useRef(true);
  const timer = useRef(null);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      running.current = false;
      clearTimeout(timer.current);
    };
  }, []);

  const [timeAgo, setTimeAgo] = useState("Never");
  useEffect(() => {
    const i = setInterval(() => {
      setTimeAgo(formatTimeAgo(stats.lastReadingAt));
    }, 1000);
    return () => clearInterval(i);
  }, [stats.lastReadingAt]);

  const sendRandomReading = useCallback(async () => {
    if (!consumers.data || consumers.data.length === 0) return;
    
    // Pick random consumer
    const randomConsumer = consumers.data[Math.floor(Math.random() * consumers.data.length)];
    
    // Generate synthetic payload
    const baseKwh = 10 + Math.random() * 5; 
    const voltage = 230 + (Math.random() * 10 - 5);
    
    const payload = {
      consumer_id: randomConsumer.consumer_id,
      ts: new Date().toISOString(),
      kwh: Number(baseKwh.toFixed(2)),
      voltage: Number(voltage.toFixed(1)),
      current: Number(((baseKwh / 24 * 2.5 * 1000) / (voltage * 0.9)).toFixed(2)),
      power_kw: Number((baseKwh / 24 * 2.5).toFixed(2)),
      meter_status: null,
      comm_status: "OK"
    };

    setPulse((v) => v + 1);
    
    setStats((prev) => ({
      ...prev,
      generated: prev.generated + 1,
    }));

    try {
      const ack = await api.reading(payload);
      if (!mounted.current) return;
      
      setLastResult({ ack, payload, at: new Date().toLocaleTimeString() });
      setPulse((v) => v + 1);
      
      if (ack.stored) {
        setStats((prev) => ({
          ...prev,
          ingested: prev.ingested + 1,
          lastReadingAt: new Date()
        }));
      } else {
        setStats((prev) => ({
          ...prev,
          rejected: prev.rejected + 1,
          lastReadingAt: new Date()
        }));
      }
    } catch (e) {
      if (!mounted.current) return;
      setStats((prev) => ({
        ...prev,
        rejected: prev.rejected + 1,
        lastReadingAt: new Date()
      }));
      setRecentErrors(prev => [e.message, ...prev].slice(0, 5));
    }
  }, [consumers.data]);

  useEffect(() => {
    if (mode !== "Running") return;
    let cancelled = false;
    running.current = true;
    
    async function tick() {
      if (cancelled || !running.current) return;
      if (document.hidden) {
        setMode("Paused");
        running.current = false;
        return;
      }
      
      await sendRandomReading();
      
      if (!cancelled && running.current) {
        timer.current = setTimeout(tick, intervalMs);
      }
    }
    
    timer.current = setTimeout(tick, intervalMs);
    
    function hide() {
      if (document.hidden) {
        running.current = false;
        setMode("Paused");
        clearTimeout(timer.current);
      }
    }
    document.addEventListener("visibilitychange", hide);
    return () => {
      cancelled = true;
      clearTimeout(timer.current);
      document.removeEventListener("visibilitychange", hide);
    };
  }, [mode, intervalMs, sendRandomReading]);

  function toggleSimulation() {
    if (mode === "Running") {
      setMode("Paused");
      running.current = false;
      clearTimeout(timer.current);
    } else {
      setMode("Running");
      running.current = true;
    }
  }

  function stopSimulation() {
    setMode("Stopped");
    running.current = false;
    clearTimeout(timer.current);
  }

  const speedHz = (1000 / intervalMs).toFixed(1);

  return (
    <>
      <PageHead
        eyebrow="LIVE INGESTION / INPUT SIMULATION"
        title="Virtual IoT Monitoring Layer"
        description="Emulates large-scale smart meter traffic against the production ML pipeline."
      >
        <Badge>{mode}</Badge>
      </PageHead>

      <div className="simulation-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <Panel
          title="Simulation Control"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong>Status:</strong> 
              <Badge>{mode === 'Stopped' ? 'Simulator stopped' : `Simulator ${mode}`}</Badge>
            </div>
            
            <Resource resource={consumers} empty="No consumers found">
              {(rows) => (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <strong>Consumers monitored:</strong>
                  <span>{mode === 'Stopped' ? 0 : rows.length}</span>
                </div>
              )}
            </Resource>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong>Simulation speed/frequency:</strong>
              <span>{speedHz} readings/sec</span>
            </div>
            
            <label style={{ marginTop: '12px' }}>
              Speed adjustment (interval ms)
              <input 
                type="range" 
                min="100" 
                max="5000" 
                step="100"
                value={intervalMs}
                onChange={(e) => setIntervalMs(Number(e.target.value))}
                style={{ width: '100%', marginTop: '8px' }}
              />
            </label>

            <div className="actions sim-actions" style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
              <button
                className="primary"
                disabled={!!consumers.error || !consumers.data?.length}
                onClick={toggleSimulation}
              >
                {mode === "Running" ? "Pause" : "Start"}
              </button>
              <button
                disabled={mode === "Stopped"}
                onClick={stopSimulation}
              >
                Stop
              </button>
            </div>
          </div>
        </Panel>

        <Panel title="Real-time Metrics">
          <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="stat-card" style={{ padding: '16px', background: 'var(--bg)', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <small style={{ color: 'var(--muted)' }}>Readings generated</small>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.generated.toLocaleString()}</div>
            </div>
            <div className="stat-card" style={{ padding: '16px', background: 'var(--bg)', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <small style={{ color: 'var(--success, green)' }}>Successfully ingested</small>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.ingested.toLocaleString()}</div>
            </div>
            <div className="stat-card" style={{ padding: '16px', background: 'var(--bg)', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <small style={{ color: 'var(--danger, red)' }}>Rejected / Errors</small>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.rejected.toLocaleString()}</div>
            </div>
            <div className="stat-card" style={{ padding: '16px', background: 'var(--bg)', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <small style={{ color: 'var(--muted)' }}>Last reading timestamp</small>
              <div style={{ fontSize: '16px', fontWeight: 'bold', marginTop: '8px' }}>{timeAgo}</div>
            </div>
          </div>
        </Panel>

        <Panel
          title="Connected Grid topology"
          className="simulation-scene"
          aside={<span>CONCEPTUAL TOPOLOGY</span>}
        >
          <Suspense fallback={<div className="scene" />}>
            <GridScene pulse={pulse} consumer={lastResult?.payload?.consumer_id || ""} />
          </Suspense>
          <div className="route-legend">
            Consumer → Meter → Feeder → TraceWatt
          </div>
        </Panel>

        <Panel title="Ingestion Queue">
          {recentErrors.length > 0 && (
            <div className="error" role="alert" style={{ marginBottom: '16px' }}>
              <strong>Recent API Errors:</strong>
              <ul style={{ margin: '8px 0 0 16px', fontSize: '13px' }}>
                {recentErrors.map((err, i) => <li key={i}>{err}</li>)}
              </ul>
            </div>
          )}

          {lastResult ? (
            <div className="notice" role="status">
              <strong>
                {lastResult.ack.stored
                  ? "Reading stored successfully."
                  : "Reading not stored. Possibly rejected or duplicate."}
              </strong>
              <p>
                Consumer: {lastResult.payload.consumer_id} · {lastResult.payload.ts}
              </p>
              <p>
                kWh: {lastResult.payload.kwh} · V: {lastResult.payload.voltage}
              </p>
              <Pipeline ack={lastResult.ack} health={true} />
            </div>
          ) : (
            <p className="muted">No data has been generated in this session yet.</p>
          )}
        </Panel>
      </div>
    </>
  );
}
