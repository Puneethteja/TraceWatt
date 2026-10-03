import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getConsumers, getFeeders } from '../api/client';
import ExportMenu from '../components/ExportMenu';

export default function DashboardHome() {
  const [consumers, setConsumers] = useState([]);
  const [feeders, setFeeders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setErrorMessage('');

    Promise.all([getConsumers(), getFeeders()])
      .then(([consumersRes, feedersRes]) => {
        if (!isMounted) return;
        setConsumers(Array.isArray(consumersRes) ? consumersRes : []);
        setFeeders(Array.isArray(feedersRes) ? feedersRes : []);
        setIsLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load dashboard overview data:', err);
        setErrorMessage('Unable to connect to backend server. Operating in offline mode.');
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const highRiskCount = consumers.filter((c) => c.risk_level === 'High').length;
  const totalLoss = consumers.reduce((acc, curr) => acc + (curr.estimated_loss || 0), 0);
  const flaggedFeedersCount = feeders.filter(
    (f) => f.cluster_flag || (f.total_unexplained_loss_pct || 0) > 15
  ).length;

  return (
    <div className="space-y-5 max-w-6xl mx-auto font-sans">
      {/* Inline Flat Error Banner */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-2 rounded">
          {errorMessage}
        </div>
      )}

      {/* Overview Card with ExportMenu */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
                Phase 6 Production Ready
              </span>
              <span className="text-xs text-gray-400 font-mono">Build 2026.10</span>
            </div>
            <h2 className="text-lg font-semibold text-gray-900 tracking-tight">
              TraceWatt Overview
            </h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Electricity theft detection, transformer reconciliation, and IoT alert monitoring.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <ExportMenu filenamePrefix="tracewatt_system_summary" />
            <div className="flex items-center space-x-2 shrink-0">
              <Link
                to="/consumers"
                className="bg-blue-600 text-white hover:bg-blue-700 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150"
              >
                Flagged Consumers
              </Link>
              <Link
                to="/feeders"
                className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150"
              >
                Feeder Losses
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      {isLoading ? (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center text-xs text-gray-500">
          Loading data...
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Flagged Consumers
            </div>
            <div className="mt-1 text-2xl font-bold font-mono text-gray-900">
              {consumers.length > 0 ? consumers.length : '-'}
            </div>
            <div className="mt-1 text-xs text-red-600 font-medium flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 mr-1.5"></span>
              {highRiskCount} classified as High Risk
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Est. Non-Technical Loss
            </div>
            <div className="mt-1 text-2xl font-bold font-mono text-gray-900">
              {totalLoss > 0 ? `₹${totalLoss.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '-'}
            </div>
            <div className="mt-1 text-xs text-gray-500">
              Across {feeders.length > 0 ? feeders.length : '-'} distribution feeders
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Theft Feeder Clusters
            </div>
            <div className="mt-1 text-2xl font-bold font-mono text-amber-600">
              {flaggedFeedersCount > 0 ? flaggedFeedersCount : '-'}
            </div>
            <div className="mt-1 text-xs text-gray-500">
              Transformers exceeding loss threshold
            </div>
          </div>
        </div>
      )}

      {/* System Specifications */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-xs font-semibold text-gray-900 uppercase tracking-wider mb-2.5">
          Backend API & Service Endpoints
        </h3>
        <div className="divide-y divide-gray-100 text-xs">
          <div className="py-2 flex items-center justify-between">
            <span className="text-gray-600">Active API Base URL</span>
            <span className="font-mono text-gray-700 bg-gray-100 px-1.5 py-0.5 rounded">
              {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
            </span>
          </div>
          <div className="py-2 flex items-center justify-between">
            <span className="text-gray-600">WebSocket Alert Stream</span>
            <span className="font-mono text-gray-700 bg-gray-100 px-1.5 py-0.5 rounded">
              {import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/alerts
            </span>
          </div>
          <div className="py-2 flex items-center justify-between">
            <span className="text-gray-600">Report Export Service</span>
            <span className="font-mono text-gray-700 bg-gray-100 px-1.5 py-0.5 rounded">
              GET /export?format=csv|json|pdf
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
