import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  BarChart,
  Bar,
  ReferenceLine,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { getFeeders, getFeederLosses, getConsumers } from '../api/client';

function CustomBarTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 text-xs p-2 rounded shadow-none font-sans">
        <div className="font-mono text-gray-500 dark:text-slate-400 mb-1 border-b border-gray-100 dark:border-slate-800 pb-1">
          Window: {label}
        </div>
        <div className="space-y-1">
          <div className="flex items-center justify-between space-x-3">
            <span className="text-gray-600 dark:text-slate-300">Energy In:</span>
            <span className="font-mono font-semibold text-blue-600 dark:text-blue-400">
              {data.energy_in_kwh != null ? `${data.energy_in_kwh.toLocaleString()} kWh` : '-'}
            </span>
          </div>
          <div className="flex items-center justify-between space-x-3">
            <span className="text-gray-600 dark:text-slate-300">Energy Metered:</span>
            <span className="font-mono font-semibold text-gray-600 dark:text-slate-300">
              {data.energy_metered_kwh != null ? `${data.energy_metered_kwh.toLocaleString()} kWh` : '-'}
            </span>
          </div>
          <div className="flex items-center justify-between space-x-3">
            <span className="text-gray-600 dark:text-slate-300">Unexplained Loss:</span>
            <span className="font-mono font-bold text-red-600 dark:text-red-400">
              {data.unexplained_loss_pct != null ? `${data.unexplained_loss_pct}%` : '-'}
            </span>
          </div>
        </div>
      </div>
    );
  }
  return null;
}

export default function FeederDetailView() {
  const { id } = useParams();

  const [feeder, setFeeder] = useState(null);
  const [losses, setLosses] = useState([]);
  const [clusterConsumers, setClusterConsumers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setErrorMessage('');

    Promise.all([
      getFeeders(),
      getFeederLosses(id),
      getConsumers({ feeder_id: id }),
    ])
      .then(([feedersRes, lossesRes, consumersRes]) => {
        if (!isMounted) return;
        const matchedFeeder = (feedersRes || []).find((f) => f.feeder_id === id) || {
          feeder_id: id,
          name: 'Distribution Feeder Network',
          transformer_count: 8,
          total_unexplained_loss_pct: null,
          cluster_flag: false,
        };
        setFeeder(matchedFeeder);
        setLosses(Array.isArray(lossesRes) ? lossesRes : []);
        setClusterConsumers(Array.isArray(consumersRes) ? consumersRes : []);
        setIsLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load feeder details:', err);
        setErrorMessage('Unable to connect to backend server. Operating in offline mode.');
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [id]);

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto py-12 text-center font-sans text-xs text-gray-500 dark:text-slate-400">
        Loading data...
      </div>
    );
  }

  // Calculate average unexplained loss pct
  const avgLossPct =
    losses.length > 0
      ? (
          losses.reduce((sum, item) => sum + (item.unexplained_loss_pct || 0), 0) /
          losses.length
        ).toFixed(1)
      : feeder?.total_unexplained_loss_pct != null
      ? feeder.total_unexplained_loss_pct
      : null;

  const totalIn = losses.reduce((sum, item) => sum + (item.energy_in_kwh || 0), 0);
  const totalMetered = losses.reduce(
    (sum, item) => sum + (item.energy_metered_kwh || 0),
    0
  );

  // Check if any monitoring window exceeds 10% unexplained loss
  const hasSignificantLoss = losses.some((l) => (l.unexplained_loss_pct || 0) > 10);
  const lossGapThreshold =
    losses.length > 0
      ? Math.round(losses.reduce((acc, l) => acc + (l.energy_in_kwh || 0), 0) / losses.length)
      : 0;

  return (
    <div className="space-y-5 max-w-6xl mx-auto font-sans">
      {/* Inline Flat Error Banner */}
      {errorMessage && (
        <div className="bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-xs p-2 rounded">
          {errorMessage}
        </div>
      )}

      {/* Header Bar */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <Link
            to="/feeders"
            className="bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-700 text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-700 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150"
          >
            ← Back to Feeders
          </Link>
          <div className="h-4 w-px bg-gray-200 dark:bg-slate-800 hidden sm:block" />
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-mono text-base font-bold text-gray-900 dark:text-slate-100">
                {feeder?.feeder_id || id}
              </span>
              <span className="text-xs text-gray-600 dark:text-slate-300 font-medium">
                {feeder?.name || 'Feeder'}
              </span>
              {feeder?.cluster_flag && (
                <span className="bg-red-100 dark:bg-red-950/60 text-red-700 dark:text-red-400 text-xs px-2 py-0.5 rounded-sm font-medium">
                  Theft Cluster Active
                </span>
              )}
            </div>
            <div className="text-xs text-gray-500 dark:text-slate-400 mt-0.5 space-x-2 font-mono">
              <span>Transformers: {feeder?.transformer_count != null ? feeder.transformer_count : '-'} units</span>
              <span>•</span>
              <span>Telemetry: Active</span>
            </div>
          </div>
        </div>

        <div className="text-xs text-gray-500 dark:text-slate-400 font-mono text-left sm:text-right">
          Grid Telemetry: Operational
        </div>
      </div>

      {/* Section 1: Energy Balance Chart */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-gray-100 dark:border-slate-800 gap-2 mb-3">
          <div>
            <h3 className="text-xs font-semibold text-gray-900 dark:text-slate-100 uppercase tracking-wider tracking-tight">
              Feeder Energy Balance (Intake vs. Metered)
            </h3>
            <p className="text-[11px] text-gray-500 dark:text-slate-400">
              Comparative reconciliation per 5-day monitoring window. Significant delta indicates non-technical losses.
            </p>
          </div>

          <div className="flex items-center space-x-4 text-xs text-gray-600 dark:text-slate-300">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-sm bg-blue-500 inline-block"></span>
              <span>Energy In</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-sm bg-gray-400 inline-block"></span>
              <span>Energy Metered</span>
            </div>
            {hasSignificantLoss && (
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-0.5 border-t border-dashed border-red-500 inline-block"></span>
                <span className="text-red-600 dark:text-red-400 font-medium">Gap (&gt;10%)</span>
              </div>
            )}
          </div>
        </div>

        {losses.length === 0 ? (
          <div className="py-12 text-center text-xs text-gray-500 dark:text-slate-400">
            No energy reconciliation data recorded for this feeder.
          </div>
        ) : (
          <div className="w-full h-[260px] bg-[linear-gradient(to_right,#f0f0f0_1px,transparent_1px),linear-gradient(to_bottom,#f0f0f0_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] dark:bg-slate-950 bg-[size:20px_20px] border border-gray-200 dark:border-slate-800 rounded-md p-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={losses}
                margin={{ top: 8, right: 12, left: -10, bottom: 0 }}
                barGap={4}
              >
                <CartesianGrid stroke="#f3f4f6" strokeDasharray="3 3" vertical={false} className="dark:opacity-10" />
                <XAxis
                  dataKey="window_start"
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                  tick={{ fontSize: 10, fill: '#6b7280', fontFamily: 'monospace' }}
                />
                <YAxis
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                  tick={{ fontSize: 10, fill: '#6b7280', fontFamily: 'monospace' }}
                />
                <Tooltip content={<CustomBarTooltip />} />
                {hasSignificantLoss && lossGapThreshold > 0 && (
                  <ReferenceLine
                    y={lossGapThreshold}
                    stroke="#ef4444"
                    strokeDasharray="3 3"
                    label={{
                      value: 'Loss Gap (>10%)',
                      fill: '#ef4444',
                      fontSize: 10,
                      fontFamily: 'monospace',
                      position: 'top',
                    }}
                  />
                )}
                <Bar
                  dataKey="energy_in_kwh"
                  fill="#3b82f6"
                  radius={[2, 2, 0, 0]}
                  isAnimationActive={true}
                  animationDuration={400}
                />
                <Bar
                  dataKey="energy_metered_kwh"
                  fill="#9ca3af"
                  radius={[2, 2, 0, 0]}
                  isAnimationActive={true}
                  animationDuration={400}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Grid: Section 2 & Section 3 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Section 2: Loss Metrics Card */}
        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg p-4 space-y-4">
          <div>
            <h3 className="text-xs font-semibold text-gray-900 dark:text-slate-100 uppercase tracking-wider mb-2">
              Loss Metrics
            </h3>
            <div className="border border-gray-200 dark:border-slate-800 rounded-md p-3 bg-gray-50/50 dark:bg-slate-800/40 cursor-pointer transition-all duration-200 ease-out hover:border-slate-600 hover:bg-slate-800/40 active:scale-[0.995]">
              <div className="text-[11px] text-gray-500 dark:text-slate-400 font-medium uppercase tracking-wide">
                Average Unexplained Loss
              </div>
              <div className="font-mono text-2xl text-gray-900 dark:text-slate-100 font-bold mt-1">
                {avgLossPct != null ? `${avgLossPct}%` : '-'}
              </div>
              <div className="text-[11px] text-red-600 dark:text-red-400 font-medium mt-1">
                {avgLossPct != null && avgLossPct > 8
                  ? 'Exceeds acceptable grid threshold (8.0%)'
                  : 'Within acceptable operating variance'}
              </div>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1.5 border-b border-gray-100 dark:border-slate-800">
              <span className="text-gray-600 dark:text-slate-400">Total Energy In:</span>
              <span className="font-mono font-medium text-gray-900 dark:text-slate-200">
                {totalIn > 0 ? `${totalIn.toLocaleString()} kWh` : '-'}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-gray-100 dark:border-slate-800">
              <span className="text-gray-600 dark:text-slate-400">Total Metered:</span>
              <span className="font-mono font-medium text-gray-900 dark:text-slate-200">
                {totalMetered > 0 ? `${totalMetered.toLocaleString()} kWh` : '-'}
              </span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-gray-600 dark:text-slate-400">Unaccounted Delta:</span>
              <span className="font-mono font-semibold text-red-600 dark:text-red-400">
                {totalIn - totalMetered > 0
                  ? `${(totalIn - totalMetered).toLocaleString()} kWh`
                  : '-'}
              </span>
            </div>
          </div>
        </div>

        {/* Section 3: Cluster Correlation */}
        <div className="md:col-span-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-slate-800 mb-3">
            <div>
              <h3 className="text-xs font-semibold text-gray-900 dark:text-slate-100 uppercase tracking-wider">
                High-Scoring Consumers on this Feeder
              </h3>
              <p className="text-[11px] text-gray-500 dark:text-slate-400">
                Correlated consumers exhibiting abnormal telemetry drops matching the feeder loss window.
              </p>
            </div>
            {feeder?.cluster_flag && (
              <span className="bg-red-100 dark:bg-red-950/60 text-red-700 dark:text-red-400 text-xs px-2 py-0.5 rounded-sm font-medium">
                Cluster Flag &gt; 0
              </span>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-600 dark:text-slate-400 border-collapse">
              <thead className="bg-gray-50 dark:bg-slate-800/70 text-gray-700 dark:text-slate-300 font-medium text-xs border-b border-gray-200 dark:border-slate-800">
                <tr>
                  <th className="py-2 px-3 uppercase tracking-wider text-[11px] font-semibold">Consumer ID</th>
                  <th className="py-2 px-3 uppercase tracking-wider text-[11px] font-semibold">Anomaly Score</th>
                  <th className="py-2 px-3 uppercase tracking-wider text-[11px] font-semibold">Estimated Loss</th>
                  <th className="py-2 px-3 uppercase tracking-wider text-[11px] font-semibold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-800 text-xs">
                {clusterConsumers.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="py-8 text-center text-xs text-gray-500 dark:text-slate-400">
                      No correlated anomalous consumers detected on this feeder.
                    </td>
                  </tr>
                ) : (
                  clusterConsumers.map((c) => (
                    <tr key={c.consumer_id} className="hover:bg-gray-50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-2 px-3">
                        <Link
                          to={`/consumers/${c.consumer_id}`}
                          className="text-blue-600 dark:text-blue-400 hover:underline font-mono text-xs font-semibold"
                        >
                          {c.consumer_id || '-'}
                        </Link>
                      </td>
                      <td className="py-2 px-3 font-mono font-medium text-gray-800 dark:text-slate-200">
                        {c.anomaly_score != null ? `${(c.anomaly_score * 100).toFixed(0)}%` : '-'}
                      </td>
                      <td className="py-2 px-3 font-mono font-semibold text-red-600 dark:text-red-400">
                        {c.estimated_loss != null ? `₹${c.estimated_loss.toLocaleString('en-IN')}` : '-'}
                      </td>
                      <td className="py-2 px-3">
                        <Link
                          to={`/consumers/${c.consumer_id}`}
                          className="text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 underline text-[11px]"
                        >
                          View Case Details →
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
