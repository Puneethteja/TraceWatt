import React, { useState } from 'react';

const SCENARIOS = [
  {
    id: 'theft',
    title: 'Inject Theft',
    type: 'Theft Simulation',
    description: 'Simulate an immediate 40-70% meter bypass or tamper on selected consumer meters to evaluate detection latency.',
    payload: { action: 'inject_bypass', factor: 0.45 },
  },
  {
    id: 'fault',
    title: 'Inject Meter Fault',
    type: 'Hardware Failure',
    description: 'Trigger sporadic zero-readings, negative spikes, and frozen registers characteristic of CT/PT equipment failure.',
    payload: { action: 'sensor_fault', error_rate: 0.35 },
  },
  {
    id: 'comms',
    title: 'Inject Comms Failure',
    type: 'Network Telemetry Loss',
    description: 'Simulate RF mesh / GPRS packet dropouts resulting in missing telemetry windows and gap imputation triggers.',
    payload: { action: 'packet_drop', loss_pct: 0.8 },
  },
  {
    id: 'seasonal',
    title: 'Inject Seasonal Shift',
    type: 'Weather & Tariff Elasticity',
    description: 'Apply acute ambient temperature rise (+8°C) to test peer-normalized consumption baseline adaptation.',
    payload: { action: 'temp_shift', delta_c: 8 },
  },
];

export default function ScenarioLab() {
  const [runningId, setRunningId] = useState(null);
  const [statusMsg, setStatusMsg] = useState(null);

  const handleRunScenario = (scenario) => {
    setRunningId(scenario.id);
    setStatusMsg(`Dispatching synthetic scenario: ${scenario.title}...`);

    setTimeout(() => {
      setRunningId(null);
      setStatusMsg(`Scenario "${scenario.title}" successfully injected into simulation pipeline.`);
      setTimeout(() => setStatusMsg(null), 4000);
    }, 600);
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-gray-900 dark:text-slate-100">
          Scenario Lab
        </h1>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
          Inject synthetic events into the live IoT simulator (PRD USP #5 - Simulation Playground)
        </p>
      </div>

      {/* Notification banner */}
      {statusMsg && (
        <div className="p-3 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-blue-800 dark:text-blue-300 rounded-md text-xs font-mono">
          [SIM-OUT] {statusMsg}
        </div>
      )}

      {/* 2-column grid of flat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SCENARIOS.map((scenario) => {
          const isRunning = runningId === scenario.id;
          return (
            <div
              key={scenario.id}
              className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-md p-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-base font-semibold tracking-tight text-gray-900 dark:text-slate-100">
                    {scenario.title}
                  </h2>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-400 border border-gray-200 dark:border-slate-700">
                    {scenario.type}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-slate-400 mb-4 leading-relaxed">
                  {scenario.description}
                </p>
              </div>

              <div className="pt-2 border-t border-gray-100 dark:border-slate-800 flex items-center justify-between">
                <span className="text-xs font-mono text-gray-400 dark:text-slate-500">
                  Target: Feeder Grid Simulator
                </span>
                <button
                  type="button"
                  onClick={() => handleRunScenario(scenario)}
                  disabled={isRunning}
                  className="bg-blue-600 hover:bg-blue-700 text-white rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150 disabled:opacity-50 cursor-pointer"
                >
                  {isRunning ? 'Injecting...' : 'Run Scenario'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
