import React from 'react';

const METRICS = [
  {
    name: 'Precision',
    value: '0.74',
    target: '0.70',
    status: 'Above target (+4.0%)',
    description: 'Fraction of detected theft anomalies that were confirmed non-technical losses upon field audit.',
  },
  {
    name: 'Recall',
    value: '0.82',
    target: '0.75',
    status: 'Above target (+7.0%)',
    description: 'Percentage of all actual physical and cyber grid theft events captured by the model ensemble.',
  },
  {
    name: 'F1 Score',
    value: '0.78',
    target: '0.72',
    status: 'Above target (+6.0%)',
    description: 'Harmonic mean balancing precision and recall for field inspection workforce efficiency.',
  },
  {
    name: 'ROC-AUC',
    value: '0.85',
    target: '0.80',
    status: 'Above target (+5.0%)',
    description: 'Overall discriminative capability across all anomaly confidence threshold variations.',
  },
];

const EVAL_SUMMARY = [
  { label: 'Evaluation Partition', value: '15,420 synthetic & real smart meters' },
  { label: 'Detection Engine', value: 'XGBoost Baseline Residual + GNN Topology v1.2' },
  { label: 'Test Timeframe', value: '30-day historical window' },
  { label: 'False Discovery Rate', value: '26.0%' },
  { label: 'Confidence Calibration', value: 'Platt Scaling (Brier Score: 0.082)' },
];

export default function ModelMetrics() {
  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-gray-900 dark:text-slate-100">
          Model Evaluation Metrics
        </h1>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
          Performance benchmarks and audit validation statistics (PRD Section D7)
        </p>
      </div>

      {/* Grid of flat metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {METRICS.map((metric) => (
          <div
            key={metric.name}
            className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-md p-4 flex flex-col justify-between cursor-pointer transition-all duration-200 ease-out hover:border-slate-600 hover:bg-slate-800/40 active:scale-[0.995]"
          >
            <div>
              <div className="text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                {metric.name}
              </div>
              <div className="font-mono text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">
                {metric.value}
              </div>
            </div>
            <div>
              <div className="text-xs text-green-600 dark:text-green-400 font-medium mb-1">
                ✓ {metric.status}
              </div>
              <div className="text-[11px] text-gray-400 dark:text-slate-500 leading-tight">
                Target: {metric.target}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Model Benchmark Details Panel */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-md p-6">
        <h2 className="text-sm font-semibold tracking-tight text-gray-900 dark:text-slate-100 mb-4">
          Benchmark Partition & Validation Metadata
        </h2>
        <div className="divide-y divide-gray-100 dark:divide-slate-800">
          {EVAL_SUMMARY.map((row) => (
            <div key={row.label} className="py-2.5 flex items-center justify-between text-xs">
              <span className="text-gray-500 dark:text-slate-400">{row.label}</span>
              <span className="font-mono font-medium text-gray-900 dark:text-slate-200">{row.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
