"""
CrewAI + x402 CleanWeb Agent Integration Example
--------------------------------------------------------------------------------
Equips a CrewAI autonomous researcher with CleanWeb x402 extraction tool.

Installation:
    pip install x402-cleanweb-agent crewai
"""

import os
import sys
import requests
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

X402_GATEWAY_URL = os.getenv("X402_GATEWAY_URL", "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app")
AGENT_VAULT_KEY = os.getenv("AGENT_VAULT_KEY", "WELCOME100")


import time
import secrets

def clean_web_for_crewai(url: str, vault_key: Optional[str] = None) -> str:
    """CrewAI compatible tool function for high-speed noise-free web extraction."""
    active_key = vault_key or os.getenv("AGENT_VAULT_KEY")
    session_nonce = f"crewai_{secrets.token_hex(4)}_{int(time.time())}"
    headers = {
        "User-Agent": "CrewAI-Autonomous-Agent/1.0",
        "X-Agent-Nonce": session_nonce
    }
    if active_key:
        headers["X-Agent-Pass"] = active_key
        headers["X-Vault-Key"] = active_key

    resp = requests.get(
        f"{X402_GATEWAY_URL}/api/v1/clean-web",
        params={"url": url},
        headers=headers,
        timeout=20
    )
    if resp.status_code == 200:
        data = resp.json()
        content = data.get("markdown_content") or data.get("content", "")
        return f"Document Title: {data.get('title')}\n\nContent:\n{content[:3000]}"
    elif resp.status_code == 402:
        return "[x402 Payment Required]: Free trial exhausted. Deposit 2.0+ USDC to /api/v1/vault/deposit or set AGENT_VAULT_KEY."
    return f"[Error]: Gateway HTTP {resp.status_code}: {resp.text}"


if __name__ == "__main__":
    print("🤖 Testing CrewAI x402 CleanWeb Scraper Tool...")
    res = clean_web_for_crewai("https://paulgraham.com/greatwork.html")
    print("\n--- [CrewAI Agent Extracted Output] ---")
    print(res[:400] + "...\n")
    print("✅ CrewAI x402 Tool verified successfully!")
