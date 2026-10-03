import React from 'react';

/**
 * DetectionTimeline component displaying anomaly onset vs. system detection latency.
 */
export default function DetectionTimeline({ periodStart, firstFlaggedAt }) {
  const startDate = periodStart ? new Date(periodStart) : new Date('2026-09-01T00:00:00Z');
  const flaggedDate = firstFlaggedAt ? new Date(firstFlaggedAt) : new Date('2026-09-15T08:30:00Z');

  // Compute latency in days
  const diffMs = Math.max(0, flaggedDate.getTime() - startDate.getTime());
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

  const formatDate = (date) => {
    return date.toISOString().split('T')[0];
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg p-4 font-sans">
      <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-slate-800">
        <h4 className="text-xs font-semibold text-gray-900 dark:text-slate-100 uppercase tracking-wider tracking-tight">
          Detection Timeline
        </h4>
        <div className="text-xs text-gray-500 dark:text-slate-400">
          Latency: <span className="font-mono font-semibold text-gray-900 dark:text-slate-100">{diffDays} days</span>
        </div>
      </div>

      {/* Flat Minimal Horizontal Timeline */}
      <div className="mt-6 mb-3 px-3">
        <div className="relative">
          {/* Timeline Border Line */}
          <div className="absolute top-1 left-2 right-2 border-t-2 border-gray-200 dark:border-slate-700" />

          {/* Points */}
          <div className="relative flex justify-between">
            {/* Start Event */}
            <div className="flex flex-col items-start">
              <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-slate-600 -mt-0.5" />
              <div className="mt-2 text-left">
                <span className="text-[11px] font-semibold text-gray-800 dark:text-slate-200 block">
                  Anomaly Started
                </span>
                <span className="font-mono text-xs text-gray-500 dark:text-slate-400 block">
                  {formatDate(startDate)}
                </span>
              </div>
            </div>

            {/* Flagged Event */}
            <div className="flex flex-col items-end">
              <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-slate-600 -mt-0.5" />
              <div className="mt-2 text-right">
                <span className="text-[11px] font-semibold text-gray-800 dark:text-slate-200 block">
                  System Flagged
                </span>
                <span className="font-mono text-xs text-gray-500 dark:text-slate-400 block">
                  {formatDate(flaggedDate)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
