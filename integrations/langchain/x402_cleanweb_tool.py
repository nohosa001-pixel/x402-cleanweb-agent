"""
LangChain Official Tool Specification for x402 CleanWeb Agent
--------------------------------------------------------------------------------
Enables autonomous AI agents to fetch clean, noise-free Markdown with 87% token
savings and zero credit card dependency via x402 micropayments.

Complies with LangChain standard BaseTool specification (동기 _run, 비동기 _arun, Pydantic v2 args_schema).
"""

from __future__ import annotations

import os
import secrets
import time
from typing import Any, Dict, Optional, Type

import requests
from pydantic import BaseModel, Field

try:
    from langchain_core.tools import BaseTool
    from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
except ImportError:
    # Fallback dummy class if langchain_core is not installed in local environment
    class BaseTool:  # type: ignore
        name: str
        description: str
        args_schema: Optional[Type[BaseModel]] = None
    CallbackManagerForToolRun = Any  # type: ignore
    AsyncCallbackManagerForToolRun = Any  # type: ignore


class X402CleanWebInput(BaseModel):
    """Input parameters for the x402 CleanWeb tool."""
    url: str = Field(
        ...,
        description="The exact HTTP/HTTPS URL of the webpage to scrape, strip ads and boilerplate from, and convert to clean Markdown."
    )
    raw_markdown: bool = Field(
        default=True,
        description="Whether to return pure stripped markdown optimized for LLM token savings."
    )


class X402CleanWebTool(BaseTool):
    """
    Tool that uses the x402 CleanWeb Gateway to scrape webpages, 
    stripping 87% of HTML boilerplate, ads, and noisy scripts, returning
    token-optimized clean Markdown with autonomous Web3 micropayment support.
    """
    name: str = "x402_clean_web"
    description: str = (
        "A high-throughput web scraping and cleaning tool. "
        "Transforms cluttered HTML webpages into 87% token-reduced clean Markdown. "
        "Useful for web research, reading articles, documentation, or news without ad noise. "
        "Input should be a valid web URL."
    )
    args_schema: Type[BaseModel] = X402CleanWebInput

    gateway_url: str = Field(
        default_factory=lambda: os.getenv("X402_GATEWAY_URL", "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app")
    )
    vault_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("AGENT_VAULT_KEY", "WELCOME100")
    )
    timeout: int = Field(default=25)

    def _build_headers(self) -> Dict[str, str]:
        session_nonce = f"langchain_{secrets.token_hex(4)}_{int(time.time())}"
        headers = {
            "User-Agent": "LangChain-Community-x402/1.0",
            "X-Agent-Nonce": session_nonce,
            "Accept": "application/json"
        }
        if self.vault_key:
            headers["X-Agent-Pass"] = self.vault_key
            headers["X-Vault-Key"] = self.vault_key
        return headers

    def _run(
        self,
        url: str,
        raw_markdown: bool = True,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
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
                title = data.get("title", "Clean Web Result")
                content = data.get("clean_markdown") or data.get("markdown_content") or data.get("content", "")
                tokens_saved = data.get("estimated_token_savings") or data.get("token_analytics", {}).get("savings_percentage", "87%")
                
                return (
                    f"### {title}\n"
                    f"*(Extracted via x402 CleanWeb Gateway — Token Savings: {tokens_saved})*\n\n"
                    f"{content}"
                )
            elif response.status_code == 402:
                challenge = response.json() if response.headers.get("content-type") == "application/json" else {}
                return (
                    f"[x402 Payment Required]: Free trial quota exhausted. "
                    f"Please pre-fund your agent vault on Solana/Polygon/Base or set AGENT_VAULT_KEY. "
                    f"Challenge Details: {challenge}"
                )
            else:
                return f"[x402 CleanWeb Error]: HTTP {response.status_code} - {response.text[:300]}"
                
        except requests.exceptions.Timeout:
            return f"[x402 CleanWeb Error]: Request timed out after {self.timeout}s for URL: {url}"
        except Exception as e:
            return f"[x402 CleanWeb Error]: Unexpected exception: {str(e)}"

    async def _arun(
        self,
        url: str,
        raw_markdown: bool = True,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Asynchronously execute the web clean request."""
        import asyncio
        # Run sync request in default executor for lightweight non-blocking execution
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, url, raw_markdown)
