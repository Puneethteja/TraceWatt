import React from 'react';

export default function ExecutiveLossMatrix({ summary }) {
  // Compute key estimates based on summary or default hackathon metrics
  const totalConsumers = summary?.total_consumers || 300;
  const highRiskCount = summary?.high_risk_count || 42;
  const estimatedStolenKwh = (highRiskCount * 485.4).toFixed(0);
  const financialLossDollar = (highRiskCount * 145.6).toLocaleString('en-US');
  const financialLossRupees = (highRiskCount * 12200).toLocaleString('en-IN');
  const dispatchRoi = '8.4x';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-sans">
      {/* Metric 1 */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-xs flex items-center justify-between">
        <div>
          <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Est. Monthly Stolen Energy
          </div>
          <div className="font-mono text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            {Number(estimatedStolenKwh).toLocaleString()} <span className="text-xs font-normal text-slate-500">kWh</span>
          </div>
          <div className="text-[11px] text-red-600 dark:text-red-400 font-medium mt-0.5 flex items-center">
            <span>▲ +14.2% vs previous period</span>
          </div>
        </div>
        <div className="w-10 h-10 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 text-red-600 dark:text-red-400 flex items-center justify-center text-lg font-bold">
          ⚡
        </div>
      </div>

      {/* Metric 2 */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-xs flex items-center justify-between">
        <div>
          <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Revenue Loss Estimate
          </div>
          <div className="font-mono text-xl font-bold text-red-600 dark:text-red-400 mt-1">
            ₹{financialLossRupees}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 font-medium mt-0.5">
            (~${financialLossDollar} USD)
          </div>
        </div>
        <div className="w-10 h-10 rounded-lg bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-900 text-amber-600 dark:text-amber-400 flex items-center justify-center text-lg font-bold">
          💰
        </div>
      </div>

      {/* Metric 3 */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-xs flex items-center justify-between">
        <div>
          <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            High-Risk Theft Backlog
          </div>
          <div className="font-mono text-xl font-bold text-amber-600 dark:text-amber-400 mt-1">
            {highRiskCount} <span className="text-xs font-normal text-slate-500">/ {totalConsumers}</span>
          </div>
          <div className="text-[11px] text-amber-600 dark:text-amber-400 font-medium mt-0.5">
            Requires Field Inspection
          </div>
        </div>
        <div className="w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-900 text-blue-600 dark:text-blue-400 flex items-center justify-center text-lg font-bold">
          🎯
        </div>
      </div>

      {/* Metric 4 */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-xs flex items-center justify-between">
        <div>
          <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Audit Recovery ROI Index
          </div>
          <div className="font-mono text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
            {dispatchRoi}
          </div>
          <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium mt-0.5">
            High Financial Recovery Rate
          </div>
        </div>
        <div className="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-900 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-lg font-bold">
          📈
        </div>
      </div>
    </div>
  );
}
