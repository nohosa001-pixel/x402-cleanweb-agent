"""
Eliza Brain Intelligence & Causality Orderbook Router.
Exposes real-time ground-truth signals, predictive causality insights,
and Solana x402 commercial orderbook for autonomous trading bots.
"""
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from eliza_brain.providers.cleanweb_feed import CleanWebIntelligenceFeed
from eliza_brain.memory.causality_graph import CausalityGraph

router = APIRouter()
_feed = CleanWebIntelligenceFeed(filter_threshold=0.45)

class SignalEvaluateRequest(BaseModel):
    clean_text: str = Field(..., description="Purified text or news to analyze")
    source_url: str = Field(..., description="Source origin URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    sync_to_agrid: bool = Field(True, description="Priority 0: Instantly dispatch to A.GRID HQ")

@router.get("/capabilities")
async def get_brain_capabilities():
    """Returns Eliza Brain cognitive reasoning and orderbook capabilities."""
    return {
        "engine": "Eliza Brain Cognitive Layer x CleanWeb",
        "version": "1.0.0",
        "settlement_rail": "Solana Mainnet-Beta (0.4s)",
        "priority_dispatch": "A.GRID Central HQ (Priority 0)",
        "supported_domains": [
            "EUDR_POLICY_SHIFT",
            "MINERAL_SUPPLY_DISRUPTION",
            "GEO_TRADE_ANOMALY",
            "ENERGY_GRID_EVENT"
        ],
        "pricing": {
            "standard_feed_usdc": 0.001,
            "prediction_oracle_premium_usdc": 0.05
        }
    }

@router.get("/orderbook")
async def get_intelligence_orderbook():
    """
    Commercial knowledge orderbook.
    Autonomous agents discover and purchase 0.1-second advance prediction oracles.
    """
    recent_insights = _feed.graph.get_recent_insights(limit=10)
    orderbook_entries = []

    for item in recent_insights:
        orderbook_entries.append({
            "order_id": f"ord_{item['signal_id']}",
            "signal_type": item["signal_type"],
            "importance_score": item["importance_score"],
            "merkle_root": item["merkle_root"],
            "recorded_at": item["recorded_at"],
            "predicted_lag_hours": item.get("prediction", {}).get("predicted_lag_hours", 4),
            "demand_impact": item.get("prediction", {}).get("predicted_agent_demand", ""),
            "price_usdc": 0.05,
            "payment_instruction": {
                "chain": "solana",
                "recipient": "411ksMz9RHYVtVMe6RUUErzZYtrU9zzvkgzswKbqx9qp",
                "token_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "vault": "7oZ16YaazQzN6z5uA1nAZWD9oGUDXyvHwXGJLFYyWi3y"
            }
        })

    return {
        "status": "active",
        "market": "A2A_GROUND_TRUTH_ORDERBOOK",
        "active_orders_count": len(orderbook_entries),
        "orders": orderbook_entries
    }

@router.post("/signals/evaluate")
async def evaluate_signal(req: SignalEvaluateRequest):
    """
    Evaluates raw clean text, records in World Causality Graph,
    and dispatches Priority 0 signal to A.GRID Headquarters.
    """
    result = await _feed.ingest_and_broadcast(
        clean_text=req.clean_text,
        source_url=req.source_url,
        metadata=req.metadata,
        sync_to_agrid=req.sync_to_agrid
    )

    if not result:
        return {
            "status": "IGNORED_LOW_SIGNAL_INTENSITY",
            "message": "Content did not meet the actionable ground-truth threshold."
        }

    return {
        "status": "EVALUATED_AND_DISPATCHED",
        "signal": result["signal"],
        "prediction": result["prediction"]
    }

@router.get("/signals/recent")
async def get_recent_signals(limit: int = Query(10, ge=1, le=50)):
    """Returns recent verified signals and causality predictions."""
    return {
        "count": len(_feed.graph.get_recent_insights(limit)),
        "insights": _feed.graph.get_recent_insights(limit)
    }
