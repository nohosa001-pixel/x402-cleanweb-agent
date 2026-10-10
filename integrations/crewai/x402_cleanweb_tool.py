"""
CrewAI Official Tool Specification for x402 CleanWeb Agent
--------------------------------------------------------------------------------
Equips CrewAI autonomous agents (Researchers, Writers, Analysts) to fetch
clean, ad-free Markdown with 87% token reduction and autonomous Web3 micropayments.

Complies with CrewAI's BaseTool standard (name, description, args_schema, _run).
"""

from __future__ import annotations

import os
import secrets
import time
from typing import Any, Dict, Optional, Type

import requests
from pydantic import BaseModel, Field

try:
    from crewai.tools import BaseTool
except ImportError:
    try:
        from crewai_tools import BaseTool
    except ImportError:
        # Fallback class adhering to Pydantic BaseModel for local testing
        class BaseTool(BaseModel):  # type: ignore
            name: str = ""
            description: str = ""
            args_schema: Optional[Type[BaseModel]] = None


class X402CleanWebToolInput(BaseModel):
    """Input parameters for the CrewAI x402 CleanWeb tool."""
    url: str = Field(
        ...,
        description="The exact HTTP/HTTPS URL of the target webpage to scrape and convert to 87% token-reduced clean Markdown."
    )


class X402CleanWebTool(BaseTool):
    """
    CrewAI Tool that fetches and converts cluttered HTML pages into clean, 
    ad-free, token-reduced Markdown via the x402 CleanWeb Gateway.
    """
    name: str = "x402_clean_web"
    description: str = (
        "A fast web scraping tool that extracts high-quality, noise-free Markdown from any webpage. "
        "Strips 87% of unnecessary HTML tags, ads, and tracking scripts, drastically saving LLM context. "
        "Useful for web research, reading online documentation, news, and technical blog posts. "
        "Input must be a valid URL string."
    )
    args_schema: Type[BaseModel] = X402CleanWebToolInput

    gateway_url: str = Field(
        default_factory=lambda: os.getenv("X402_GATEWAY_URL", "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app")
    )
    vault_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("AGENT_VAULT_KEY")
    )
    timeout: int = Field(default=25)

    def _build_headers(self) -> Dict[str, str]:
        session_nonce = f"crewai_{secrets.token_hex(4)}_{int(time.time())}"
        headers = {
            "User-Agent": "CrewAI-Tools-x402/1.0",
            "X-Agent-Nonce": session_nonce,
            "Accept": "application/json"
        }
        if self.vault_key:
            headers["X-Agent-Pass"] = self.vault_key
            headers["X-Vault-Key"] = self.vault_key
        return headers

    def _run(self, url: str) -> str:
        """Synchronously execute the web clean request."""
        try:
            headers = self._build_headers()
            response = requests.get(
                f"{self.gateway_url.rstrip('/')}/api/v1/clean-web",
                params={"url": url},
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                title = data.get("title", "Untitled Document")
                content = data.get("clean_markdown") or data.get("markdown_content") or data.get("content", "")
                tokens_saved = data.get("estimated_token_savings") or data.get("token_analytics", {}).get("savings_percentage", "87%")
                
                return (
                    f"### Document: {title}\n"
                    f"*(Cleaned via x402 CleanWeb — Token Reduction: {tokens_saved})*\n\n"
                    f"{content}"
                )
            elif response.status_code == 402:
                challenge = response.json() if response.headers.get("content-type") == "application/json" else {}
                return (
                    f"[x402 Payment Required]: Free trial exhausted. "
                    f"Deposit micro-USDC to /api/v1/vault/deposit or set AGENT_VAULT_KEY. "
                    f"Challenge: {challenge}"
                )
            else:
                return f"[x402 CleanWeb Error]: HTTP {response.status_code} - {response.text[:300]}"

        except requests.exceptions.Timeout:
            return f"[x402 CleanWeb Error]: Request timed out after {self.timeout}s for URL: {url}"
        except Exception as e:
            return f"[x402 CleanWeb Error]: Unexpected exception: {str(e)}"
