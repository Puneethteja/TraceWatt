import numpy as np
from typing import Dict, Any, Tuple, List

def triangular_mf(x: float, a: float, b: float, c: float) -> float:
    if x <= a or x >= c:
        return 0.0
    if a < x <= b:
        return (x - a) / (b - a) if b > a else 1.0
    if b < x < c:
        return (c - x) / (c - b) if c > b else 1.0
    return 0.0

def trapezoidal_mf(x: float, a: float, b: float, c: float, d: float) -> float:
    if x <= a or x >= d:
        return 0.0
    if a < x < b:
        return (x - a) / (b - a) if b > a else 1.0
    if b <= x <= c:
        return 1.0
    if c < x < d:
        return (d - x) / (d - c) if d > c else 1.0
    return 0.0

class FuzzyAnomalyEngine:
    """
    TraceWatt Mamdani-style Fuzzy Logic Inference System.
    Evaluates power consumption drops, meter telemetry status, communication stability,
    and peer cohort deviations using linguistic variables and fuzzy rules.
    """

    def __init__(self):
        # Define rule definitions
        self.rules = [
            {
                "id": "R1_THEFT_SEVERE",
                "condition": lambda drop, comm, meter, peer: min(drop["Severe"], 1.0 - comm["High"], 1.0 - meter["Faulty"], peer["Isolated"]),
                "cause": "Theft/Tampering",
                "risk_level": "High",
                "score_center": 0.94,
                "confidence_base": 0.94,
                "action": "Dispatch field inspection unit to verify terminal junction seals.",
                "evidence": "Fuzzy Rule R1 Fired: Severe consumption drop isolated from peer group without telemetry or hardware faults."
            },
            {
                "id": "R2_THEFT_HIGH",
                "condition": lambda drop, comm, meter, peer: min(drop["High"], 1.0 - comm["High"], 1.0 - meter["Faulty"], peer["Isolated"]),
                "cause": "Theft/Tampering",
                "risk_level": "High",
                "score_center": 0.84,
                "confidence_base": 0.88,
                "action": "Dispatch field inspection unit to verify meter seals.",
                "evidence": "Fuzzy Rule R2 Fired: High consumption drop with clean communication and hardware status."
            },
            {
                "id": "R3_METER_FAULT",
                "condition": lambda drop, comm, meter, peer: meter["Faulty"],
                "cause": "Meter Malfunction",
                "risk_level": "Medium",
                "score_center": 0.72,
                "confidence_base": 0.85,
                "action": "Schedule meter diagnostic team for recalibration or replacement.",
                "evidence": "Fuzzy Rule R3 Fired: Hardware fault status registered on CT/PT register."
            },
            {
                "id": "R4_COMM_FAILURE",
                "condition": lambda drop, comm, meter, peer: comm["High"],
                "cause": "Communication Failure",
                "risk_level": "Medium",
                "score_center": 0.58,
                "confidence_base": 0.82,
                "action": "Reset cellular modem interface and test signal strength.",
                "evidence": "Fuzzy Rule R4 Fired: Communication packet loss and telemetry gateway ping timeouts."
            },
            {
                "id": "R5_LEGITIMATE_SEASONAL",
                "condition": lambda drop, comm, meter, peer: min(max(drop["High"], drop["Severe"]), peer["Normal"]),
                "cause": "Legitimate Load Change",
                "risk_level": "Low",
                "score_center": 0.32,
                "confidence_base": 0.86,
                "action": "Update consumer baseline to accommodate peer seasonal shift.",
                "evidence": "Fuzzy Rule R5 Fired: Consumption drop correlated across peer group, indicating seasonal/HVAC shift."
            },
            {
                "id": "R6_NORMAL",
                "condition": lambda drop, comm, meter, peer: drop["Low"],
                "cause": "Normal Pattern",
                "risk_level": "Low",
                "score_center": 0.10,
                "confidence_base": 0.95,
                "action": "No action required.",
                "evidence": "Fuzzy Rule R6 Fired: Consumption within normal 30-day baseline limits."
            }
        ]

    def fuzzify_inputs(self, drop_ratio: float, comm_error: float, meter_fault: float, peer_deviation: float) -> Tuple[Dict, Dict, Dict, Dict]:
        """Convert crisp numeric inputs into fuzzy linguistic term memberships."""
        drop_ratio = float(np.clip(drop_ratio, 0.0, 1.0))
        comm_error = float(np.clip(comm_error, 0.0, 1.0))
        meter_fault = float(np.clip(meter_fault, 0.0, 1.0))
        peer_deviation = float(np.clip(peer_deviation, 0.0, 1.0))

        # 1. Consumption Drop memberships
        drop = {
            "Low": trapezoidal_mf(drop_ratio, 0.0, 0.0, 0.15, 0.30),
            "Medium": triangular_mf(drop_ratio, 0.20, 0.40, 0.60),
            "High": triangular_mf(drop_ratio, 0.50, 0.70, 0.85),
            "Severe": trapezoidal_mf(drop_ratio, 0.75, 0.88, 1.0, 1.0)
        }

        # 2. Communication Error memberships
        comm = {
            "Low": trapezoidal_mf(comm_error, 0.0, 0.0, 0.20, 0.45),
            "High": trapezoidal_mf(comm_error, 0.35, 0.60, 1.0, 1.0)
        }

        # 3. Meter Hardware Fault memberships
        meter = {
            "Clear": trapezoidal_mf(meter_fault, 0.0, 0.0, 0.15, 0.35),
            "Faulty": trapezoidal_mf(meter_fault, 0.25, 0.55, 1.0, 1.0)
        }

        # 4. Peer Cohort Deviation memberships (Isolated vs Normal)
        peer = {
            "Normal": trapezoidal_mf(peer_deviation, 0.0, 0.0, 0.25, 0.45),
            "Isolated": trapezoidal_mf(peer_deviation, 0.35, 0.60, 1.0, 1.0)
        }

        return drop, comm, meter, peer

    def evaluate(self, drop_ratio: float, comm_error: float, meter_fault: float, peer_deviation: float) -> Dict[str, Any]:
        """
        Execute Mamdani fuzzy inference and defuzzify via Weighted Centroid Average.
        """
        drop, comm, meter, peer = self.fuzzify_inputs(drop_ratio, comm_error, meter_fault, peer_deviation)

        fired_rules = []
        total_weight = 0.0
        weighted_score_sum = 0.0
        winning_rule = None
        max_strength = -1.0

        for r in self.rules:
            strength = r["condition"](drop, comm, meter, peer)
            if strength > 0.01:
                fired_rules.append({
                    "id": r["id"],
                    "strength": round(strength, 3),
                    "cause": r["cause"],
                    "risk_level": r["risk_level"],
                    "evidence": r["evidence"]
                })
                weighted_score_sum += strength * r["score_center"]
                total_weight += strength

                if strength > max_strength:
                    max_strength = strength
                    winning_rule = r

        # Default fallback if no rules fired strongly
        if total_weight > 0.0:
            anomaly_score = weighted_score_sum / total_weight
        else:
            anomaly_score = 0.10
            winning_rule = self.rules[-1] # R6_NORMAL

        anomaly_score = round(float(np.clip(anomaly_score, 0.0, 1.0)), 2)
        confidence = round(float(winning_rule["confidence_base"] * max(max_strength, 0.70)), 2)

        # Structure explainability payload
        evidence_list = [r["evidence"] for r in fired_rules] if fired_rules else [winning_rule["evidence"]]
        counter_evidence_list = []

        if comm["High"] > 0.2:
            counter_evidence_list.append("Cellular gateway report indicates network packet dropout.")
        if meter["Faulty"] > 0.2:
            counter_evidence_list.append("Meter diagnostic flag indicates internal hardware register fault.")
        if peer["Normal"] > 0.2:
            counter_evidence_list.append("Peer group displays similar consumption trend.")
        if not counter_evidence_list:
            counter_evidence_list.append("No hardware or communication interference detected.")

        return {
            "anomaly_score": anomaly_score,
            "risk_level": winning_rule["risk_level"],
            "probable_cause": winning_rule["cause"],
            "confidence": confidence,
            "recommended_action": winning_rule["action"],
            "evidence": evidence_list,
            "counter_evidence": counter_evidence_list,
            "fuzzy_memberships": {
                "drop": {k: round(v, 2) for k, v in drop.items()},
                "comm": {k: round(v, 2) for k, v in comm.items()},
                "meter": {k: round(v, 2) for k, v in meter.items()},
                "peer": {k: round(v, 2) for k, v in peer.items()}
            },
            "fired_rules": fired_rules
        }

# Global singleton instance
fuzzy_engine = FuzzyAnomalyEngine()
