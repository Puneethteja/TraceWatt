import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api, request } from '../api/client';

export default function LinemanDashboard() {
  const [cases, setCases] = useState([]);
  const [consumers, setConsumers] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [filter, setFilter] = useState('Active'); // Active, Resolved, All
  const [selectedCase, setSelectedCase] = useState(null);
  
  // Drawer state
  const [caseDetails, setCaseDetails] = useState(null);
  const [consumptionData, setConsumptionData] = useState([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isDrawerLoading, setIsDrawerLoading] = useState(false);
  
  // Resolve action state
  const [note, setNote] = useState('');
  const [isResolving, setIsResolving] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      // Fetch cases and consumers in parallel
      const [casesRes, consumersRes] = await Promise.all([
        request("/cases?limit=1000"),
        request("/consumers?limit=1000")
      ]);
      
      // Map consumers by ID for quick feeder/transformer lookup
      const consumerMap = {};
      (consumersRes || []).forEach(c => {
        consumerMap[c.consumer_id] = c;
      });
      
      setConsumers(consumerMap);
      setCases(casesRes || []);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Unable to load cases. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRowClick = async (c) => {
    setSelectedCase(c);
    setIsDrawerOpen(true);
    setIsDrawerLoading(true);
    setNote('');
    setShowConfirm(false);
    
    try {
      const [details, consumption] = await Promise.all([
        request(`/cases/${c.consumer_id}`),
        request(`/consumers/${c.consumer_id}/consumption`).catch(() => [])
      ]);
      setCaseDetails(details);
      setConsumptionData(consumption);
    } catch (err) {
      console.error(err);
    } finally {
      setIsDrawerLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!selectedCase) return;
    setIsResolving(true);
    try {
      await request(`/cases/${selectedCase.consumer_id}/status`, {
        method: "PATCH",
        data: { status: "Closed", note: note || "Resolved by lineman." }
      });
      // Close drawer and refresh
      setIsDrawerOpen(false);
      fetchData();
    } catch (err) {
      alert("Failed to resolve case. Please try again.");
    } finally {
      setIsResolving(false);
      setShowConfirm(false);
    }
  };

  // Filtering logic
  const activeStatuses = ["New", "Under Review", "Inspection Scheduled", "Open"];
  
  const filteredCases = cases.filter(c => {
    if (filter === 'Active') return activeStatuses.includes(c.status);
    if (filter === 'Resolved') return !activeStatuses.includes(c.status);
    return true; // All
  }).sort((a, b) => {
    const pA = a.priority || 0;
    const pB = b.priority || 0;
    return pB - pA;
  });

  // Metrics
  const needsAttention = cases.filter(c => c.status === "New").length;
  const underReview = cases.filter(c => c.status === "Under Review" || c.status === "Inspection Scheduled").length;
  const highPriority = cases.filter(c => activeStatuses.includes(c.status) && c.risk_level === "High").length;
  const resolvedCount = cases.filter(c => !activeStatuses.includes(c.status)).length;

  const getRiskColor = (level) => {
    if (level === 'High') return 'bg-red-100 text-red-800 border-red-200';
    if (level === 'Medium') return 'bg-amber-100 text-amber-800 border-amber-200';
    return 'bg-green-100 text-green-800 border-green-200';
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900 pb-12">
      {/* Navigation Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-bold font-mono">
              ⚡
            </div>
            <div>
              <h1 className="text-lg font-bold leading-tight">LINEMAN DASHBOARD</h1>
              <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">TraceWatt Field Operations</p>
            </div>
          </div>
          <Link to="/" className="text-sm text-blue-600 font-medium hover:underline">
            Back to TraceWatt →
          </Link>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Metrics Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
            <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Needs Attention</div>
            <div className="text-3xl font-bold font-mono text-blue-600">{isLoading ? '-' : needsAttention}</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
            <div className="text-xs font-semibold text-gray-500 uppercase mb-1">High Priority</div>
            <div className="text-3xl font-bold font-mono text-red-600">{isLoading ? '-' : highPriority}</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
            <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Under Review</div>
            <div className="text-3xl font-bold font-mono text-amber-600">{isLoading ? '-' : underReview}</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
            <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Resolved</div>
            <div className="text-3xl font-bold font-mono text-green-600">{isLoading ? '-' : resolvedCount}</div>
          </div>
        </div>

        {/* Work Queue Header & Filters */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-4">
          <h2 className="text-xl font-bold">Consumers Needing Attention</h2>
          <div className="flex bg-gray-100 p-1 rounded-md border border-gray-200">
            {['Active', 'Resolved', 'All'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-1.5 text-sm font-medium rounded ${filter === f ? 'bg-white shadow text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Error / Loading States */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-6">
            {error}
          </div>
        )}
        
        {isLoading && !error && (
          <div className="text-center py-12 text-gray-500">
            Loading active cases...
          </div>
        )}

        {/* Queue List (Mobile: Cards, Desktop: Table) */}
        {!isLoading && !error && (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            {filteredCases.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                {filter === 'Active' ? "No consumers currently require attention. Great job!" : "No cases found."}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[800px]">
                  <thead>
                    <tr className="bg-gray-50 text-xs uppercase tracking-wider text-gray-500 border-b border-gray-200">
                      <th className="p-4 font-semibold">Consumer</th>
                      <th className="p-4 font-semibold">Risk</th>
                      <th className="p-4 font-semibold">Cause</th>
                      <th className="p-4 font-semibold">Location</th>
                      <th className="p-4 font-semibold">Est. Impact</th>
                      <th className="p-4 font-semibold">Status</th>
                      <th className="p-4 font-semibold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredCases.map(c => {
                      const consumer = consumers[c.consumer_id] || {};
                      return (
                        <tr key={c.consumer_id} className="hover:bg-blue-50 transition-colors group cursor-pointer" onClick={() => handleRowClick(c)}>
                          <td className="p-4">
                            <div className="font-mono font-bold text-gray-900">{c.consumer_id}</div>
                            <div className="text-xs text-gray-500 capitalize">{consumer.category || 'Unknown'}</div>
                          </td>
                          <td className="p-4">
                            <span className={`px-2.5 py-1 rounded text-xs font-semibold border ${getRiskColor(c.risk_level)}`}>
                              {c.risk_level}
                            </span>
                          </td>
                          <td className="p-4">
                            <div className="font-medium text-gray-900">{c.cause}</div>
                          </td>
                          <td className="p-4 text-sm text-gray-600">
                            <div><span className="text-gray-400">FDR:</span> {consumer.feeder_id}</div>
                            <div><span className="text-gray-400">TX:</span> {consumer.transformer_id}</div>
                          </td>
                          <td className="p-4">
                            <div className="font-mono font-medium text-amber-700">₹{c.estimated_loss?.toLocaleString() || 0}</div>
                          </td>
                          <td className="p-4">
                            <div className="text-sm font-medium text-gray-700">{c.status}</div>
                          </td>
                          <td className="p-4 text-right">
                            <button className="text-sm font-semibold text-blue-600 group-hover:text-blue-800 bg-blue-50 px-3 py-1.5 rounded">
                              Investigate →
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Detail Drawer overlay */}
      {isDrawerOpen && (
        <div className="fixed inset-0 bg-gray-900/40 z-40 flex justify-end backdrop-blur-sm" onClick={() => setIsDrawerOpen(false)}>
          <div 
            className="w-full max-w-2xl bg-white h-full shadow-2xl overflow-y-auto transform transition-transform border-l border-gray-200"
            onClick={e => e.stopPropagation()}
          >
            {/* Drawer Header */}
            <div className="bg-gray-50 border-b border-gray-200 p-6 sticky top-0 z-10 flex justify-between items-start">
              <div>
                <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-1">Consumer Investigation</h2>
                <div className="text-3xl font-mono font-bold text-gray-900">{selectedCase?.consumer_id}</div>
                <div className="mt-2 flex gap-2">
                  <span className={`px-2.5 py-1 rounded text-xs font-semibold border ${getRiskColor(selectedCase?.risk_level)}`}>
                    {selectedCase?.risk_level} Risk
                  </span>
                  <span className="px-2.5 py-1 rounded text-xs font-semibold border bg-gray-100 text-gray-700 border-gray-200">
                    Status: {selectedCase?.status}
                  </span>
                </div>
              </div>
              <button 
                onClick={() => setIsDrawerOpen(false)}
                className="text-gray-400 hover:text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-full w-8 h-8 flex items-center justify-center font-bold"
              >
                ✕
              </button>
            </div>

            {isDrawerLoading ? (
              <div className="p-8 text-center text-gray-500">Loading case details...</div>
            ) : (
              <div className="p-6 space-y-8">
                
                {/* Network Location */}
                <section>
                  <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Location / Network Context</h3>
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-100 font-mono text-sm flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">Transformer:</span>
                      <strong className="text-gray-900">{consumers[selectedCase?.consumer_id]?.transformer_id}</strong>
                    </div>
                    <div className="text-gray-300 pl-2">↓</div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">Feeder:</span>
                      <strong className="text-gray-900">{consumers[selectedCase?.consumer_id]?.feeder_id}</strong>
                    </div>
                    <div className="text-gray-300 pl-2">↓</div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">Consumer:</span>
                      <strong className="text-blue-600">{selectedCase?.consumer_id}</strong>
                    </div>
                  </div>
                </section>

                {/* Evidence */}
                <section>
                  <h3 className="text-xs font-bold text-red-500 uppercase tracking-wider mb-3">Why This Case Was Flagged</h3>
                  <div className="bg-red-50 text-red-900 p-4 rounded-lg border border-red-100 text-sm">
                    {caseDetails?.evidence ? (
                      <ul className="list-disc pl-5 space-y-2">
                        {Array.isArray(caseDetails.evidence) ? 
                          caseDetails.evidence.map((ev, i) => <li key={i}>{ev}</li>) : 
                          <li>{caseDetails.evidence}</li>
                        }
                      </ul>
                    ) : "No specific evidence recorded."}
                  </div>
                </section>

                {/* Counter Evidence */}
                <section>
                  <h3 className="text-xs font-bold text-green-600 uppercase tracking-wider mb-3">Why Not Theft?</h3>
                  <div className="bg-green-50 text-green-900 p-4 rounded-lg border border-green-100 text-sm">
                    {caseDetails?.counter_evidence ? (
                      <ul className="list-disc pl-5 space-y-2">
                        {Array.isArray(caseDetails.counter_evidence) ? 
                          caseDetails.counter_evidence.map((ev, i) => <li key={i}>{ev}</li>) : 
                          <li>{caseDetails.counter_evidence}</li>
                        }
                      </ul>
                    ) : "No additional counter-evidence available."}
                  </div>
                </section>

                {/* Recommended Check */}
                <section>
                  <h3 className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-3">Recommended Check</h3>
                  <div className="bg-blue-50 text-blue-900 p-4 rounded-lg border border-blue-100 text-sm font-medium">
                    {caseDetails?.recommended_action || "Perform standard visual and hardware meter inspection."}
                  </div>
                </section>

                {/* Consumption Chart */}
                <section>
                  <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Recent Consumption</h3>
                  <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
                    {consumptionData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={consumptionData}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                          <XAxis dataKey="date" tick={{fontSize: 10}} axisLine={false} tickLine={false} />
                          <YAxis tick={{fontSize: 10}} axisLine={false} tickLine={false} />
                          <Tooltip 
                            contentStyle={{ borderRadius: '8px', fontSize: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                          />
                          <Line type="monotone" dataKey="kwh" stroke="#2563eb" strokeWidth={2} dot={false} name="Actual (kWh)" />
                          <Line type="monotone" dataKey="baseline_kwh" stroke="#9ca3af" strokeWidth={2} strokeDasharray="4 4" dot={false} name="Expected (kWh)" />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-gray-400 text-sm">
                        No consumption data available.
                      </div>
                    )}
                  </div>
                </section>

                <hr className="border-gray-200" />

                {/* Action Area */}
                {!activeStatuses.includes(selectedCase?.status) ? (
                   <div className="bg-gray-50 border border-gray-200 p-4 rounded-lg text-center text-sm text-gray-600">
                     This case has already been resolved. Status: <strong>{selectedCase?.status}</strong>
                   </div>
                ) : (
                  <section className="bg-white border border-gray-200 p-6 rounded-lg shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">Resolve Case</h3>
                    
                    <div className="mb-4">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Resolution Note</label>
                      <textarea
                        className="w-full border border-gray-300 rounded-md p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                        rows="3"
                        placeholder="Optional: Add what you found during inspection..."
                        value={note}
                        onChange={e => setNote(e.target.value)}
                        disabled={isResolving}
                      ></textarea>
                    </div>

                    {!showConfirm ? (
                      <button 
                        onClick={() => setShowConfirm(true)}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-md transition-colors"
                      >
                        Resolve Case
                      </button>
                    ) : (
                      <div className="bg-amber-50 border border-amber-200 p-4 rounded-md">
                        <p className="text-sm text-amber-800 font-semibold mb-3">
                          Resolve this case? Once resolved, this case will no longer appear in the active work queue.
                        </p>
                        <div className="flex gap-3">
                          <button 
                            onClick={handleResolve}
                            disabled={isResolving}
                            className="flex-1 bg-amber-600 hover:bg-amber-700 text-white font-bold py-2 px-4 rounded transition-colors disabled:opacity-50"
                          >
                            {isResolving ? 'Resolving...' : 'Yes, Resolve Case'}
                          </button>
                          <button 
                            onClick={() => setShowConfirm(false)}
                            disabled={isResolving}
                            className="flex-1 bg-white border border-gray-300 text-gray-700 font-bold py-2 px-4 rounded hover:bg-gray-50 transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </section>
                )}

              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
