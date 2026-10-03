import React, { useState, useEffect } from 'react';
import { getConsumerDetail, getCaseDetail, updateCaseStatus } from '../api/client';

const STATUS_OPTIONS = [
  'New',
  'Under Review',
  'Inspection Scheduled',
  'Confirmed',
  'False Alarm',
  'Closed',
];

export default function CaseDetailDrawer({ consumerId, onClose }) {
  const [consumer, setConsumer] = useState(null);
  const [caseData, setCaseData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [currentStatus, setCurrentStatus] = useState('New');
  const [note, setNote] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [history, setHistory] = useState([]);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setErrorMessage('');

    Promise.all([
      getConsumerDetail(consumerId),
      getCaseDetail(consumerId),
    ])
      .then(([consumerRes, caseRes]) => {
        if (!isMounted) return;
        const cons = consumerRes || {};
        const cData = caseRes || {};
        setConsumer(cons);
        setCaseData(cData);
        setCurrentStatus(cData.status || cons.status || 'New');
        setNote(cData.note || '');
        setHistory([
          {
            id: 1,
            text: `Case record initialized`,
            time: cData.first_flagged_at || 'Recently',
          },
        ]);
        setIsLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Error fetching case details:', err);
        setErrorMessage('Unable to load case details from backend server.');
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [consumerId]);

  const handleUpdate = async () => {
    setIsUpdating(true);
    setSaveMessage('');
    try {
      const res = await updateCaseStatus(consumerId, { status: currentStatus, note });
      if (res && res.error) {
        setSaveMessage('Failed to update status');
      } else {
        setHistory((prev) => [
          {
            id: Date.now(),
            text: `Status changed to ${currentStatus}${note ? ` (Note: "${note}")` : ''}`,
            time: 'Just now',
          },
          ...prev,
        ]);
        setSaveMessage('Status updated successfully');
      }
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (err) {
      console.error('Failed to update status:', err);
      setSaveMessage('Failed to update status');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <>
      {/* Subtle backdrop overlay */}
      <div
        className="fixed inset-0 bg-gray-900/20 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-over panel with subtle slide-in animation */}
      <div className="fixed top-0 right-0 h-full w-[480px] max-w-full bg-white border-l border-gray-200 shadow-sm z-50 flex flex-col font-sans transition-transform duration-200 ease-out">
        {/* Header */}
        <div className="h-14 px-5 border-b border-gray-200 flex items-center justify-between shrink-0 bg-white">
          <div className="flex items-center space-x-2.5">
            <span className="font-mono text-sm font-semibold text-gray-900">
              {consumerId || '-'}
            </span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-gray-100 text-gray-700 border border-gray-200">
              {currentStatus || '-'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 rounded p-1 transition-colors duration-150"
            title="Close panel"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable Content */}
        {isLoading ? (
          <div className="p-8 text-center text-xs text-gray-500">Loading data...</div>
        ) : (
          <div className="flex-1 overflow-y-auto divide-y divide-gray-200">
            {errorMessage && (
              <div className="p-3">
                <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-2 rounded">
                  {errorMessage}
                </div>
              </div>
            )}

            {/* Section 1: Key Metrics with Dash Null Handling */}
            <div className="p-5">
              <h3 className="text-xs font-semibold text-gray-900 uppercase tracking-wider mb-3">
                Key Metrics
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                  <div className="text-[11px] text-gray-500 font-medium">Anomaly Score</div>
                  <div className="font-mono text-sm font-semibold text-gray-900 mt-0.5">
                    {caseData?.anomaly_score != null
                      ? `${(caseData.anomaly_score * 100).toFixed(1)}%`
                      : consumer?.anomaly_score != null
                      ? `${(consumer.anomaly_score * 100).toFixed(1)}%`
                      : '-'}
                  </div>
                </div>
                <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                  <div className="text-[11px] text-gray-500 font-medium">Model Confidence</div>
                  <div className="font-mono text-sm font-semibold text-gray-900 mt-0.5">
                    {caseData?.confidence != null
                      ? `${(caseData.confidence * 100).toFixed(0)}%`
                      : consumer?.confidence != null
                      ? `${(consumer.confidence * 100).toFixed(0)}%`
                      : '-'}
                  </div>
                </div>
                <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                  <div className="text-[11px] text-gray-500 font-medium">Estimated Loss</div>
                  <div className="font-mono text-sm font-semibold text-gray-900 mt-0.5">
                    {caseData?.estimated_loss != null
                      ? `₹${caseData.estimated_loss.toLocaleString('en-IN')}`
                      : consumer?.estimated_loss != null
                      ? `₹${consumer.estimated_loss.toLocaleString('en-IN')}`
                      : '-'}
                  </div>
                </div>
                <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                  <div className="text-[11px] text-gray-500 font-medium">Priority Rank</div>
                  <div className="font-mono text-sm font-semibold text-gray-900 mt-0.5">
                    {caseData?.priority_rank != null
                      ? `#${caseData.priority_rank}`
                      : consumer?.priority_rank != null
                      ? `#${consumer.priority_rank}`
                      : '-'}
                  </div>
                </div>
              </div>

              {/* Quick Context Strip */}
              <div className="mt-3 flex items-center justify-between text-xs text-gray-500 px-1">
                <span>Category: <strong className="text-gray-700 font-medium">{consumer?.category || '-'}</strong></span>
                <span>Feeder: <strong className="text-gray-700 font-mono font-medium">{consumer?.feeder_id || '-'}</strong></span>
              </div>
            </div>

            {/* Section 2: Evidence */}
            <div className="p-5 space-y-4">
              <div>
                <h3 className="text-xs font-semibold text-gray-900 uppercase tracking-wider mb-2">
                  Supporting Evidence
                </h3>
                {caseData?.evidence && caseData.evidence.length > 0 ? (
                  <ul className="space-y-2">
                    {caseData.evidence.map((item, index) => (
                      <li key={index} className="flex items-start text-xs text-gray-700 leading-relaxed">
                        <span className="text-green-600 font-bold mr-2 shrink-0">✓</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-gray-400 italic">No supporting evidence recorded.</p>
                )}
              </div>

              <div>
                <h3 className="text-xs font-semibold text-gray-900 uppercase tracking-wider mb-2">
                  Counter Evidence
                </h3>
                {caseData?.counter_evidence && caseData.counter_evidence.length > 0 ? (
                  <ul className="space-y-2">
                    {caseData.counter_evidence.map((item, index) => (
                      <li key={index} className="flex items-start text-xs text-gray-700 leading-relaxed">
                        <span className="text-red-600 font-bold mr-2 shrink-0">✕</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-gray-400 italic">No counter evidence noted.</p>
                )}
              </div>

              {caseData?.recommended_action && (
                <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-md">
                  <div className="text-[11px] font-semibold text-gray-700 uppercase tracking-wider">
                    Recommended Action
                  </div>
                  <div className="text-xs text-gray-600 mt-1">
                    {caseData.recommended_action}
                  </div>
                </div>
              )}
            </div>

            {/* Section 3: Status Update */}
            <div className="p-5 space-y-3">
              <h3 className="text-xs font-semibold text-gray-900 uppercase tracking-wider">
                Status & Triage Update
              </h3>
              <div>
                <label htmlFor="case-status-select" className="block text-[11px] font-medium text-gray-600 mb-1">
                  Triage Status
                </label>
                <select
                  id="case-status-select"
                  value={currentStatus}
                  onChange={(e) => setCurrentStatus(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-2.5 py-1.5 text-xs text-gray-800 bg-white focus:outline-none focus:border-blue-600"
                >
                  {STATUS_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="case-notes-textarea" className="block text-[11px] font-medium text-gray-600 mb-1">
                  Investigation Notes
                </label>
                <textarea
                  id="case-notes-textarea"
                  rows={3}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Add inspector findings, meter seal state, or review details..."
                  className="w-full border border-gray-300 rounded-md p-2 text-xs text-gray-800 focus:outline-none focus:border-blue-600 resize-none"
                />
              </div>

              <div className="flex items-center justify-between pt-1">
                <button
                  type="button"
                  onClick={handleUpdate}
                  disabled={isUpdating}
                  className="bg-blue-600 text-white hover:bg-blue-700 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150 disabled:opacity-50"
                >
                  {isUpdating ? 'Updating...' : 'Update Status'}
                </button>
                {saveMessage && (
                  <span className="text-xs font-medium text-green-600">
                    {saveMessage}
                  </span>
                )}
              </div>
            </div>

            {/* Section 4: Case History */}
            <div className="p-5">
              <h3 className="text-xs font-semibold text-gray-900 uppercase tracking-wider mb-3">
                Case Audit Trail
              </h3>
              <div className="space-y-3">
                {history.map((item) => (
                  <div key={item.id} className="text-xs border-l-2 border-gray-300 pl-3 py-0.5">
                    <div className="text-gray-800 font-medium">{item.text}</div>
                    <div className="text-[11px] text-gray-400 mt-0.5 font-mono">{item.time}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
