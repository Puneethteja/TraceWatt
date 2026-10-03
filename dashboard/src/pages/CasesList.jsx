import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { getCases, updateCaseStatus } from '../api/client';
import CaseDetailDrawer from '../components/CaseDetailDrawer';
import ExportMenu from '../components/ExportMenu';

const STATUS_OPTIONS = [
  'New',
  'Under Review',
  'Inspection Scheduled',
  'Confirmed',
  'False Alarm',
  'Closed',
];

export default function CasesList() {
  const [cases, setCases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [riskFilter, setRiskFilter] = useState('All');
  const [selectedConsumerId, setSelectedConsumerId] = useState(null);
  const [updatingId, setUpdatingId] = useState(null);
  const [updateFeedback, setUpdateFeedback] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setErrorMessage('');

    getCases()
      .then((data) => {
        if (!isMounted) return;
        setCases(Array.isArray(data) ? data : []);
        setIsLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load cases:', err);
        setErrorMessage('Unable to load investigation cases from server. Operating in offline mode.');
        setCases([]);
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleStatusChange = async (consumerId, newStatus) => {
    setUpdatingId(consumerId);
    try {
      await updateCaseStatus(consumerId, { status: newStatus });
      setCases((prev) =>
        prev.map((c) =>
          c.consumer_id === consumerId ? { ...c, status: newStatus } : c
        )
      );
      setUpdateFeedback({ id: consumerId, message: `Status updated to ${newStatus}` });
      setTimeout(() => setUpdateFeedback(null), 3000);
    } catch (err) {
      console.error('Failed to update case status:', err);
    } finally {
      setUpdatingId(null);
    }
  };

  const filteredCases = useMemo(() => {
    return cases.filter((item) => {
      const matchSearch =
        !searchQuery ||
        item.consumer_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.cause?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchStatus = statusFilter === 'All' || item.status === statusFilter;
      const matchRisk = riskFilter === 'All' || item.risk_level?.toLowerCase() === riskFilter.toLowerCase();
      return matchSearch && matchStatus && matchRisk;
    });
  }, [cases, searchQuery, statusFilter, riskFilter]);

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

      {/* Top Bar with Title, Search, and Filters */}
      <div className="bg-white border border-gray-200 rounded-md p-4 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-base font-semibold text-gray-900 tracking-tight">
              Investigation Cases & Triage Workflow
            </h1>
            <p className="text-xs text-gray-500">
              Manage field audit status, schedule physical inspections, and log forensic tamper findings.
            </p>
          </div>
          <ExportMenu
            filters={{ status: statusFilter, risk: riskFilter }}
            filenamePrefix="cases_export"
          />
        </div>

        {/* Filter controls */}
        <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-gray-100 text-sm">
          <div className="flex-1 min-w-[220px]">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search consumer ID or theft cause..."
              className="bg-white border border-gray-200 rounded-md px-3 py-1.5 text-sm w-full focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 placeholder-gray-400"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-1.5">
            <label htmlFor="filter-status" className="text-xs font-medium text-gray-600">
              Status:
            </label>
            <select
              id="filter-status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white border border-gray-200 rounded-md px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="All">All Statuses</option>
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          {/* Risk Filter */}
          <div className="flex items-center space-x-1.5">
            <label htmlFor="filter-risk-case" className="text-xs font-medium text-gray-600">
              Risk:
            </label>
            <select
              id="filter-risk-case"
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

          {(searchQuery || statusFilter !== 'All' || riskFilter !== 'All') && (
            <button
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('All');
                setRiskFilter('All');
              }}
              className="text-xs text-blue-600 hover:text-blue-800 underline ml-auto transition-colors duration-150 cursor-pointer"
            >
              Reset filters
            </button>
          )}

          <div className="text-xs font-mono text-gray-500 ml-auto hidden md:block">
            {filteredCases.length} cases
          </div>
        </div>
      </div>

      {/* Cases Data Table */}
      <div className="bg-white border border-gray-200 rounded-md overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-gray-500">Loading cases...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-600 border-collapse">
              <thead className="bg-gray-50 text-gray-700 font-medium text-xs border-b border-gray-200">
                <tr>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Priority Rank</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Consumer ID</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Risk Level</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Cause</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Status Update</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Last Updated</th>
                  <th className="py-2.5 px-4 uppercase tracking-wider text-[11px] font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredCases.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="py-8 text-center text-xs text-gray-500">
                      No investigation cases found matching selected criteria.
                    </td>
                  </tr>
                ) : (
                  filteredCases.map((item) => (
                    <tr key={item.consumer_id} className="hover:bg-gray-50 transition-colors duration-150">
                      <td className="py-2.5 px-4 font-mono text-xs text-gray-600">
                        {item.priority_rank != null ? `#${item.priority_rank}` : '-'}
                      </td>
                      <td className="py-2.5 px-4">
                        <Link
                          to={`/consumers/${item.consumer_id}`}
                          className="font-mono text-xs font-semibold text-blue-600 hover:underline"
                        >
                          {item.consumer_id}
                        </Link>
                      </td>
                      <td className="py-2.5 px-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${getRiskBadge(
                            item.risk_level
                          )}`}
                        >
                          {item.risk_level || 'Medium'}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-xs text-gray-800">
                        {item.cause || 'Unmetered Tap'}
                      </td>
                      <td className="py-2.5 px-4">
                        <div className="flex items-center space-x-2">
                          <select
                            value={item.status || 'New'}
                            disabled={updatingId === item.consumer_id}
                            onChange={(e) => handleStatusChange(item.consumer_id, e.target.value)}
                            className="bg-white border border-gray-200 rounded px-2 py-1 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
                          >
                            {STATUS_OPTIONS.map((opt) => (
                              <option key={opt} value={opt}>
                                {opt}
                              </option>
                            ))}
                          </select>
                          {updateFeedback?.id === item.consumer_id && (
                            <span className="text-[10px] text-green-600 font-medium">✓ Saved</span>
                          )}
                        </div>
                      </td>
                      <td className="py-2.5 px-4 font-mono text-xs text-gray-400">
                        {item.last_updated || 'Recent'}
                      </td>
                      <td className="py-2.5 px-4">
                        <button
                          type="button"
                          onClick={() => setSelectedConsumerId(item.consumer_id)}
                          className="bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 rounded px-2 py-1 text-xs font-medium transition-colors duration-150 cursor-pointer"
                        >
                          Inspect Drawer
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

      {/* Case Detail Drawer Slide-over */}
      {selectedConsumerId && (
        <CaseDetailDrawer
          consumerId={selectedConsumerId}
          onClose={() => setSelectedConsumerId(null)}
        />
      )}
    </div>
  );
}
