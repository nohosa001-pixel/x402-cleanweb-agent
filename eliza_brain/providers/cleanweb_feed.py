"""
CleanWeb Intelligence Provider Feed for external agents & A.GRID 사령부.
Provides sub-second prediction context and verified ground-truth knowledge streams.
"""
from typing import Dict, Any, List, Optional
from eliza_brain.evaluators.signal_filter import SignalFilter, GroundTruthSignal
from eliza_brain.memory.causality_graph import CausalityGraph
from app.agrid_ops_client import dispatch_early_signal_background, dispatch_early_signal_to_agrid_async

class CleanWebIntelligenceFeed:
    """Unified cognitive orchestrator connecting CleanWeb scrubbing, Eliza Brain causality, and A.GRID delivery."""

    def __init__(self, filter_threshold: float = 0.5):
        self.filter = SignalFilter(min_threshold=filter_threshold)
        self.graph = CausalityGraph()

    async def ingest_and_broadcast(
        self,
        clean_text: str,
        source_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        sync_to_agrid: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        1. Evaluates clean text for actionable ground truth.
        2. Derives market prediction in CausalityGraph.
        3. Priority 0: Dispatches immediately to A.GRID HQ.
        4. Returns the synthesized intelligence payload.
        """
        signal = self.filter.evaluate(clean_text, source_url, metadata)
        if not signal:
            return None

        prediction_report = self.graph.record_and_predict(signal)

        # Priority 0 Dispatch to A.GRID
        if sync_to_agrid:
            dispatch_early_signal_background(
                signal_type=signal.signal_type,
                importance_score=signal.importance_score,
                summary_clean_text=signal.summary_clean_text,
                merkle_root=signal.merkle_root,
                source_url=signal.source_url,
                metadata={
                    **(metadata or {}),
                    "actionable_intent": signal.actionable_intent,
                    "prediction": prediction_report.get("prediction", {})
                }
            )

        return {
            "signal": {
                "id": signal.signal_id,
                "type": signal.signal_type,
                "importance": signal.importance_score,
                "merkle_root": signal.merkle_root,
                "intent": signal.actionable_intent,
            },
            "prediction": prediction_report.get("prediction", {})
        }
