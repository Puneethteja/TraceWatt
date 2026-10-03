import React from 'react';

/**
 * ExplainabilityPanel component showing model reasoning, supporting/counter evidence,
 * and review alerts when model inference is inconclusive.
 */
export default function ExplainabilityPanel({
  cause,
  confidence,
  recommendedAction,
  evidence = [],
  counterEvidence = [],
}) {
  const isRequiresReview = cause?.toLowerCase() === 'requires review';
  const confidencePercent = Math.round(
    confidence > 1 ? confidence : (confidence || 0) * 100
  );

  return (
    <div className="bg-white border border-gray-200 rounded-md p-4 flex flex-col space-y-4 font-sans h-full">
      {/* Header with Cause & Confidence */}
      <div className="flex items-start justify-between pb-3 border-b border-gray-100">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-gray-500 font-medium">
            Root Cause Diagnosis
          </div>
          <div className="text-base font-semibold text-gray-900 mt-0.5 tracking-tight">
            {cause || 'Unclassified Anomaly'}
          </div>
        </div>
        <div className="text-right">
          <div className="text-[11px] uppercase tracking-wider text-gray-500 font-medium">
            Confidence
          </div>
          <div className="font-mono text-base font-bold text-gray-900 mt-0.5">
            {confidencePercent}%
          </div>
        </div>
      </div>

      {/* Requires Review Alert Box */}
      {isRequiresReview && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 text-xs p-3 rounded">
          <div className="font-semibold mb-1 flex items-center">
            <span className="mr-1.5 font-bold">⚠</span> Inconclusive Diagnosis — Additional Evidence Required
          </div>
          <p className="leading-relaxed">
            Automated model classification confidence is insufficient. Physical transformer reconciliation recommended.
          </p>
        </div>
      )}

      {/* Supporting Evidence - Forensic Legal Styling */}
      <div>
        <h4 className="text-xs font-semibold text-gray-900 uppercase tracking-wider mb-2 tracking-tight">
          Supporting Evidence
        </h4>
        {evidence && evidence.length > 0 ? (
          <div>
            {evidence.map((item, idx) => (
              <div
                key={idx}
                className="bg-green-50 border-l-2 border-green-500 p-3 mb-2 text-sm text-gray-800 flex items-start leading-relaxed"
              >
                <span className="text-green-600 font-bold mr-2 shrink-0">✓</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-400 italic">No supporting evidence flagged.</p>
        )}
      </div>

      {/* Counter Evidence - Forensic Legal Styling */}
      <div>
        <h4 className="text-xs font-semibold text-gray-900 uppercase tracking-wider mb-2 tracking-tight">
          Counter Evidence
        </h4>
        {counterEvidence && counterEvidence.length > 0 ? (
          <div>
            {counterEvidence.map((item, idx) => (
              <div
                key={idx}
                className="bg-red-50 border-l-2 border-red-500 p-3 mb-2 text-sm text-gray-800 flex items-start leading-relaxed"
              >
                <span className="text-red-600 font-bold mr-2 shrink-0">✗</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-400 italic">No mitigating counter-evidence recorded.</p>
        )}
      </div>

      {/* Recommended Action */}
      {recommendedAction && (
        <div className="pt-2 border-t border-gray-100 mt-auto">
          <div className="text-[11px] font-semibold text-gray-700 uppercase tracking-wider">
            Recommended Action
          </div>
          <div className="text-xs text-gray-600 mt-1 leading-relaxed">
            {recommendedAction}
          </div>
        </div>
      )}
    </div>
  );
}
