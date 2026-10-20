"""
Eliza Brain Signal Filter & Actionability Evaluator.
Filters out noise, evaluates novelty/ground-truth significance, and computes importance scores (0.0 - 1.0).
"""
import re
import hashlib
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class GroundTruthSignal:
    signal_id: str
    signal_type: str
    importance_score: float
    summary_clean_text: str
    merkle_root: str
    source_url: str
    actionable_intent: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SignalFilter:
    """Evaluates raw cleaned content to extract actionable ground-truth signals."""
    
    HIGH_IMPACT_KEYWORDS = {
        "EUDR_POLICY_SHIFT": [
            "eudr", "deforestation", "due diligence", "geolocation", "moratorium", 
            "european parliament", "delay", "grace period", "compliance deadline"
        ],
        "MINERAL_SUPPLY_DISRUPTION": [
            "export ban", "critical mineral", "lithium", "cobalt", "nickel", 
            "rare earth", "mine shutdown", "refinery strike", "smelter quota"
        ],
        "GEO_TRADE_ANOMALY": [
            "port congestion", "canal closure", "suez", "panama", "strait of malacca", 
            "freight index", "customs blockage", "e-seal tampering"
        ],
        "ENERGY_GRID_EVENT": [
            "grid blackout", "pjm capacity", "ercot peak", "nuclear restart", 
            "curtailment", "data center power", "interconnection delay"
        ]
    }

    def __init__(self, min_threshold: float = 0.5):
        self.min_threshold = min_threshold

    def evaluate(self, clean_text: str, source_url: str, context_meta: Optional[Dict[str, Any]] = None) -> Optional[GroundTruthSignal]:
        """
        Analyzes the text for domain impact, calculating importance and extracting signal classification.
        Returns GroundTruthSignal if score >= min_threshold, else None.
        """
        if not clean_text or len(clean_text.strip()) < 20:
            return None

        clean_lower = clean_text.lower()
        best_type = "GENERAL_INTELLIGENCE"
        best_matches = 0

        for category, keywords in self.HIGH_IMPACT_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in clean_lower)
            if matches > best_matches:
                best_matches = matches
                best_type = category

        # Base score on keyword intensity and length/clarity
        match_ratio = min(best_matches / 4.0, 0.7)
        length_bonus = 0.15 if 100 <= len(clean_text) <= 5000 else 0.05
        urgency_markers = sum(1 for w in ["breaking", "urgent", "immediate", "effective immediately", "mandate", "ban"] if w in clean_lower)
        urgency_score = min(urgency_markers * 0.1, 0.2)

        total_score = round(min(match_ratio + length_bonus + urgency_score, 1.0), 3)

        if total_score < self.min_threshold:
            return None

        # Compute cryptographic deterministic hash
        content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        merkle_root = f"0x{content_hash}"
        signal_id = f"sig_{content_hash[:12]}"

        # Deduce actionable intent
        if best_type == "EUDR_POLICY_SHIFT":
            intent = "Update EUDR compliance risk matrix & dispatch warning to affected supply chain routes."
        elif best_type == "MINERAL_SUPPLY_DISRUPTION":
            intent = "Trigger mineral pricing oracle update & notify commodity escrow vaults."
        elif best_type == "GEO_TRADE_ANOMALY":
            intent = "Re-route autonomous freight contracts and inspect cold-chain e-seals."
        elif best_type == "ENERGY_GRID_EVENT":
            intent = "Adjust data center energy compute pricing and micro-stream reserves."
        else:
            intent = "Log to continuous causality graph for correlation analysis."

        return GroundTruthSignal(
            signal_id=signal_id,
            signal_type=best_type,
            importance_score=total_score,
            summary_clean_text=clean_text[:2000],
            merkle_root=merkle_root,
            source_url=source_url,
            actionable_intent=intent,
            metadata=context_meta or {}
        )
