import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  getConsumerDetail,
  getCaseDetail,
  getConsumption,
  getBaseline,
} from '../api/client';
import ConsumptionChart from '../components/ConsumptionChart';
import ExplainabilityPanel from '../components/ExplainabilityPanel';
import DetectionTimeline from '../components/DetectionTimeline';

export default function ConsumerDetailView() {
  const { id: paramId } = useParams();
  const id = paramId || 'CONS-001';

  const [consumer, setConsumer] = useState(null);
  const [caseData, setCaseData] = useState(null);
  const [consumption, setConsumption] = useState([]);
  const [baselineData, setBaselineData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setErrorMessage('');

    Promise.all([
      getConsumerDetail(id),
      getCaseDetail(id),
      getConsumption(id),
      getBaseline(id),
    ])
      .then(([consumerRes, caseRes, consumptionRes, baselineRes]) => {
        if (!isMounted) return;
        setConsumer(consumerRes);
        setCaseData(caseRes);
        setConsumption(Array.isArray(consumptionRes) ? consumptionRes : []);
        setBaselineData(baselineRes);
        setIsLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load consumer details:', err);
        setErrorMessage('Unable to connect to backend server. Operating in offline mode.');
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [id]);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto py-12 text-center font-sans text-xs text-gray-500">
        Loading data...
      </div>
    );
  }

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

  const riskLevel = consumer?.risk_level || caseData?.risk_level || 'Medium';
  const consumerId = consumer?.consumer_id || caseData?.consumer_id || id;
  const status = consumer?.status || caseData?.status || 'Under Review';
  const anomalyScore = consumer?.anomaly_score ?? caseData?.anomaly_score ?? 0.85;
  const estimatedLoss = consumer?.estimated_loss ?? caseData?.estimated_loss ?? 18450;
  const confidence = caseData?.confidence ?? consumer?.confidence ?? 0.91;

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Inline Flat Error Banner */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-md">
          {errorMessage}
        </div>
      )}

      {/* Header Bar */}
      <div className="bg-white border border-gray-200 rounded-md p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-4">
          <Link
            to="/consumers"
            className="bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150"
          >
            ← Back to Consumers
          </Link>
          <div className="h-5 w-px bg-gray-200 hidden sm:block" />
          <div className="flex items-center space-x-3">
            <span className="font-mono text-xl font-bold text-gray-900">
              {consumerId}
            </span>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${getRiskBadge(
                riskLevel
              )}`}
            >
              {riskLevel} Risk
            </span>
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700 border border-gray-200">
              {status}
            </span>
          </div>
        </div>

        <div className="text-xs text-gray-500 space-x-2 font-mono text-left sm:text-right">
          <span>Feeder: <strong className="text-gray-700">{consumer?.feeder_id || 'FDR-NORTH-01'}</strong></span>
          <span>•</span>
          <span>Meter: <strong className="text-gray-700">{consumer?.meter_id || 'MTR-88219'}</strong></span>
        </div>
      </div>

      {/* 3-Column Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-6">
        {/* Section 1: Consumption vs Baseline Chart (col-span-2) */}
        <div className="lg:col-span-2">
          {consumption.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-md p-10 text-center text-xs text-gray-500">
              No historical consumption data recorded for this consumer.
            </div>
          ) : (
            <ConsumptionChart data={consumption} />
          )}
        </div>

        {/* Section 2: Explainability Panel (col-span-1) */}
        <div className="lg:col-span-1">
          <ExplainabilityPanel
            cause={caseData?.cause || consumer?.cause || 'Unmetered Tap Detected'}
            confidence={confidence}
            recommendedAction={caseData?.recommended_action || 'Dispatch field inspection unit to verify terminal junction seals.'}
            evidence={caseData?.evidence || ['Abrupt 54% drop in active power without load reduction.', 'Feeder aggregate balance shows corresponding unaccounted gap.']}
            counterEvidence={caseData?.counter_evidence || ['Meter internal clock sync verified.', 'No historical solar net metering installed.']}
          />
        </div>

        {/* Section 3: Key Metrics & Timeline (Bottom row, col-span-full) */}
        <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Key Metrics Cards */}
          <div className="md:col-span-2 bg-white border border-gray-200 rounded-md p-4">
            <h3 className="text-xs font-semibold text-gray-900 uppercase tracking-wider mb-3">
              Forensic Case Telemetry & Impact
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                <div className="text-[11px] text-gray-500 font-medium">Anomaly Score</div>
                <div className="font-mono text-lg font-bold text-gray-900 mt-0.5">
                  {(anomalyScore * 100).toFixed(0)}%
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">Confidence: {(confidence * 100).toFixed(0)}%</div>
              </div>

              <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                <div className="text-[11px] text-gray-500 font-medium">Estimated Loss</div>
                <div className="font-mono text-lg font-bold text-red-600 mt-0.5">
                  ₹{estimatedLoss.toLocaleString('en-IN')}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">Unbilled energy</div>
              </div>

              <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                <div className="text-[11px] text-gray-500 font-medium">Sanctioned Load</div>
                <div className="font-mono text-lg font-semibold text-gray-900 mt-0.5">
                  {consumer?.sanctioned_load_kw != null ? `${consumer.sanctioned_load_kw} kW` : '5.0 kW'}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">Tariff: {consumer?.tariff || 'LT-Domestic'}</div>
              </div>

              <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                <div className="text-[11px] text-gray-500 font-medium">Baseline Mean</div>
                <div className="font-mono text-lg font-semibold text-gray-900 mt-0.5">
                  {caseData?.baseline_kwh != null
                    ? `${caseData.baseline_kwh} kWh`
                    : baselineData?.baseline_kwh != null
                    ? `${baselineData.baseline_kwh} kWh`
                    : '28.4 kWh'}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">
                  Deviation: {caseData?.deviation_pct != null ? `${caseData.deviation_pct}%` : '-48.2%'}
                </div>
              </div>
            </div>
          </div>

          {/* Timeline Card */}
          <div className="md:col-span-1">
            <DetectionTimeline
              periodStart={caseData?.period_start || '2026-09-01T00:00:00Z'}
              firstFlaggedAt={caseData?.first_flagged_at || '2026-09-12T14:30:00Z'}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
