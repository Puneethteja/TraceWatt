/**
 * Mock data matching TraceWatt Pydantic Schemas
 * Used for Phase 1 frontend development and offline mocking.
 */

// Schema: ConsumerSummary
export const mockConsumers = [
  {
    consumer_id: 'CONS-10492',
    meter_id: 'MTR-98214',
    category: 'Commercial',
    sanctioned_load_kw: 15.0,
    tariff: 'COMM-LT-2',
    transformer_id: 'TRF-NORTH-04',
    feeder_id: 'FDR-N04-A',
    anomaly_score: 0.94,
    risk_level: 'High',
    cause: 'Theft/Tampering',
    confidence: 0.92,
    status: 'OPEN',
    estimated_loss: 45200.0,
    priority_rank: 1,
  },
  {
    consumer_id: 'CONS-20831',
    meter_id: 'MTR-77402',
    category: 'Industrial',
    sanctioned_load_kw: 45.0,
    tariff: 'IND-HT-1',
    transformer_id: 'TRF-EAST-12',
    feeder_id: 'FDR-E12-B',
    anomaly_score: 0.88,
    risk_level: 'High',
    cause: 'Bypass / Direct Hook',
    confidence: 0.89,
    status: 'INVESTIGATING',
    estimated_loss: 68400.0,
    priority_rank: 2,
  },
  {
    consumer_id: 'CONS-31045',
    meter_id: 'MTR-55321',
    category: 'Residential',
    sanctioned_load_kw: 5.0,
    tariff: 'DOM-LT-1',
    transformer_id: 'TRF-SOUTH-02',
    feeder_id: 'FDR-S02-C',
    anomaly_score: 0.72,
    risk_level: 'Medium',
    cause: 'Meter Malfunction',
    confidence: 0.78,
    status: 'FLAGGED',
    estimated_loss: 14300.0,
    priority_rank: 3,
  },
  {
    consumer_id: 'CONS-41982',
    meter_id: 'MTR-33981',
    category: 'Commercial',
    sanctioned_load_kw: 20.0,
    tariff: 'COMM-LT-2',
    transformer_id: 'TRF-WEST-08',
    feeder_id: 'FDR-W08-A',
    anomaly_score: 0.65,
    risk_level: 'Medium',
    cause: 'Phase Inversion / Neutral Cut',
    confidence: 0.71,
    status: 'OPEN',
    estimated_loss: 19800.0,
    priority_rank: 4,
  },
  {
    consumer_id: 'CONS-55219',
    meter_id: 'MTR-12904',
    category: 'Agricultural',
    sanctioned_load_kw: 10.0,
    tariff: 'AGR-LT-3',
    transformer_id: 'TRF-NORTH-04',
    feeder_id: 'FDR-N04-A',
    anomaly_score: 0.58,
    risk_level: 'Medium',
    cause: 'Requires Review',
    confidence: 0.64,
    status: 'UNDER_REVIEW',
    estimated_loss: 11400.0,
    priority_rank: 5,
  },
  {
    consumer_id: 'CONS-60124',
    meter_id: 'MTR-44219',
    category: 'Residential',
    sanctioned_load_kw: 3.0,
    tariff: 'DOM-LT-1',
    transformer_id: 'TRF-CENTRAL-01',
    feeder_id: 'FDR-C01-B',
    anomaly_score: 0.18,
    risk_level: 'Low',
    cause: 'Seasonal Fluctuation',
    confidence: 0.52,
    status: 'CLOSED',
    estimated_loss: 450.0,
    priority_rank: 6,
  },
];

// Schema: CaseOut
export const mockCases = [
  {
    consumer_id: 'CONS-10492',
    anomaly_score: 0.94,
    risk_level: 'High',
    cause: 'Theft/Tampering',
    confidence: 0.92,
    period_start: '2026-09-01T00:00:00Z',
    period_end: '2026-09-30T23:59:59Z',
    baseline_kwh: 2450.0,
    actual_kwh: 580.0,
    deviation_pct: -76.3,
    evidence: [
      'Sudden 76% drop in daily consumption coinciding with peak cooling season',
      'Zero night-time base load recorded for 18 consecutive days',
      'Transformer energy delta of 38 kWh/day unmetered on feeder FDR-N04-A',
    ],
    counter_evidence: [
      'No formal meter outage reported by utility dispatch',
      'Neighboring commercial units show typical consumption patterns',
    ],
    recommended_action: 'Deploy field inspection team for physical meter enclosure inspection and CT bypass verification.',
    status: 'OPEN',
    note: 'Priority 1 case flagged by XGBoost ensemble model. High probability of meter tampering.',
    estimated_loss: 45200.0,
    priority_rank: 1,
    first_flagged_at: '2026-09-15T08:30:00Z',
    updated_at: '2026-10-02T11:15:00Z',
  },
  {
    consumer_id: 'CONS-20831',
    anomaly_score: 0.88,
    risk_level: 'High',
    cause: 'Bypass / Direct Hook',
    confidence: 0.89,
    period_start: '2026-09-01T00:00:00Z',
    period_end: '2026-09-30T23:59:59Z',
    baseline_kwh: 8900.0,
    actual_kwh: 2300.0,
    deviation_pct: -74.1,
    evidence: [
      'Discrepancy between sanctioned load (45 kW) and recorded maximum demand (12 kW)',
      'Substation feeder logs reveal 60A current imbalance during evening shifts',
    ],
    counter_evidence: [
      'Consumer claimed partial factory maintenance during early September',
    ],
    recommended_action: 'Perform unannounced nocturnal inspection with infrared thermal imaging.',
    status: 'INVESTIGATING',
    note: 'Field investigator assigned. Awaiting meter tamper seal review.',
    estimated_loss: 68400.0,
    priority_rank: 2,
    first_flagged_at: '2026-09-10T14:20:00Z',
    updated_at: '2026-10-01T16:45:00Z',
  },
  {
    consumer_id: 'CONS-31045',
    anomaly_score: 0.72,
    risk_level: 'Medium',
    cause: 'Meter Malfunction',
    confidence: 0.78,
    period_start: '2026-09-01T00:00:00Z',
    period_end: '2026-09-30T23:59:59Z',
    baseline_kwh: 620.0,
    actual_kwh: 120.0,
    deviation_pct: -80.6,
    evidence: [
      'Intermittent telemetry packet drop and flatline readings for 4-hour windows',
      'Hardware error code ERR_RTC_DRIFT recorded in meter diagnostics',
    ],
    counter_evidence: [
      'No physical seal breach reported',
    ],
    recommended_action: 'Recalibrate and replace smart meter unit MTR-55321.',
    status: 'FLAGGED',
    note: 'Suspected faulty current transformer or optical sensor defect.',
    estimated_loss: 14300.0,
    priority_rank: 3,
    first_flagged_at: '2026-09-18T09:00:00Z',
    updated_at: '2026-09-28T10:10:00Z',
  },
  {
    consumer_id: 'CONS-41982',
    anomaly_score: 0.65,
    risk_level: 'Medium',
    cause: 'Phase Inversion / Neutral Cut',
    confidence: 0.71,
    period_start: '2026-09-01T00:00:00Z',
    period_end: '2026-09-30T23:59:59Z',
    baseline_kwh: 3100.0,
    actual_kwh: 1450.0,
    deviation_pct: -53.2,
    evidence: [
      'Neutral current drop to 0A with asymmetric phase loading',
      'Reverse active power indicator intermittently triggered',
    ],
    counter_evidence: [],
    recommended_action: 'Verify terminal neutral wiring and earthing resistance.',
    status: 'OPEN',
    note: 'Review neutral isolation or earthing bypass.',
    estimated_loss: 19800.0,
    priority_rank: 4,
    first_flagged_at: '2026-09-22T13:45:00Z',
    updated_at: '2026-10-02T09:05:00Z',
  },
  {
    consumer_id: 'CONS-55219',
    anomaly_score: 0.58,
    risk_level: 'Medium',
    cause: 'Requires Review',
    confidence: 0.64,
    period_start: '2026-09-01T00:00:00Z',
    period_end: '2026-09-30T23:59:59Z',
    baseline_kwh: 1200.0,
    actual_kwh: 520.0,
    deviation_pct: -56.7,
    evidence: [
      'Sharp consumption drop of 57% during peak harvest pumping period',
      'Feeder total unmetered energy increased concurrently by 18 kWh/day',
    ],
    counter_evidence: [
      'Missing distribution transformer telemetry packets for past 72 hours',
      'Unverified rooftop solar net-metering application logged with DISCOM',
    ],
    recommended_action: 'Dispatch surveyor to verify solar installation and check distribution transformer secondary CT.',
    status: 'UNDER_REVIEW',
    note: 'Inconclusive telemetry. Review pending on-site solar net-metering validation.',
    estimated_loss: 11400.0,
    priority_rank: 5,
    first_flagged_at: '2026-09-21T11:00:00Z',
    updated_at: '2026-10-02T17:00:00Z',
  },
  {
    consumer_id: 'CONS-60124',
    anomaly_score: 0.18,
    risk_level: 'Low',
    cause: 'Seasonal Fluctuation',
    confidence: 0.52,
    period_start: '2026-09-01T00:00:00Z',
    period_end: '2026-09-30T23:59:59Z',
    baseline_kwh: 350.0,
    actual_kwh: 310.0,
    deviation_pct: -11.4,
    evidence: [
      'Normal post-summer cooling demand decrease',
    ],
    counter_evidence: [
      'Historical monthly profiles show identical seasonal drop in previous years',
    ],
    recommended_action: 'Close case as legitimate consumption variance.',
    status: 'CLOSED',
    note: 'Verified legitimate pattern variance.',
    estimated_loss: 450.0,
    priority_rank: 6,
    first_flagged_at: '2026-09-20T10:15:00Z',
    updated_at: '2026-10-01T14:30:00Z',
  },
];

// Schema: FeederOut
export const mockFeeders = [
  {
    feeder_id: 'FDR-N04-A',
    name: 'North Industrial Feeder A',
    transformer_count: 8,
    total_unexplained_loss_pct: 25.4,
    cluster_flag: true,
  },
  {
    feeder_id: 'FDR-E12-B',
    name: 'East Commercial Feeder B',
    transformer_count: 12,
    total_unexplained_loss_pct: 18.9,
    cluster_flag: true,
  },
  {
    feeder_id: 'FDR-W08-A',
    name: 'West Sector Feeder A',
    transformer_count: 6,
    total_unexplained_loss_pct: 10.6,
    cluster_flag: false,
  },
  {
    feeder_id: 'FDR-S02-C',
    name: 'South Residential Feeder C',
    transformer_count: 5,
    total_unexplained_loss_pct: 7.6,
    cluster_flag: false,
  },
];

// Schema: FeederSummaryOut
export const mockFeederLosses = [
  {
    transformer_id: 'TRF-NORTH-04',
    feeder_id: 'FDR-N04-A',
    window_start: '2026-09-01',
    window_end: '2026-09-05',
    energy_in_kwh: 12500.0,
    energy_metered_kwh: 9200.0,
    unexplained_loss_pct: 26.4,
    cluster_score: 0.88,
    cluster_flag: 1,
  },
  {
    transformer_id: 'TRF-NORTH-04',
    feeder_id: 'FDR-N04-A',
    window_start: '2026-09-06',
    window_end: '2026-09-10',
    energy_in_kwh: 13200.0,
    energy_metered_kwh: 9800.0,
    unexplained_loss_pct: 25.7,
    cluster_score: 0.85,
    cluster_flag: 1,
  },
  {
    transformer_id: 'TRF-NORTH-04',
    feeder_id: 'FDR-N04-A',
    window_start: '2026-09-11',
    window_end: '2026-09-15',
    energy_in_kwh: 14100.0,
    energy_metered_kwh: 10100.0,
    unexplained_loss_pct: 28.3,
    cluster_score: 0.92,
    cluster_flag: 1,
  },
  {
    transformer_id: 'TRF-NORTH-04',
    feeder_id: 'FDR-N04-A',
    window_start: '2026-09-16',
    window_end: '2026-09-20',
    energy_in_kwh: 13800.0,
    energy_metered_kwh: 10400.0,
    unexplained_loss_pct: 24.6,
    cluster_score: 0.81,
    cluster_flag: 1,
  },
  {
    transformer_id: 'TRF-NORTH-04',
    feeder_id: 'FDR-N04-A',
    window_start: '2026-09-21',
    window_end: '2026-09-25',
    energy_in_kwh: 14500.0,
    energy_metered_kwh: 10800.0,
    unexplained_loss_pct: 25.5,
    cluster_score: 0.87,
    cluster_flag: 1,
  },
  {
    transformer_id: 'TRF-NORTH-04',
    feeder_id: 'FDR-N04-A',
    window_start: '2026-09-26',
    window_end: '2026-09-30',
    energy_in_kwh: 13900.0,
    energy_metered_kwh: 10200.0,
    unexplained_loss_pct: 26.6,
    cluster_score: 0.90,
    cluster_flag: 1,
  },
];

// Correlated high-scoring consumers on suspicious feeder clusters
export const mockClusterConsumers = [
  {
    consumer_id: 'CONS-10492',
    anomaly_score: 0.94,
    estimated_loss: 45200.0,
    feeder_id: 'FDR-N04-A',
    transformer_id: 'TRF-NORTH-04',
  },
  {
    consumer_id: 'CONS-91482',
    anomaly_score: 0.81,
    estimated_loss: 32100.0,
    feeder_id: 'FDR-N04-A',
    transformer_id: 'TRF-NORTH-04',
  },
  {
    consumer_id: 'CONS-78210',
    anomaly_score: 0.74,
    estimated_loss: 24500.0,
    feeder_id: 'FDR-N04-A',
    transformer_id: 'TRF-NORTH-04',
  },
  {
    consumer_id: 'CONS-55219',
    anomaly_score: 0.58,
    estimated_loss: 11400.0,
    feeder_id: 'FDR-N04-A',
    transformer_id: 'TRF-NORTH-04',
  },
];

// Schema: 30-day Daily Consumption Series
export const mockConsumption = [
  { ts: '2026-09-01', kwh: 34.2 },
  { ts: '2026-09-02', kwh: 35.8 },
  { ts: '2026-09-03', kwh: 33.9 },
  { ts: '2026-09-04', kwh: 36.1 },
  { ts: '2026-09-05', kwh: 34.5 },
  { ts: '2026-09-06', kwh: 37.0 },
  { ts: '2026-09-07', kwh: 35.2 },
  { ts: '2026-09-08', kwh: 33.8 },
  { ts: '2026-09-09', kwh: 36.4 },
  { ts: '2026-09-10', kwh: 35.1 },
  { ts: '2026-09-11', kwh: 34.7 },
  { ts: '2026-09-12', kwh: 36.9 },
  { ts: '2026-09-13', kwh: 35.5 },
  { ts: '2026-09-14', kwh: 34.0 },
  { ts: '2026-09-15', kwh: 33.6 },
  { ts: '2026-09-16', kwh: 14.2 },
  { ts: '2026-09-17', kwh: 8.5 },
  { ts: '2026-09-18', kwh: 9.1 },
  { ts: '2026-09-19', kwh: 7.8 },
  { ts: '2026-09-20', kwh: 8.2 },
  { ts: '2026-09-21', kwh: 9.0 },
  { ts: '2026-09-22', kwh: 8.4 },
  { ts: '2026-09-23', kwh: 7.9 },
  { ts: '2026-09-24', kwh: 8.6 },
  { ts: '2026-09-25', kwh: 9.3 },
  { ts: '2026-09-26', kwh: 8.1 },
  { ts: '2026-09-27', kwh: 7.7 },
  { ts: '2026-09-28', kwh: 8.9 },
  { ts: '2026-09-29', kwh: 8.3 },
  { ts: '2026-09-30', kwh: 8.0 },
];

// Schema: Monthly Baseline & Peer Quantile Bounds
export const mockBaseline = [
  { month: '2026-07', baseline_kwh: 34.5, peer_p25: 28.0, peer_p75: 42.0 },
  { month: '2026-08', baseline_kwh: 35.2, peer_p25: 29.0, peer_p75: 43.5 },
  { month: '2026-09', baseline_kwh: 35.0, peer_p25: 28.5, peer_p75: 43.0 },
];

/**
 * Returns merged 30-day time-series for Recharts ConsumptionChart.
 * Integrates daily actuals (kwh), baseline (baseline_kwh), and peer quantile band (peer_p25 to peer_p75).
 */
export const getConsumptionChartData = (consumerId) => {
  const isAnomalous = ['CONS-10492', 'CONS-20831', 'CONS-31045', 'CONS-41982'].includes(consumerId);
  const baseScale = consumerId === 'CONS-20831' ? 3.0 : consumerId === 'CONS-31045' ? 0.4 : 1.0;

  return mockConsumption.map((item, idx) => {
    const dayOfMonth = idx + 1;
    // Base normal expected usage around 35 kWh * scale
    const base = parseFloat((35.0 * baseScale + Math.sin(dayOfMonth * 0.5) * 2.0).toFixed(1));
    const p25 = parseFloat((base * 0.82).toFixed(1));
    const p75 = parseFloat((base * 1.22).toFixed(1));

    let actual = parseFloat((item.kwh * baseScale).toFixed(1));
    if (!isAnomalous) {
      // Normal consumers stay near baseline
      actual = parseFloat((base + (Math.sin(dayOfMonth) * 2.5)).toFixed(1));
    }

    return {
      ts: item.ts,
      kwh: actual,
      baseline_kwh: base,
      peer_p25: p25,
      peer_p75: p75,
      // For Recharts Area range support: [p25, p75]
      peer_band: [p25, p75],
    };
  });
};

// Helper to generate mock consumption time-series for a consumer
export const generateMockConsumption = (consumerId) => {
  const points = [];
  const baseAvg = consumerId === 'CONS-20831' ? 120 : consumerId === 'CONS-10492' ? 35 : 12;
  const isAnomalous = ['CONS-10492', 'CONS-20831'].includes(consumerId);

  for (let i = 29; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];
    
    // Anomaly drops drastically in the last 15 days
    const dropFactor = isAnomalous && i <= 15 ? 0.25 : 1.0;
    const variance = 1 + (Math.sin(i * 0.8) * 0.15);
    const actual = parseFloat((baseAvg * dropFactor * variance).toFixed(2));
    const baseline = parseFloat((baseAvg * variance).toFixed(2));

    points.push({
      date: dateStr,
      actual_kwh: actual,
      baseline_kwh: baseline,
      anomaly_flag: isAnomalous && i <= 15,
    });
  }
  return points;
};

// Initial alerts matching AlertOut schema
export const mockAlerts = [
  {
    id: 'ALT-8821',
    consumer_id: 'CONS-10492',
    ts: '2026-10-03 14:15:20',
    risk_level: 'High',
    cause: 'Theft/Tampering',
    message: 'Persistent zero night-load deviation detected on distribution feeder FDR-N04-A.',
  },
  {
    id: 'ALT-8820',
    consumer_id: 'CONS-20831',
    ts: '2026-10-03 13:42:05',
    risk_level: 'High',
    cause: 'Bypass / Direct Hook',
    message: 'Current imbalance of 60A recorded during nocturnal industrial shift.',
  },
  {
    id: 'ALT-8819',
    consumer_id: 'CONS-31045',
    ts: '2026-10-03 12:05:44',
    risk_level: 'Medium',
    cause: 'Meter Malfunction',
    message: 'Hardware clock drift flag ERR_RTC_DRIFT recorded with flatline consumption.',
  },
  {
    id: 'ALT-8818',
    consumer_id: 'CONS-41982',
    ts: '2026-10-03 10:18:30',
    risk_level: 'Low',
    cause: 'Phase Inversion / Neutral Cut',
    message: 'Reverse active power intermittently registered on commercial meter terminal.',
  },
];

const SIMULATION_POOL = [
  {
    consumer_id: 'CONS-10492',
    risk_level: 'High',
    cause: 'Theft/Tampering',
    message: 'Sudden 74% consumption drop detected against seasonal baseline.',
  },
  {
    consumer_id: 'CONS-20831',
    risk_level: 'High',
    cause: 'Bypass / Direct Hook',
    message: 'Transformer TRF-EAST-12 unexplained loss spiked to 28.5%.',
  },
  {
    consumer_id: 'CONS-55219',
    risk_level: 'Medium',
    cause: 'Requires Review',
    message: 'Inconclusive net-metering solar telemetry discrepancy flagged.',
  },
  {
    consumer_id: 'CONS-41982',
    risk_level: 'Medium',
    cause: 'Phase Inversion / Neutral Cut',
    message: 'Neutral line current dropped to 0.0A with active phase draw.',
  },
  {
    consumer_id: 'CONS-31045',
    risk_level: 'Low',
    cause: 'Meter Malfunction',
    message: 'Optical telemetry pulse error confirmed during continuous scan.',
  },
];

/**
 * Starts mock IoT alert generator emitting a new alert every 12 seconds.
 * @param {Function} onNewAlert Callback invoked with new alert item.
 * @returns {Function} Cleanup function to stop simulation.
 */
export const startMockAlertSimulation = (onNewAlert) => {
  let counter = 8822;

  const intervalId = setInterval(() => {
    const template = SIMULATION_POOL[Math.floor(Math.random() * SIMULATION_POOL.length)];
    const now = new Date();
    const dateFormatted = now.toISOString().replace('T', ' ').slice(0, 19);

    const alertItem = {
      id: `ALT-${counter++}`,
      consumer_id: template.consumer_id,
      ts: dateFormatted,
      risk_level: template.risk_level,
      cause: template.cause,
      message: template.message,
    };

    if (typeof onNewAlert === 'function') {
      onNewAlert(alertItem);
    }
  }, 12000);

  return () => clearInterval(intervalId);
};
