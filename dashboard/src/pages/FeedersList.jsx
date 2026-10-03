import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getFeeders } from '../api/client';

export default function FeedersList() {
  const navigate = useNavigate();
  const [feeders, setFeeders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setErrorMessage('');

    getFeeders()
      .then((data) => {
        if (!isMounted) return;
        setFeeders(Array.isArray(data) ? data : []);
        setIsLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load feeders:', err);
        setErrorMessage('Unable to connect to backend server. Operating in offline mode.');
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="space-y-4 max-w-6xl mx-auto font-sans">
      {/* Inline Flat Error Banner */}
      {errorMessage && (
        <div className="bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-xs p-2 rounded">
          {errorMessage}
        </div>
      )}

      {/* Top Bar Header */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-gray-900 dark:text-slate-100">Feeder Overview</h2>
          <p className="text-xs text-gray-500 dark:text-slate-400">
            Grid distribution feeder telemetry, aggregate energy losses, and transformer cluster diagnostics.
          </p>
        </div>
        <div className="text-xs font-mono text-gray-500 dark:text-slate-400 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded px-2.5 py-1">
          {feeders.length} Active Feeders
        </div>
      </div>

      {/* Functional Feeder Data Table */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-gray-500 dark:text-slate-400">Loading data...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-600 dark:text-slate-400 border-collapse">
              <thead className="bg-gray-50 dark:bg-slate-800/70 text-gray-700 dark:text-slate-300 font-medium text-xs border-b border-gray-200 dark:border-slate-800">
                <tr>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Feeder ID</th>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Name</th>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Transformer Count</th>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Total Unexplained Loss %</th>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-800">
                {feeders.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="py-8 text-center text-xs text-gray-500 dark:text-slate-400">
                      No distribution feeders recorded.
                    </td>
                  </tr>
                ) : (
                  feeders.map((item) => (
                    <tr
                      key={item.feeder_id}
                      onClick={() => navigate(`/feeders/${item.feeder_id}`)}
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="py-2.5 px-3.5">
                        <Link
                          to={`/feeders/${item.feeder_id}`}
                          className="text-blue-600 dark:text-blue-400 hover:underline font-mono text-xs font-semibold"
                        >
                          {item.feeder_id || '-'}
                        </Link>
                      </td>
                      <td className="py-2.5 px-3.5 text-xs text-gray-800 dark:text-slate-200 font-medium">
                        {item.name || '-'}
                      </td>
                      <td className="py-2.5 px-3.5 font-mono text-xs text-gray-700 dark:text-slate-300">
                        {item.transformer_count != null ? `${item.transformer_count} units` : '-'}
                      </td>
                      <td className="py-2.5 px-3.5 font-mono text-xs font-semibold text-red-600 dark:text-red-400">
                        {item.total_unexplained_loss_pct != null
                          ? `${item.total_unexplained_loss_pct}%`
                          : item.unexplained_loss_pct != null
                          ? `${item.unexplained_loss_pct}%`
                          : '-'}
                      </td>
                      <td className="py-2.5 px-3.5">
                        {item.cluster_flag ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-red-100 dark:bg-red-950/60 text-red-700 dark:text-red-400">
                            Suspicious Cluster
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-green-100 dark:bg-green-950/60 text-green-700 dark:text-green-400">
                            Balanced
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
