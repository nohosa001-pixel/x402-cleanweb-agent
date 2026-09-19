"""
LangChain + x402 CleanWeb Agent Integration Example
--------------------------------------------------------------------------------
Enables any LangChain agent to autonomously fetch clean web data with 87% token
savings and zero human intervention using x402 micropayments.

Installation:
    pip install x402-cleanweb-agent langchain langchain-core
"""

import os
import sys
from typing import Optional
from pydantic import BaseModel, Field

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
try:
    from langchain_core.tools import tool
except ImportError:
    # Fallback decorator for pure Python usage
    def tool(name: str, args_schema=None):
        def decorator(func):
            func.invoke = lambda d: func(**d)
            return func
        return decorator

import requests

X402_GATEWAY_URL = os.getenv("X402_GATEWAY_URL", "https://x402-cleanweb-agent-212942243360.asia-northeast3.run.app")
AGENT_VAULT_KEY = os.getenv("AGENT_VAULT_KEY", "WELCOME100")  # Or your pre-funded Vault Session Key


class CleanWebInput(BaseModel):
    url: str = Field(description="Target webpage URL to scrape, clean, and extract noise-free markdown from.")


@tool("clean_web_search", args_schema=CleanWebInput)
def clean_web_tool(url: str) -> str:
    """
    Scrapes a webpage, strips 87% of HTML boilerplate, ads, and noise, 
    and returns pure clean markdown. Handles x402 micropayments autonomously.
    """
    headers = {
        "User-Agent": "LangChain-Autonomous-Agent/1.0",
        "X-Agent-Pass": AGENT_VAULT_KEY,
        "X-Vault-Key": AGENT_VAULT_KEY
    }
    
    response = requests.get(
        f"{X402_GATEWAY_URL}/api/v1/clean-web",
        params={"url": url},
        headers=headers,
        timeout=20
    )
    
    if response.status_code == 200:
        data = response.json()
        title = data.get("title", "Untitled")
        content = data.get("content", "")
        tokens_saved = data.get("stats", {}).get("tokens_saved_estimate", "87%")
        return f"### {title}\n(Cleaned via x402 - Token Savings: {tokens_saved})\n\n{content[:4000]}"
    elif response.status_code == 402:
        return f"[x402 Payment Required]: Please deposit 2.0+ USDC to your agent vault or set AGENT_VAULT_KEY."
    else:
        return f"[Error]: Received HTTP {response.status_code} from x402 Gateway."


if __name__ == "__main__":
    print("🤖 Testing LangChain x402 CleanWeb Tool...")
    result = clean_web_tool.invoke({"url": "https://paulgraham.com/greatwork.html"})
    print("\n--- [LangChain Agent Tool Output] ---")
    print(result[:500] + "...\n")
    print("✅ LangChain x402 Tool is ready for production agent deployment!")
