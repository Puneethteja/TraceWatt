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
  const { id } = useParams();

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
      <div className="max-w-6xl mx-auto py-12 text-center font-sans text-xs text-gray-500">
        Loading data...
      </div>
    );
  }

  if (!consumer && !caseData && !isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center font-sans">
        <h2 className="text-base font-semibold text-gray-900 tracking-tight">Consumer Record Unavailable</h2>
        <p className="text-xs text-gray-500 mt-1">
          No record found for consumer ID <span className="font-mono text-gray-700">{id}</span>.
        </p>
        <div className="mt-4">
          <Link
            to="/consumers"
            className="inline-flex items-center bg-white border border-gray-300 text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md px-3 py-1.5 text-sm transition-colors duration-150"
          >
            ← Back to List
          </Link>
        </div>
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

  const riskLevel = consumer?.risk_level || caseData?.risk_level || '-';
  const consumerId = consumer?.consumer_id || caseData?.consumer_id || id;
  const status = consumer?.status || caseData?.status || '-';
  const priorityRank = consumer?.priority_rank ?? caseData?.priority_rank;
  const anomalyScore = consumer?.anomaly_score ?? caseData?.anomaly_score;
  const estimatedLoss = consumer?.estimated_loss ?? caseData?.estimated_loss;
  const confidence = caseData?.confidence ?? consumer?.confidence;

  return (
    <div className="space-y-4 max-w-6xl mx-auto font-sans">
      {/* Inline Flat Error Banner */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-2 rounded">
          {errorMessage}
        </div>
      )}

      {/* Header Bar */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <Link
            to="/consumers"
            className="bg-white border border-gray-300 text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150"
          >
            ← Back to List
          </Link>
          <div className="h-4 w-px bg-gray-200 hidden sm:block" />
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-mono text-base font-bold text-gray-900">
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
            <div className="text-xs text-gray-500 mt-0.5 space-x-2">
              <span>Meter: <strong className="font-mono text-gray-700">{consumer?.meter_id || '-'}</strong></span>
              <span>•</span>
              <span>Category: <strong className="text-gray-700">{consumer?.category || '-'}</strong></span>
              <span>•</span>
              <span>Feeder: <strong className="font-mono text-gray-700">{consumer?.feeder_id || '-'}</strong></span>
            </div>
          </div>
        </div>

        <div className="text-xs text-gray-500 text-left sm:text-right font-mono">
          Priority Rank {priorityRank != null ? `#${priorityRank}` : '-'}
        </div>
      </div>

      {/* 2-Column Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Top row: ConsumptionChart (col-span-2) */}
        <div className="col-span-1 md:col-span-2">
          {consumption.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg p-10 text-center font-sans text-xs text-gray-500">
              No historical data available for this consumer.
            </div>
          ) : (
            <ConsumptionChart data={consumption} />
          )}
        </div>

        {/* Bottom left: ExplainabilityPanel */}
        <div>
          <ExplainabilityPanel
            cause={caseData?.cause || consumer?.cause || '-'}
            confidence={confidence}
            recommendedAction={caseData?.recommended_action || '-'}
            evidence={caseData?.evidence || []}
            counterEvidence={caseData?.counter_evidence || []}
          />
        </div>

        {/* Bottom right: DetectionTimeline & Key Metrics */}
        <div className="space-y-4 flex flex-col">
          <DetectionTimeline
            periodStart={caseData?.period_start}
            firstFlaggedAt={caseData?.first_flagged_at}
          />

          {/* Simple Key Metrics Box */}
          <div className="bg-white border border-gray-200 rounded-lg p-4 flex-1">
            <h4 className="text-xs font-semibold text-gray-900 uppercase tracking-wider tracking-tight mb-3">
              Key Metrics & Loss Impact
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                <div className="text-[11px] text-gray-500 font-medium">Anomaly Score</div>
                <div className="font-mono text-base font-bold text-gray-900 mt-0.5">
                  {anomalyScore != null ? `${(anomalyScore * 100).toFixed(0)}%` : '-'}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">Statistical deviation</div>
              </div>

              <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                <div className="text-[11px] text-gray-500 font-medium">Estimated Loss</div>
                <div className="font-mono text-base font-bold text-red-600 mt-0.5">
                  {estimatedLoss != null ? `₹${estimatedLoss.toLocaleString('en-IN')}` : '-'}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">Unbilled energy estimate</div>
              </div>

              <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                <div className="text-[11px] text-gray-500 font-medium">Sanctioned Load</div>
                <div className="font-mono text-sm font-semibold text-gray-900 mt-0.5">
                  {consumer?.sanctioned_load_kw != null ? `${consumer.sanctioned_load_kw} kW` : '-'}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">Tariff: {consumer?.tariff || '-'}</div>
              </div>

              <div className="border border-gray-200 rounded-md p-3 bg-gray-50/50">
                <div className="text-[11px] text-gray-500 font-medium">Baseline Consumption</div>
                <div className="font-mono text-sm font-semibold text-gray-900 mt-0.5">
                  {caseData?.baseline_kwh != null
                    ? `${caseData.baseline_kwh} kWh`
                    : baselineData?.baseline_kwh != null
                    ? `${baselineData.baseline_kwh} kWh`
                    : '-'}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">
                  Deviation: {caseData?.deviation_pct != null ? `${caseData.deviation_pct}%` : '-'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
