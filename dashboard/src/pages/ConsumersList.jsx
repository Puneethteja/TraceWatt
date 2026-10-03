import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { getConsumers } from '../api/client';
import CaseDetailDrawer from '../components/CaseDetailDrawer';
import ExportMenu from '../components/ExportMenu';

export default function ConsumersList() {
  const [consumers, setConsumers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [selectedConsumerId, setSelectedConsumerId] = useState(null);
  const [riskFilter, setRiskFilter] = useState('All');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [feederFilter, setFeederFilter] = useState('All');

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setErrorMessage('');

    getConsumers()
      .then((data) => {
        if (!isMounted) return;
        setConsumers(Array.isArray(data) ? data : []);
        setIsLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load consumers:', err);
        setErrorMessage('Unable to connect to backend server. Operating in offline mode.');
        setConsumers([]);
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Extract unique options for dropdowns
  const categories = useMemo(() => {
    return ['All', ...Array.from(new Set(consumers.map((c) => c.category).filter(Boolean)))];
  }, [consumers]);

  const feeders = useMemo(() => {
    return ['All', ...Array.from(new Set(consumers.map((c) => c.feeder_id).filter(Boolean)))];
  }, [consumers]);

  // Filtered consumers based on selections
  const filteredConsumers = useMemo(() => {
    return consumers.filter((c) => {
      const matchRisk = riskFilter === 'All' || c.risk_level?.toLowerCase() === riskFilter.toLowerCase();
      const matchCategory = categoryFilter === 'All' || c.category?.toLowerCase() === categoryFilter.toLowerCase();
      const matchFeeder = feederFilter === 'All' || c.feeder_id === feederFilter;
      return matchRisk && matchCategory && matchFeeder;
    });
  }, [consumers, riskFilter, categoryFilter, feederFilter]);

  const getRiskBadge = (risk) => {
    switch (risk?.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-700';
      case 'medium':
        return 'bg-amber-100 text-amber-700';
      case 'low':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-4 max-w-6xl mx-auto font-sans">
      {/* Top Error Banner (if API call fails) */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-2 rounded">
          {errorMessage}
        </div>
      )}

      {/* Page Title & Filter Bar with ExportMenu */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900 tracking-tight">Consumer Anomaly Registry</h2>
            <p className="text-xs text-gray-500">
              Select any row for drawer inspection, or click Consumer ID for full explainability deep-dive.
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <ExportMenu
              filters={{ risk: riskFilter, category: categoryFilter, feeder: feederFilter }}
              filenamePrefix="consumers_registry"
            />
          </div>
        </div>

        {/* Filters Top Bar */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-gray-100 text-sm">
          <div className="flex items-center space-x-1.5">
            <label htmlFor="filter-risk" className="text-xs font-medium text-gray-600">
              Risk Level:
            </label>
            <select
              id="filter-risk"
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-2 py-1 text-sm bg-white text-gray-700 focus:outline-none focus:border-blue-600"
            >
              <option value="All">All Risks</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5">
            <label htmlFor="filter-category" className="text-xs font-medium text-gray-600">
              Category:
            </label>
            <select
              id="filter-category"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-2 py-1 text-sm bg-white text-gray-700 focus:outline-none focus:border-blue-600"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat === 'All' ? 'All Categories' : cat}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-1.5">
            <label htmlFor="filter-feeder" className="text-xs font-medium text-gray-600">
              Feeder:
            </label>
            <select
              id="filter-feeder"
              value={feederFilter}
              onChange={(e) => setFeederFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-2 py-1 text-sm bg-white text-gray-700 focus:outline-none focus:border-blue-600"
            >
              {feeders.map((fdr) => (
                <option key={fdr} value={fdr}>
                  {fdr === 'All' ? 'All Feeders' : fdr}
                </option>
              ))}
            </select>
          </div>

          {(riskFilter !== 'All' || categoryFilter !== 'All' || feederFilter !== 'All') && (
            <button
              onClick={() => {
                setRiskFilter('All');
                setCategoryFilter('All');
                setFeederFilter('All');
              }}
              className="text-xs text-blue-600 hover:text-blue-800 underline ml-auto cursor-pointer transition-colors duration-150"
            >
              Reset filters
            </button>
          )}

          <div className="text-xs font-mono text-gray-500 ml-auto hidden sm:block">
            {filteredConsumers.length} records
          </div>
        </div>
      </div>

      {/* Functional Data Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-gray-500">Loading data...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-600 border-collapse">
              <thead className="bg-gray-50 text-gray-700 font-medium text-xs border-b border-gray-200">
                <tr>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Priority Rank</th>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Consumer ID</th>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Category</th>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Risk Level</th>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Cause</th>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Estimated Loss</th>
                  <th className="py-2.5 px-3.5 uppercase tracking-wider text-[11px] font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredConsumers.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="py-8 text-center text-xs text-gray-500">
                      No consumers found matching selected filters.
                    </td>
                  </tr>
                ) : (
                  filteredConsumers.map((item) => {
                    const isSelected = selectedConsumerId === item.consumer_id;
                    return (
                      <tr
                        key={item.consumer_id}
                        onClick={() => setSelectedConsumerId(item.consumer_id)}
                        className={`cursor-pointer transition-colors duration-150 ${
                          isSelected
                            ? 'border-l-2 border-blue-600 bg-gray-50'
                            : 'border-l-2 border-transparent'
                        }`}
                      >
                        <td className="py-2.5 px-3.5 font-mono text-xs text-gray-600">
                          {item.priority_rank != null ? `#${item.priority_rank}` : '-'}
                        </td>
                        <td className="py-2.5 px-3.5">
                          <Link
                            to={`/consumers/${item.consumer_id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="text-blue-600 hover:underline font-mono text-xs font-semibold"
                          >
                            {item.consumer_id || '-'}
                          </Link>
                        </td>
                        <td className="py-2.5 px-3.5 text-xs text-gray-700">
                          {item.category || '-'}
                        </td>
                        <td className="py-2.5 px-3.5">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${getRiskBadge(
                              item.risk_level
                            )}`}
                          >
                            {item.risk_level || '-'}
                          </span>
                        </td>
                        <td className="py-2.5 px-3.5 text-xs text-gray-800">
                          {item.cause || '-'}
                        </td>
                        <td className="py-2.5 px-3.5 font-mono text-xs text-gray-600 font-medium">
                          {item.estimated_loss != null
                            ? `₹${item.estimated_loss.toLocaleString('en-IN')}`
                            : '-'}
                        </td>
                        <td className="py-2.5 px-3.5">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-gray-100 text-gray-700 border border-gray-200">
                            {item.status || '-'}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Case Detail Slide-over Drawer */}
      {selectedConsumerId && (
        <CaseDetailDrawer
          consumerId={selectedConsumerId}
          onClose={() => setSelectedConsumerId(null)}
        />
      )}
    </div>
  );
}
