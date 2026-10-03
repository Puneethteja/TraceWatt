import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  getDashboardSummary,
  getConsumptionTrend,
  getRiskDistribution,
  getRecentAlerts,
} from '../api/client';

function TrendTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-gray-200 text-xs p-2 shadow-sm rounded font-sans">
        <div className="font-mono text-gray-500 mb-1 border-b border-gray-100 pb-1">
          {label}
        </div>
        <div className="space-y-1">
          <div className="flex items-center justify-between space-x-3">
            <span className="text-gray-600">Actual:</span>
            <span className="font-mono font-semibold text-blue-600">
              {payload[0]?.value} kWh
            </span>
          </div>
          {payload[1] && (
            <div className="flex items-center justify-between space-x-3">
              <span className="text-gray-600">Baseline:</span>
              <span className="font-mono font-semibold text-gray-500">
                {payload[1]?.value} kWh
              </span>
            </div>
          )}
        </div>
      </div>
    );
  }
  return null;
}

function RiskBarTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-gray-200 text-xs p-2 shadow-sm rounded font-sans">
        <div className="font-medium text-gray-700">{label}</div>
        <div className="font-mono font-semibold text-gray-900 mt-1">
          {payload[0].value} consumers
        </div>
      </div>
    );
  }
  return null;
}

export default function DashboardHome() {
  const [summary, setSummary] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [riskData, setRiskData] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setError(null);

    Promise.all([
      getDashboardSummary(),
      getConsumptionTrend(),
      getRiskDistribution(),
      getRecentAlerts(5),
    ])
      .then(([summaryRes, trendRes, riskRes, alertsRes]) => {
        if (!isMounted) return;
        setSummary(summaryRes);
        setTrendData(Array.isArray(trendRes) ? trendRes : []);
        setRiskData(Array.isArray(riskRes) ? riskRes : []);
        setRecentAlerts(Array.isArray(alertsRes) ? alertsRes : []);
        setIsLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load dashboard data:', err);
        setError('Unable to load dashboard intelligence telemetry. Operating in offline mode.');
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return '#ef4444';
      case 'medium':
        return '#f59e0b';
      case 'low':
      default:
        return '#22c55e';
    }
  };

  const getRiskDotClass = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'bg-red-500';
      case 'medium':
        return 'bg-amber-500';
      case 'low':
      default:
        return 'bg-green-500';
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-2 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-gray-900">
            Energy Intelligence Dashboard
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Operational telemetry, non-technical loss analytics, and automated case triage.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-gray-500 bg-white border border-gray-200 px-2.5 py-1 rounded">
            Partition: Grid-Region-01
          </span>
        </div>
      </div>

      {/* Flat Inline Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-md mb-4">
          {error}
        </div>
      )}

      {/* 1. Summary Cards (4 Cards) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Card 1: Total Consumers */}
        <div className="bg-white border border-gray-200 rounded-md p-4 flex flex-col justify-between transition-all duration-200 ease-out hover:border-gray-300">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-500">Total Consumers</span>
            <span className="text-slate-400 text-base">👥</span>
          </div>
          <div>
            {isLoading ? (
              <span className="text-xs text-gray-400 animate-pulse">Loading data...</span>
            ) : summary ? (
              <div className="text-2xl font-semibold text-gray-900 font-mono">
                {summary.total_consumers?.toLocaleString()}
              </div>
            ) : (
              <span className="text-sm text-gray-500">No data available</span>
            )}
          </div>
        </div>

        {/* Card 2: Active Alerts */}
        <div className="bg-white border border-gray-200 rounded-md p-4 flex flex-col justify-between transition-all duration-200 ease-out hover:border-gray-300">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-500">Active Alerts</span>
            <span className="text-slate-400 text-base">⚠️</span>
          </div>
          <div>
            {isLoading ? (
              <span className="text-xs text-gray-400 animate-pulse">Loading data...</span>
            ) : summary ? (
              <div className="text-2xl font-semibold text-red-600 font-mono">
                {summary.active_alerts?.toLocaleString()}
              </div>
            ) : (
              <span className="text-sm text-gray-500">No data available</span>
            )}
          </div>
        </div>

        {/* Card 3: Open Cases */}
        <div className="bg-white border border-gray-200 rounded-md p-4 flex flex-col justify-between transition-all duration-200 ease-out hover:border-gray-300">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-500">Open Cases</span>
            <span className="text-slate-400 text-base">📋</span>
          </div>
          <div>
            {isLoading ? (
              <span className="text-xs text-gray-400 animate-pulse">Loading data...</span>
            ) : summary ? (
              <div className="text-2xl font-semibold text-amber-600 font-mono">
                {summary.open_cases?.toLocaleString()}
              </div>
            ) : (
              <span className="text-sm text-gray-500">No data available</span>
            )}
          </div>
        </div>

        {/* Card 4: Total Consumption */}
        <div className="bg-white border border-gray-200 rounded-md p-4 flex flex-col justify-between transition-all duration-200 ease-out hover:border-gray-300">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-500">Total Consumption</span>
            <span className="text-slate-400 text-base">⚡</span>
          </div>
          <div>
            {isLoading ? (
              <span className="text-xs text-gray-400 animate-pulse">Loading data...</span>
            ) : summary ? (
              <div className="text-2xl font-semibold text-gray-900 font-mono">
                {summary.total_consumption_kwh?.toLocaleString()} <span className="text-sm font-normal text-gray-500">kWh</span>
              </div>
            ) : (
              <span className="text-sm text-gray-500">No data available</span>
            )}
          </div>
        </div>
      </div>

      {/* 2. Analytics Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Consumption Trend Card (col-span-2) */}
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-md p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-3">
            <div>
              <h2 className="text-sm font-semibold text-gray-900 tracking-tight">
                Consumption Trend (14 Days)
              </h2>
              <p className="text-xs text-gray-500">
                Aggregated daily consumption vs. baseline model
              </p>
            </div>
            <div className="flex items-center space-x-3 text-xs text-gray-600">
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-0.5 bg-blue-600 inline-block"></span>
                <span>Actual</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-0.5 border-t border-dashed border-gray-400 inline-block"></span>
                <span>Baseline</span>
              </div>
            </div>
          </div>

          <div className="w-full h-[250px]">
            {isLoading ? (
              <div className="h-full flex items-center justify-center text-xs text-gray-400 animate-pulse">
                Loading data...
              </div>
            ) : trendData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-gray-500">
                No data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="#f3f4f6" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                    tick={{ fontSize: 10, fill: '#6b7280', fontFamily: 'monospace' }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                    tick={{ fontSize: 10, fill: '#6b7280', fontFamily: 'monospace' }}
                  />
                  <Tooltip content={<TrendTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={true}
                    animationDuration={400}
                  />
                  <Line
                    type="monotone"
                    dataKey="baseline"
                    stroke="#9ca3af"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={false}
                    isAnimationActive={true}
                    animationDuration={400}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Risk Distribution Card (col-span-1) */}
        <div className="lg:col-span-1 bg-white border border-gray-200 rounded-md p-5 flex flex-col justify-between">
          <div className="pb-3 border-b border-gray-100 mb-3">
            <h2 className="text-sm font-semibold text-gray-900 tracking-tight">
              Risk Distribution
            </h2>
            <p className="text-xs text-gray-500">
              Active consumer triage profiles
            </p>
          </div>

          <div className="w-full h-[200px]">
            {isLoading ? (
              <div className="h-full flex items-center justify-center text-xs text-gray-400 animate-pulse">
                Loading data...
              </div>
            ) : riskData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-gray-500">
                No data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskData} margin={{ top: 8, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid stroke="#f3f4f6" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                    tick={{ fontSize: 10, fill: '#6b7280' }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                    tick={{ fontSize: 10, fill: '#6b7280', fontFamily: 'monospace' }}
                  />
                  <Tooltip content={<RiskBarTooltip />} />
                  <Bar dataKey="value" radius={[2, 2, 0, 0]} isAnimationActive={true} animationDuration={400}>
                    {riskData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getRiskColor(entry.level)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Minimal breakdown legend */}
          <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-600 font-mono">
            {riskData.map((item) => (
              <div key={item.name} className="flex items-center space-x-1">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: getRiskColor(item.level) }}
                />
                <span>{item.level}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Alerts Panel (col-span-1) */}
        <div className="lg:col-span-1 bg-white border border-gray-200 rounded-md p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-2">
            <div>
              <h2 className="text-sm font-semibold text-gray-900 tracking-tight">
                Recent Alerts
              </h2>
              <p className="text-xs text-gray-500">Live IoT anomaly feed</p>
            </div>
            <Link
              to="/alerts"
              className="text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors"
            >
              View all →
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="py-8 text-center text-xs text-gray-400 animate-pulse">
                Loading data...
              </div>
            ) : recentAlerts.length === 0 ? (
              <div className="py-8 text-center text-sm text-gray-500">
                No data available
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {recentAlerts.map((alert) => (
                  <div key={alert.id} className="py-2.5 flex items-start space-x-2.5">
                    <span
                      className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${getRiskDotClass(
                        alert.risk_level
                      )}`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <Link
                          to={`/consumers/${alert.consumer_id}`}
                          className="font-mono text-xs text-blue-600 hover:underline font-semibold"
                        >
                          {alert.consumer_id}
                        </Link>
                        <span className="font-mono text-[10px] text-gray-400">
                          {alert.ts ? alert.ts.slice(11, 16) : ''}
                        </span>
                      </div>
                      <p className="text-xs text-gray-700 truncate mt-0.5">
                        {alert.message}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
