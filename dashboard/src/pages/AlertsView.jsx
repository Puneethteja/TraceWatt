import React, { useState, useEffect } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import { getAlerts } from '../api/client';

export default function AlertsView(props) {
  const outletContext = useOutletContext();
  const fallbackWs = useWebSocket();

  const liveAlerts = props.alerts || outletContext?.alerts || fallbackWs.alerts || [];
  const clearAlerts = props.clearAlerts || outletContext?.clearAlerts || fallbackWs.clearAlerts;
  const connectionStatus = props.connectionStatus || fallbackWs.connectionStatus || 'connected';

  const [initialAlerts, setInitialAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setErrorMessage('');

    getAlerts()
      .then((data) => {
        if (!isMounted) return;
        if (Array.isArray(data)) {
          setInitialAlerts(data);
        }
        setIsLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load past alerts:', err);
        setErrorMessage('Unable to connect to alerts API. Live WebSocket feed is active.');
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Merge live incoming alerts with initial fetched alerts, de-duplicating by ID
  const allAlerts = [...liveAlerts];
  initialAlerts.forEach((initAlert) => {
    if (!allAlerts.some((a) => a.id === initAlert.id)) {
      allAlerts.push(initAlert);
    }
  });

  const getRiskDot = (risk) => {
    switch (risk?.toLowerCase()) {
      case 'high':
        return 'bg-red-500';
      case 'medium':
        return 'bg-amber-500';
      default:
        return 'bg-gray-400';
    }
  };

  const isConnected = connectionStatus === 'connected';

  return (
    <div className="space-y-4 max-w-5xl mx-auto font-sans">
      {/* Inline Flat Error Banner */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-2 rounded">
          {errorMessage}
        </div>
      )}

      {/* Top Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-base font-semibold text-gray-900 tracking-tight">Live Alerts Feed</h2>
            <span className="inline-flex items-center text-xs text-gray-500 font-medium">
              <span
                className={`w-2 h-2 rounded-full mr-1.5 ${
                  isConnected ? 'bg-green-500 ring-2 ring-green-500/30' : 'bg-amber-500 ring-2 ring-amber-500/30'
                }`}
              />
              {isConnected ? 'Connected' : connectionStatus}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            Continuous stream of IoT smart meter tamper events, loss spikes, and model anomalies.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-xs font-mono text-gray-500 bg-gray-50 border border-gray-200 rounded px-2.5 py-1">
            {allAlerts.length} Total Alerts
          </span>
          {allAlerts.length > 0 && (
            <button
              onClick={() => {
                clearAlerts();
                setInitialAlerts([]);
              }}
              className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150 cursor-pointer"
            >
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* Feed List Container */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
        {isLoading && allAlerts.length === 0 ? (
          <div className="py-12 text-center text-xs text-gray-500">Loading data...</div>
        ) : allAlerts.length === 0 ? (
          <div className="py-16 text-center text-sm text-gray-500">
            No active alerts. System is monitoring.
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {allAlerts.map((alert) => (
              <div
                key={alert.id}
                className="bg-white p-4 hover:bg-gray-50 transition-colors flex items-start justify-between gap-4"
              >
                {/* Left side: Status Indicator Dot */}
                <div className="flex items-start space-x-3 flex-1 min-w-0">
                  <div
                    className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${getRiskDot(
                      alert.risk_level
                    )}`}
                    title={`${alert.risk_level || 'Alert'} Risk`}
                  />

                  {/* Middle: Message & Cause */}
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <p className="text-sm text-gray-900 leading-snug">
                      {alert.message || '-'}
                    </p>
                    <div className="flex items-center space-x-2">
                      <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-sm font-medium inline-block">
                        {alert.cause || 'Anomaly'}
                      </span>
                      <span className="text-[11px] font-mono text-gray-400">
                        {alert.id}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Right side: Consumer ID & Timestamp */}
                <div className="flex flex-col items-end shrink-0 space-y-1">
                  <Link
                    to={`/consumers/${alert.consumer_id}`}
                    className="font-mono text-xs text-blue-600 hover:underline font-semibold"
                  >
                    {alert.consumer_id || '-'}
                  </Link>
                  <span className="font-mono text-xs text-gray-400">
                    {alert.ts || '-'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
