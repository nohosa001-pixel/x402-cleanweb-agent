"""A.GRID Ops Central Hub Client for CleanWeb Studio.
Asynchronously dispatches micropayment & A2A clearing events to the central agrid-ops-agent headquarters.
"""
import os
import uuid
import logging
import asyncio
import json
import urllib.request
from typing import Optional, Dict, Any

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger("agrid_ops_client")

AGRID_OPS_URL = os.getenv("AGRID_OPS_URL", "http://localhost:8080")
AGRID_SYNC_ENABLED = os.getenv("AGRID_SYNC_ENABLED", "true").lower() in ("true", "1", "yes")

async def report_clearing_event_async(
    operation: str,
    amount_usdc: float,
    caller_agent_id: str,
    source_service: str = "cleanweb-studio",
    chain: str = "polygon",
    tx_hash: Optional[str] = None,
    is_a2a_delegation: bool = False,
    target_service: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Sends a clearing event to agrid-ops-agent for central double-entry accounting journal entries.
    Executes with a fast timeout (2.0s) so it never blocks or slows down M2M sub-5ms client requests.
    """
    if not AGRID_SYNC_ENABLED:
        return None

    event_payload = {
        "event_id": f"evt_cw_{uuid.uuid4().hex[:12]}",
        "source_service": source_service,
        "caller_agent_id": caller_agent_id or "anonymous_agent",
        "operation": operation,
        "amount_usdc": float(amount_usdc),
        "chain": chain,
        "tx_hash": tx_hash,
        "is_a2a_delegation": is_a2a_delegation,
        "target_service": target_service,
    }

    try:
        if httpx is not None:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.post(f"{AGRID_OPS_URL}/api/v1/grid/clearing/event", json=event_payload)
                if res.is_success:
                    data = res.json()
                    logger.info(f"[A.GRID-HQ] Cleared event {event_payload['event_id']} (₩{data.get('amount_krw', 0):,})")
                    return data
                else:
                    logger.debug(f"[A.GRID-HQ] Non-200 response: {res.status_code}")
                    return None
        else:
            # Fallback to stdlib urllib via threadpool if httpx is not installed
            def _sync_post():
                req = urllib.request.Request(
                    f"{AGRID_OPS_URL}/api/v1/grid/clearing/event",
                    data=json.dumps(event_payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    if 200 <= resp.status < 300:
                        return json.loads(resp.read().decode("utf-8"))
                    return None
            return await asyncio.to_thread(_sync_post)
    except Exception as exc:
        # Graceful fallback: Never break CleanWeb operations if central ops agent is offline
        logger.debug(f"[A.GRID-HQ] Central sync skipped (offline or timeout): {exc}")
        return None


def dispatch_clearing_event_background(
    operation: str,
    amount_usdc: float,
    caller_agent_id: str,
    chain: str = "polygon",
    tx_hash: Optional[str] = None,
    is_a2a_delegation: bool = False,
    target_service: Optional[str] = None,
):
    """Fire-and-forget background dispatcher for FastAPI endpoints."""
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(report_clearing_event_async(
                operation=operation,
                amount_usdc=amount_usdc,
                caller_agent_id=caller_agent_id,
                chain=chain,
                tx_hash=tx_hash,
                is_a2a_delegation=is_a2a_delegation,
                target_service=target_service,
            ))
    except Exception as e:
        logger.debug(f"Failed to dispatch background clearing event: {e}")

