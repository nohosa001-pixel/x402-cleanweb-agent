"""
Causality Graph Memory for Eliza Brain.
Tracks cause-and-effect chains and predicts upcoming agent market movements.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from eliza_brain.evaluators.signal_filter import GroundTruthSignal

class CausalityGraph:
    """In-memory causality graph mapping antecedent events to predicted market reactions."""

    PREDICTION_RULES = {
        "EUDR_POLICY_SHIFT": {
            "predicted_lag_hours": 4,
            "predicted_agent_demand": "High demand for EUDR audit & polygon satellite proofs",
            "recommended_action": "Prime A.GRID EUDR clearinghouse liquidity"
        },
        "MINERAL_SUPPLY_DISRUPTION": {
            "predicted_lag_hours": 2,
            "predicted_agent_demand": "Surge in hedging & RWA escrow queries for cobalt/lithium",
            "recommended_action": "Update minerals-oracle-x402 feeds and lock in supplier delivery stakes"
        },
        "GEO_TRADE_ANOMALY": {
            "predicted_lag_hours": 1,
            "predicted_agent_demand": "Port container ETA recalculation and e-seal dispute filings",
            "recommended_action": "Enforce GPS geofence invariants on all maritime smart escrows"
        },
        "ENERGY_GRID_EVENT": {
            "predicted_lag_hours": 0.5,
            "predicted_agent_demand": "GPU compute cluster shifting to lower tariff regional nodes",
            "recommended_action": "Stream Solana DePIN dynamic micro-settlement adjustments"
        }
    }

    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self._history: List[Dict[str, Any]] = []

    def record_and_predict(self, signal: GroundTruthSignal) -> Dict[str, Any]:
        """Records a signal into memory and derives predictions for front-running agent demands."""
        rule = self.PREDICTION_RULES.get(signal.signal_type, {
            "predicted_lag_hours": 12,
            "predicted_agent_demand": "General LLM market context update",
            "recommended_action": "Store in knowledge base"
        })

        entry = {
            "signal_id": signal.signal_id,
            "signal_type": signal.signal_type,
            "importance_score": signal.importance_score,
            "merkle_root": signal.merkle_root,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "prediction": rule
        }

        self._history.append(entry)
        if len(self._history) > self.max_history:
            self._history.pop(0)

        return entry

    def get_recent_insights(self, limit: int = 10) -> List[Dict[str, Any]]:
        return list(reversed(self._history[-limit:]))
