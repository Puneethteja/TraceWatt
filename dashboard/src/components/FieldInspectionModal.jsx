import React, { useState } from 'react';

export default function FieldInspectionModal({ consumer, onClose, onActionLogged }) {
  const [actionType, setActionType] = useState('Field Dispatch Inspection');
  const [priority, setPriority] = useState('P1 - Immediate (Emergency Theft)');
  const [team, setTeam] = useState('Squad Alpha - Grid Audit Div');
  const [scheduledDate, setScheduledDate] = useState(
    new Date(Date.now() + 86400000).toISOString().split('T')[0]
  );
  const [notes, setNotes] = useState('');
  const [checklist, setChecklist] = useState({
    sealVerification: true,
    ctPtBypassCheck: true,
    firmwareAudit: false,
    neutralBypassCheck: true,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successToast, setSuccessToast] = useState(false);

  if (!consumer) return null;

  const toggleChecklist = (key) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    setTimeout(() => {
      setIsSubmitting(false);
      setSuccessToast(true);
      if (onActionLogged) {
        onActionLogged({
          consumerId: consumer.consumer_id,
          actionType,
          priority,
          team,
          scheduledDate,
          notes,
          checklist,
          timestamp: new Date().toLocaleString(),
        });
      }
      setTimeout(() => {
        setSuccessToast(false);
        onClose();
      }, 1500);
    }, 600);
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
              <h3 className="font-bold text-base tracking-wide">
                Schedule Field Audit Dispatch
              </h3>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Consumer ID: <span className="font-mono text-amber-300 font-semibold">{consumer.consumer_id}</span> ({consumer.name || 'Industrial Consumer'})
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg transition-colors text-lg"
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs font-sans">
          {/* Action Type & Priority */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">
                Audit Action Type
              </label>
              <select
                value={actionType}
                onChange={(e) => setActionType(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-3 py-2 text-xs font-medium text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="Field Dispatch Inspection">⚡ Physical Field Dispatch</option>
                <option value="Smart Meter Diagnostic">🔍 Meter Calibration Check</option>
                <option value="Tamper Seal Check">🛡️ Anti-Tamper Seal Audit</option>
                <option value="Remote Disconnect">⛔ Remote Disconnect Request</option>
                <option value="Legal Violation Notice">📜 Issue Tampering Notice</option>
                <option value="Mark False Alarm">✅ Verify & Dismiss (False Alarm)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">
                Priority Tier
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-3 py-2 text-xs font-medium text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="P1 - Immediate (Emergency Theft)">🚨 P1 - Immediate (High Loss)</option>
                <option value="P2 - 24 Hours">⚠️ P2 - High (Within 24h)</option>
                <option value="P3 - Routine Audit">📅 P3 - Standard Schedule</option>
              </select>
            </div>
          </div>

          {/* Assigned Squad & Date */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">
                Assigned Inspection Team
              </label>
              <select
                value={team}
                onChange={(e) => setTeam(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-3 py-2 text-xs font-medium text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="Squad Alpha - Grid Audit Div">Squad Alpha (NTL Forensic)</option>
                <option value="Squad Beta - Rapid Response">Squad Beta (Field Operations)</option>
                <option value="Squad Gamma - Meter Calibration">Squad Gamma (Meter Diagnostics)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">
                Inspection Date
              </label>
              <input
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-3 py-1.5 text-xs font-medium text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Field Checklist protocol */}
          <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
            <span className="block font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Mandatory Inspection Protocol Checklist
            </span>
            <div className="grid grid-cols-2 gap-2 text-slate-600 dark:text-slate-400">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={checklist.sealVerification}
                  onChange={() => toggleChecklist('sealVerification')}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>Physical Seal Audit</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={checklist.ctPtBypassCheck}
                  onChange={() => toggleChecklist('ctPtBypassCheck')}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>CT/PT Shunt Bypass Test</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={checklist.firmwareAudit}
                  onChange={() => toggleChecklist('firmwareAudit')}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>Optical Firmware Log Audit</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={checklist.neutralBypassCheck}
                  onChange={() => toggleChecklist('neutralBypassCheck')}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>Neutral Line Current Check</span>
              </label>
            </div>
          </div>

          {/* Operator Instructions & Evidence Notes */}
          <div>
            <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">
              Field Team Special Instructions / Notes
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Inspect secondary CT meter box behind transformer vault 3..."
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md p-2.5 text-xs text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          {/* Toast Alert on Submit Success */}
          {successToast && (
            <div className="bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-700 text-emerald-800 dark:text-emerald-200 px-3 py-2 rounded-md text-xs font-semibold flex items-center justify-between">
              <span>✅ Dispatch Ticket Logged & Dispatched to {team}!</span>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-xs transition-colors flex items-center space-x-1.5 disabled:opacity-50"
            >
              {isSubmitting ? (
                <span>Dispatching...</span>
              ) : (
                <span>Confirm Dispatch Ticket</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
