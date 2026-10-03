import React, { useState } from 'react';

const FEEDER_NODES = [
  { id: 'FDR-01', name: 'Industrial Zone West', transformers: 12, lossPct: 14.8, status: 'critical', theftCases: 8, loadKw: 420 },
  { id: 'FDR-02', name: 'Suburban Residential East', transformers: 24, lossPct: 8.2, status: 'warning', theftCases: 3, loadKw: 310 },
  { id: 'FDR-03', name: 'Commercial Hub Central', transformers: 18, lossPct: 18.4, status: 'critical', theftCases: 12, loadKw: 580 },
  { id: 'FDR-04', name: 'North Rural Agricultural', transformers: 30, lossPct: 3.1, status: 'optimal', theftCases: 1, loadKw: 190 },
  { id: 'FDR-05', name: 'Metro Tech Park', transformers: 15, lossPct: 4.5, status: 'optimal', theftCases: 0, loadKw: 640 },
  { id: 'FDR-06', name: 'South Coastal Industrial', transformers: 9, lossPct: 11.6, status: 'warning', theftCases: 5, loadKw: 390 },
];

export default function SubstationGridHeatmap() {
  const [selectedFeeder, setSelectedFeeder] = useState(FEEDER_NODES[0]);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'critical':
        return <span className="bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300 border border-red-200 dark:border-red-800 px-2 py-0.5 rounded text-[10px] font-bold uppercase">Critical Loss (&gt;12%)</span>;
      case 'warning':
        return <span className="bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800 px-2 py-0.5 rounded text-[10px] font-bold uppercase">Moderate Leakage (6-12%)</span>;
      default:
        return <span className="bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 px-2 py-0.5 rounded text-[10px] font-bold uppercase">Optimal (&lt;6%)</span>;
    }
  };

  const getNodeColor = (status, isSelected) => {
    let base = '';
    if (status === 'critical') base = 'bg-red-500/10 border-red-500 hover:bg-red-500/20 text-red-700 dark:text-red-400';
    else if (status === 'warning') base = 'bg-amber-500/10 border-amber-500 hover:bg-amber-500/20 text-amber-700 dark:text-amber-400';
    else base = 'bg-emerald-500/10 border-emerald-500 hover:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400';

    return `${base} ${isSelected ? 'ring-2 ring-blue-600 scale-[1.02] shadow-md' : ''}`;
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-xs font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-lg">🗺️</span>
            <h2 className="font-bold text-slate-900 dark:text-slate-100 text-sm tracking-tight">
              Grid Substation & Feeder NTL Loss Heatmap
            </h2>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Real-time loss delta reconciliation across 6 primary distribution feeder lines.
          </p>
        </div>
        <div className="mt-2 sm:mt-0 flex items-center space-x-3 text-[11px] font-medium text-slate-600 dark:text-slate-400">
          <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-red-500 mr-1" /> &gt;12% Theft Risk</span>
          <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 mr-1" /> 6-12% Leakage</span>
          <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 mr-1" /> Normal</span>
        </div>
      </div>

      {/* Grid Matrix Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Feeder Cards Grid (2 cols) */}
        <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-3 gap-3">
          {FEEDER_NODES.map((node) => {
            const isSelected = selectedFeeder.id === node.id;
            return (
              <button
                key={node.id}
                onClick={() => setSelectedFeeder(node)}
                className={`text-left p-3.5 rounded-lg border transition-all duration-150 cursor-pointer flex flex-col justify-between ${getNodeColor(node.status, isSelected)}`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold">{node.id}</span>
                    <span className="font-mono text-xs font-black">{node.lossPct}%</span>
                  </div>
                  <div className="text-xs font-medium text-slate-800 dark:text-slate-200 truncate mt-1">
                    {node.name}
                  </div>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-200/50 dark:border-slate-800 flex items-center justify-between text-[11px]">
                  <span>{node.transformers} Transformers</span>
                  <span className="font-semibold text-red-600 dark:text-red-400">{node.theftCases} Flagged</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Feeder Deep Dive Panel (1 col) */}
        <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-lg p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono font-bold text-xs text-blue-600 dark:text-blue-400">{selectedFeeder.id}</span>
              {getStatusBadge(selectedFeeder.status)}
            </div>

            <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">
              {selectedFeeder.name}
            </h3>

            <div className="mt-4 space-y-2.5 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-slate-200 dark:border-slate-700">
                <span className="text-slate-500 dark:text-slate-400">Distribution Loss Rate</span>
                <span className="font-mono font-bold text-slate-900 dark:text-slate-100">{selectedFeeder.lossPct}%</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-200 dark:border-slate-700">
                <span className="text-slate-500 dark:text-slate-400">Total Connected Load</span>
                <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">{selectedFeeder.loadKw} kW</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-200 dark:border-slate-700">
                <span className="text-slate-500 dark:text-slate-400">Transformers Monitored</span>
                <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">{selectedFeeder.transformers} Units</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-500 dark:text-slate-400">Active High-Theft Cases</span>
                <span className="font-mono font-bold text-red-600 dark:text-red-400">{selectedFeeder.theftCases} Consumers</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-700">
            <a
              href={`/feeders/${selectedFeeder.id}`}
              className="w-full inline-flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white font-medium py-1.5 px-3 rounded text-xs transition-colors"
            >
              Analyze {selectedFeeder.id} Feeder Balance →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
