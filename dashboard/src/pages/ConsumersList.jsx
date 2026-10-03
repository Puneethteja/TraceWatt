import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getConsumers } from '../api/client';
import ExportMenu from '../components/ExportMenu';
import FieldInspectionModal from '../components/FieldInspectionModal';

export default function ConsumersList() {
  const navigate = useNavigate();
  const [consumers, setConsumers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('All');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [feederFilter, setFeederFilter] = useState('All');
  const [dispatchConsumer, setDispatchConsumer] = useState(null);
  const [toastMessage, setToastMessage] = useState('');

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

  // Filtered consumers based on selections and search query
  const filteredConsumers = useMemo(() => {
    return consumers.filter((c) => {
      const matchSearch =
        !searchQuery ||
        c.consumer_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.cause?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.category?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchRisk = riskFilter === 'All' || c.risk_level?.toLowerCase() === riskFilter.toLowerCase();
      const matchCategory = categoryFilter === 'All' || c.category?.toLowerCase() === categoryFilter.toLowerCase();
      const matchFeeder = feederFilter === 'All' || c.feeder_id === feederFilter;
      return matchSearch && matchRisk && matchCategory && matchFeeder;
    });
  }, [consumers, searchQuery, riskFilter, categoryFilter, feederFilter]);

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
    <div className="space-y-4 max-w-7xl mx-auto font-sans">
      {/* Top Error Banner */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-md">
          {errorMessage}
        </div>
      )}

      {/* Top Bar with Search & Filter Dropdowns */}
      <div className="bg-white border border-gray-200 rounded-md p-4 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-base font-semibold text-gray-900 tracking-tight">
              Consumer Anomaly Registry
            </h1>
            <p className="text-xs text-gray-500">
              Meter telemetry triage. Click any consumer row to view detailed explainability and baseline curves.
            </p>
          </div>
          <ExportMenu
            filters={{ risk: riskFilter, category: categoryFilter, feeder: feederFilter }}
            filenamePrefix="consumers_registry"
          />
        </div>

        {/* Search input and Filter dropdowns */}
        <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-gray-100 text-sm">
          {/* Search Input */}
          <div className="flex-1 min-w-[220px]">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search consumer ID, category, or cause..."
              className="bg-white border border-gray-200 rounded-md px-3 py-1.5 text-sm w-full focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 placeholder-gray-400"
            />
          </div>

          {/* Risk Level Filter */}
          <div className="flex items-center space-x-1.5">
            <label htmlFor="filter-risk" className="text-xs font-medium text-gray-600">
              Risk:
            </label>
            <select
              id="filter-risk"
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-white border border-gray-200 rounded-md px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="All">All Risks</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          {/* Category Filter */}
          <div className="flex items-center space-x-1.5">
            <label htmlFor="filter-category" className="text-xs font-medium text-gray-600">
              Category:
            </label>
            <select
              id="filter-category"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-white border border-gray-200 rounded-md px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat === 'All' ? 'All Categories' : cat}
                </option>
              ))}
            </select>
          </div>

          {/* Feeder Filter */}
          <div className="flex items-center space-x-1.5">
            <label htmlFor="filter-feeder" className="text-xs font-medium text-gray-600">
              Feeder:
            </label>
            <select
              id="filter-feeder"
              value={feederFilter}
              onChange={(e) => setFeederFilter(e.target.value)}
              className="bg-white border border-gray-200 rounded-md px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {feeders.map((fdr) => (
                <option key={fdr} value={fdr}>
                  {fdr === 'All' ? 'All Feeders' : fdr}
                </option>
              ))}
            </select>
          </div>

          {(searchQuery || riskFilter !== 'All' || categoryFilter !== 'All' || feederFilter !== 'All') && (
            <button
              onClick={() => {
                setSearchQuery('');
                setRiskFilter('All');
                setCategoryFilter('All');
                setFeederFilter('All');
              }}
              className="text-xs text-blue-600 hover:text-blue-800 underline ml-auto transition-colors duration-150 cursor-pointer"
            >
              Reset filters
            </button>
          )}

          <div className="text-xs font-mono text-gray-500 ml-auto hidden md:block">
            {filteredConsumers.length} records
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="bg-white border border-gray-200 rounded-md overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-gray-500">Loading data...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-600 border-collapse">
              <thead className="bg-gray-50 text-gray-700 font-medium text-xs border-b border-gray-200">
                <tr>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Priority Rank</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Consumer ID</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Category</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Risk Level</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Cause</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Estimated Loss</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Status</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold text-right">Audit Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredConsumers.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="py-8 text-center text-xs text-gray-500">
                      No consumers found matching selected filters.
                    </td>
                  </tr>
                ) : (
                  filteredConsumers.map((item) => (
                    <tr
                      key={item.consumer_id}
                      onClick={() => navigate(`/consumers/${item.consumer_id}`)}
                      className="cursor-pointer hover:bg-gray-50 transition-colors duration-150"
                    >
                      <td className="py-2.5 px-4 font-mono text-xs text-gray-600">
                        {item.priority_rank != null ? `#${item.priority_rank}` : '-'}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-xs font-semibold text-blue-600 hover:underline">
                        {item.consumer_id || '-'}
                      </td>
                      <td className="py-2.5 px-4 text-xs text-gray-700">
                        {item.category || '-'}
                      </td>
                      <td className="py-2.5 px-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${getRiskBadge(
                            item.risk_level
                          )}`}
                        >
                          {item.risk_level || '-'}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-xs text-gray-800">
                        {item.cause || '-'}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-xs text-gray-600 font-medium">
                        {item.estimated_loss != null
                          ? `₹${item.estimated_loss.toLocaleString('en-IN')}`
                          : '-'}
                      </td>
                      <td className="py-2.5 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-gray-100 text-gray-700 border border-gray-200">
                          {item.status || '-'}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => setDispatchConsumer(item)}
                          className="bg-amber-500 hover:bg-amber-600 text-white px-2.5 py-1 rounded text-xs font-semibold shadow-2xs transition-colors"
                        >
                          ⚡ Dispatch
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Field Inspection Audit Dispatch Modal */}
      {dispatchConsumer && (
        <FieldInspectionModal
          consumer={dispatchConsumer}
          onClose={() => setDispatchConsumer(null)}
          onActionLogged={(details) => {
            setToastMessage(`⚡ Field inspection ticket logged for ${details.consumerId}`);
            setTimeout(() => setToastMessage(''), 3500);
          }}
        />
      )}

      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white px-4 py-2.5 rounded-lg shadow-lg text-xs font-semibold border border-slate-700 animate-bounce">
          {toastMessage}
        </div>
      )}
    </div>
  );
}
