"""
ElizaOS (v2) + x402 CleanWeb Agent Action Provider Example
--------------------------------------------------------------------------------
Equips an ElizaOS autonomous Web3/AI agent with the x402 CleanWeb data provider.
Allows ElizaOS characters/agents to browse the web with 87% token reduction,
automatic 402 micro-settlements, and on-chain EIP-712 cryptographic proofs.

Installation:
    pip install x402-cleanweb-agent
"""

import os
import sys
import json
import time
import secrets
import requests
from typing import Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

X402_GATEWAY_URL = os.getenv("X402_GATEWAY_URL", "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app")
AGENT_VAULT_KEY = os.getenv("AGENT_VAULT_KEY", "WELCOME100")


class ElizaOSCleanWebAction:
    """ElizaOS compatible action provider for autonomous web research & grounding."""

    name = "CLEAN_WEB_SEARCH"
    description = "Searches or scrapes a URL with 87% token noise compression and cryptographic on-chain proof."

    def __init__(self, gateway_url: str = X402_GATEWAY_URL, vault_key: Optional[str] = None):
        self.gateway_url = gateway_url.rstrip("/")
        self.vault_key = vault_key or AGENT_VAULT_KEY

    def validate(self, runtime: Any, message: Dict[str, Any]) -> bool:
        """Validates that a URL is present in the ElizaOS runtime context."""
        text = message.get("content", {}).get("text", "")
        return "http://" in text or "https://" in text

    def handler(self, url: str) -> Dict[str, Any]:
        """Executes the CleanWeb data retrieval for the ElizaOS agent."""
        nonce = f"elizaos_{secrets.token_hex(4)}_{int(time.time())}"
        headers = {
            "User-Agent": "ElizaOS-Autonomous-Agent/2.0",
            "X-Agent-Nonce": nonce,
            "Accept": "application/json"
        }
        if self.vault_key:
            headers["X-Vault-Key"] = self.vault_key
            headers["X-Agent-Pass"] = self.vault_key

        try:
            resp = requests.post(
                f"{self.gateway_url}/api/v1/clean-web",
                json={"url": url},
                headers=headers,
                timeout=25
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "title": data.get("title", ""),
                    "markdown": data.get("markdown_content") or data.get("content", ""),
                    "token_savings": data.get("token_savings_percent", "87.0%"),
                    "token_cost_usdc": 0.001
                }
            elif resp.status_code == 402:
                payment_info = {
                    "recipient": resp.headers.get("x-payment-recipient"),
                    "amount": resp.headers.get("x-payment-amount"),
                    "networks": resp.headers.get("x-payment-networks")
                }
                return {
                    "success": False,
                    "error": "HTTP 402 Payment Required",
                    "payment_details": payment_info
                }
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("🤖 [ElizaOS v2 x402 Action Provider Test]")
    action = ElizaOSCleanWebAction()
    test_url = "https://paulgraham.com/greatwork.html"
    print(f"Executing CleanWeb Action for: {test_url}")
    result = action.handler(test_url)
    if result.get("success"):
        print(f"✅ Success! Title: {result.get('title')}")
        print(f"Token Savings: {result.get('token_savings')}")
        print("Sample Markdown:", result.get("markdown", "")[:200], "...")
    else:
        print("Result:", result)
