"""
Security Gate Agent Client for CleanWeb Studio.
Integrates with agent-security-gate-x402 (The Spend & Execution Firewall)
to inspect scraped web content, YouTube transcripts, and agent inputs for:
  - Prompt Injection & DAN attacks
  - AST Malicious code execution
  - Contradiction / Hallucinations
  - Cryptographic EIP-712 Attestation Proofs
"""

import os
import time
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("security_gate_client")

SECURITY_GATE_URL = os.getenv(
    "SECURITY_GATE_URL",
    "https://agent-security-gate-x402-212942243360.asia-northeast3.run.app"
).rstrip("/")


class SecurityGateClient:
    """Client for performing sub-5ms security and attestation audits on agent data."""

    def __init__(self, base_url: str = SECURITY_GATE_URL, timeout_sec: float = 6.0):
        self.base_url = base_url
        self.timeout_sec = timeout_sec

    def inspect_content(
        self,
        text: str,
        is_code: bool = False,
        agent_nonce: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submits content to Agent Security Gate for AST, prompt-injection, and EIP-712 attestation.
        Returns a structured dictionary with verdict, risk score, threats, and signatures.
        """
        endpoint = f"{self.base_url}/api/v1/inspect"
        headers = {
            "Content-Type": "application/json",
            "X-Agent-Nonce": agent_nonce or f"cw_gate_{int(time.time() * 1000)}"
        }
        payload = {
            "agent_output": text[:100000],  # Cap audit window at 100k chars for latency
            "is_code": is_code
        }

        t0 = time.time()
        try:
            resp = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout_sec
            )
            elapsed_ms = round((time.time() - t0) * 1000, 2)

            if resp.status_code == 200:
                data = resp.json()
                audit = data.get("audit", {})
                attestation = data.get("attestation", {})
                
                return {
                    "enabled": True,
                    "status": "success",
                    "latency_ms": elapsed_ms,
                    "is_safe": audit.get("is_safe", True),
                    "verdict": audit.get("verdict", "PASSED"),
                    "risk_score": audit.get("risk_score", 0.0),
                    "threats": audit.get("threats", []),
                    "attestation": {
                        "issuer": attestation.get("issuer"),
                        "subject_hash": attestation.get("subject_hash"),
                        "signature": attestation.get("signature"),
                        "issued_at": attestation.get("issued_at")
                    },
                    "payment_settled_usdc": data.get("payment_receipt", {}).get("cost_settled_usdc", "0.002")
                }
            else:
                logger.warning(f"Security Gate returned HTTP {resp.status_code}: {resp.text[:120]}")
                return {
                    "enabled": True,
                    "status": "warning",
                    "latency_ms": elapsed_ms,
                    "is_safe": True,
                    "verdict": "PASSED_UNCHECKED",
                    "risk_score": 0.0,
                    "threats": [],
                    "error": f"Gate HTTP {resp.status_code}",
                    "attestation": None
                }

        except Exception as e:
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            logger.error(f"Security Gate audit failed: {e}")
            return {
                "enabled": True,
                "status": "fallback",
                "latency_ms": elapsed_ms,
                "is_safe": True,
                "verdict": "PASSED_FALLBACK",
                "risk_score": 0.0,
                "threats": [],
                "error": str(e),
                "attestation": None
            }


security_gate_client = SecurityGateClient()
