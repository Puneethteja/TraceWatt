import React from 'react';
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

/**
 * Custom flat utilitarian tooltip matching design guidelines:
 * bg-white border border-gray-200 text-xs p-2
 */
function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white border border-gray-200 text-xs p-2 rounded shadow-none font-sans">
        <div className="font-mono text-gray-500 mb-1 border-b border-gray-100 pb-1">
          {label}
        </div>
        <div className="space-y-1">
          <div className="flex items-center justify-between space-x-3">
            <span className="text-gray-600">Actual Usage:</span>
            <span className="font-mono font-semibold text-blue-600">
              {data.kwh} kWh
            </span>
          </div>
          <div className="flex items-center justify-between space-x-3">
            <span className="text-gray-600">Expected Baseline:</span>
            <span className="font-mono text-gray-700">
              {data.baseline_kwh} kWh
            </span>
          </div>
          <div className="flex items-center justify-between space-x-3">
            <span className="text-gray-600">Peer 25-75%:</span>
            <span className="font-mono text-gray-500">
              {data.peer_p25} - {data.peer_p75} kWh
            </span>
          </div>
        </div>
      </div>
    );
  }
  return null;
}

export default function ConsumptionChart({ data = [] }) {
  // Edge Case: Telemetry packet drops or communication gaps may return null/undefined for kwh.
  // Recharts SVG path generator can break or throw invalid NaN coords on null values.
  // We map null/undefined kwh values to 0 to safely indicate zero meter reading while preserving timeline continuity.
  const sanitizedData = (data || []).map((point) => {
    const kwhVal = point.kwh == null ? 0 : Number(point.kwh);
    const baseVal = point.baseline_kwh == null ? 0 : Number(point.baseline_kwh);
    const p25 = point.peer_p25 == null ? 0 : Number(point.peer_p25);
    const p75 = point.peer_p75 == null ? 0 : Number(point.peer_p75);

    return {
      ...point,
      kwh: kwhVal,
      baseline_kwh: baseVal,
      peer_p25: p25,
      peer_p75: p75,
      peer_band: point.peer_band || [p25, p75],
    };
  });

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col h-full font-sans">
      {/* Top Header & Custom Flat Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-gray-100 gap-2 mb-3">
        <div>
          <h3 className="text-xs font-semibold text-gray-900 uppercase tracking-wider tracking-tight">
            Daily Consumption vs. Baseline & Peer Band
          </h3>
          <p className="text-[11px] text-gray-500">
            30-day telemetry profile against synthetic seasonal model and peer quantile range.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center space-x-4 text-xs text-gray-600">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-sm bg-blue-500 inline-block"></span>
            <span>Actual Usage</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 border-t border-dashed border-gray-400 inline-block"></span>
            <span>Baseline</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-sm bg-gray-200 inline-block"></span>
            <span>Peer 25th-75th Band</span>
          </div>
        </div>
      </div>

      {/* Recharts Container with Engineering Graph Paper Background */}
      <div className="w-full h-[240px] bg-[linear-gradient(to_right,#f0f0f0_1px,transparent_1px),linear-gradient(to_bottom,#f0f0f0_1px,transparent_1px)] bg-[size:20px_20px] border border-gray-200 rounded-md p-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={sanitizedData}
            margin={{ top: 8, right: 12, left: -16, bottom: 0 }}
          >
            <CartesianGrid stroke="#f3f4f6" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="ts"
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
              tick={{ fontSize: 10, fill: '#6b7280', fontFamily: 'monospace' }}
              tickFormatter={(v) => v.slice(5)} // Show MM-DD
            />
            <YAxis
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
              tick={{ fontSize: 10, fill: '#6b7280', fontFamily: 'monospace' }}
            />
            <Tooltip content={<CustomTooltip />} />
            {/* Peer Band Fill */}
            <Area
              type="monotone"
              dataKey="peer_band"
              stroke="none"
              fill="#e5e7eb"
              fillOpacity={0.8}
              isAnimationActive={true}
              animationDuration={400}
            />
            {/* Baseline Dashed Line */}
            <Line
              type="monotone"
              dataKey="baseline_kwh"
              stroke="#9ca3af"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              dot={false}
              isAnimationActive={true}
              animationDuration={400}
            />
            {/* Actual Consumption Solid Blue Line */}
            <Line
              type="monotone"
              dataKey="kwh"
              stroke="#3b82f6"
              strokeWidth={1.5}
              dot={{ r: 2, fill: '#3b82f6' }}
              activeDot={{ r: 4, fill: '#2563eb' }}
              isAnimationActive={true}
              animationDuration={400}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
