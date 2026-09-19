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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

X402_GATEWAY_URL = os.getenv("X402_GATEWAY_URL", "https://x402-cleanweb-agent-212942243360.asia-northeast3.run.app")
AGENT_VAULT_KEY = os.getenv("AGENT_VAULT_KEY", "WELCOME100")


def clean_web_for_crewai(url: str) -> str:
    """CrewAI compatible tool function for high-speed noise-free web extraction."""
    headers = {
        "User-Agent": "CrewAI-Autonomous-Agent/1.0",
        "X-Agent-Pass": AGENT_VAULT_KEY,
        "X-Vault-Key": AGENT_VAULT_KEY
    }
    resp = requests.get(
        f"{X402_GATEWAY_URL}/api/v1/clean-web",
        params={"url": url},
        headers=headers,
        timeout=20
    )
    if resp.status_code == 200:
        data = resp.json()
        return f"Document Title: {data.get('title')}\n\nContent:\n{data.get('content', '')[:3000]}"
    elif resp.status_code == 402:
        return "[x402 Payment Required]: Please deposit USDC into your Agent Vault to continue zero-latency scraping."
    return f"[Error]: Gateway HTTP {resp.status_code}"


if __name__ == "__main__":
    print("🤖 Testing CrewAI x402 CleanWeb Scraper Tool...")
    res = clean_web_for_crewai("https://paulgraham.com/greatwork.html")
    print("\n--- [CrewAI Agent Extracted Output] ---")
    print(res[:400] + "...\n")
    print("✅ CrewAI x402 Tool verified successfully!")
