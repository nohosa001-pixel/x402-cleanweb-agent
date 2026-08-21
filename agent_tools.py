"""
AI Agent Standard Tool Suite for x402 Micropayment Protocol
--------------------------------------------------------------------------------
Provides ready-to-use tool wrappers for LangChain, CrewAI, LlamaIndex, smolagents,
and custom autonomous AI agents with built-in Budget Guard protection.
"""

import os
import json
import time
from typing import Dict, Any, Optional, List, Callable
from autonomous_agent_client import AutonomousX402Agent, DEFAULT_BASE_URL

class BudgetGuard:
    """
    Prevents autonomous AI agents from overspending USDC in loops or errors.
    """
    def __init__(self, max_daily_budget_usdc: float = 1.0):
        self.max_daily_budget_usdc = max_daily_budget_usdc
        self.spent_usdc: float = 0.0
        self.history: List[Dict[str, Any]] = []
        self.created_at = time.time()

    def can_spend(self, amount: float) -> bool:
        return (self.spent_usdc + amount) <= self.max_daily_budget_usdc

    def record_spend(self, amount: float, purpose: str, tx_hash: Optional[str] = None):
        if not self.can_spend(amount):
            raise PermissionError(
                f"[BUDGET GUARD EXCEEDED] Cannot spend {amount} USDC. "
                f"Already spent: {self.spent_usdc:.4f} USDC / Daily Limit: {self.max_daily_budget_usdc:.4f} USDC"
            )
        self.spent_usdc += amount
        self.history.append({
            "timestamp": time.time(),
            "amount_usdc": amount,
            "purpose": purpose,
            "tx_hash": tx_hash,
            "total_spent_so_far": self.spent_usdc
        })

    def get_report(self) -> Dict[str, Any]:
        return {
            "daily_budget_limit_usdc": self.max_daily_budget_usdc,
            "total_spent_usdc": round(self.spent_usdc, 4),
            "remaining_budget_usdc": round(max(0.0, self.max_daily_budget_usdc - self.spent_usdc), 4),
            "transaction_count": len(self.history),
            "history": self.history
        }


class X402AgentToolkit:
    """
    Toolkit for Autonomous AI Agents with Budget Guard.
    """
    def __init__(
        self,
        private_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        max_daily_budget_usdc: float = 1.0
    ):
        self.agent_client = AutonomousX402Agent(private_key=private_key, base_url=base_url)
        self.budget_guard = BudgetGuard(max_daily_budget_usdc=max_daily_budget_usdc)

    def clean_web(self, url: str) -> str:
        """
        [0.01 USDC] Scrapes any website, strips ads & clutter, and returns clean, LLM-ready Markdown.
        """
        price = 0.01
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"
        
        res = self.agent_client.clean_web(url)
        self.budget_guard.record_spend(price, f"clean_web: {url}", res.get("payment", {}).get("tx_hash"))
        
        md = res.get("markdown_content", "")
        savings = res.get("token_analytics", {}).get("token_savings_percentage", "N/A")
        return f"### {res.get('title', 'Web Content')}\n\n{md}\n\n*(Token savings: {savings})*"

    def clean_youtube(self, url: str, language: str = "ko,en") -> str:
        """
        [0.02 USDC] Extracts full video transcript and timestamped segments from YouTube in Markdown.
        """
        price = 0.02
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"
        
        res = self.agent_client.clean_youtube(url, language=language)
        self.budget_guard.record_spend(price, f"clean_youtube: {url}", res.get("payment", {}).get("tx_hash"))
        return res.get("markdown_transcript", "")

    def clean_pdf(self, url: str) -> str:
        """
        [0.05 USDC] Extracts research papers (arXiv) and PDF reports into structured Markdown.
        """
        price = 0.05
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"
        
        res = self.agent_client.clean_pdf(url)
        self.budget_guard.record_spend(price, f"clean_pdf: {url}", res.get("payment", {}).get("tx_hash"))
        return res.get("markdown_content", "")

    def clean_text(self, url: str) -> str:
        """
        [0.005 USDC] Ultra-fast raw plain text scraper for vector embeddings and RAG search.
        """
        price = 0.005
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"
        
        res = self.agent_client.clean_text(url)
        self.budget_guard.record_spend(price, f"clean_text: {url}", res.get("payment", {}).get("tx_hash"))
        return res.get("plain_text", "")

    def get_spending_report(self) -> str:
        """Returns the current spending and budget status for this agent."""
        return json.dumps(self.budget_guard.get_report(), indent=2)

    def get_tools_list(self) -> List[Callable]:
        """Returns standard Python callable tools (compatible with smolagents, CrewAI, AutoGen)."""
        return [
            self.clean_web,
            self.clean_youtube,
            self.clean_pdf,
            self.clean_text,
            self.get_spending_report
        ]

    def get_openai_function_schemas(self) -> List[Dict[str, Any]]:
        """Returns OpenAI / Anthropic standard Function Calling Tool Schemas."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "x402_clean_web",
                    "description": "Scrapes and converts any website into LLM-ready structured Markdown (0.01 USDC on Polygon).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Target web page URL"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_clean_youtube",
                    "description": "Extracts complete transcript with timestamps from any YouTube video (0.02 USDC on Polygon).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "YouTube video URL"},
                            "language": {"type": "string", "description": "Comma separated languages (default: 'ko,en')"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_clean_pdf",
                    "description": "Extracts structured Markdown from PDF research papers (arXiv) and reports (0.05 USDC on Polygon).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Direct PDF URL"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_clean_text",
                    "description": "Extracts lightweight raw plain text for vector search (0.005 USDC on Polygon).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Target URL"}
                        },
                        "required": ["url"]
                    }
                }
            }
        ]


def get_x402_agent_tools(
    private_key: Optional[str] = None,
    max_daily_budget_usdc: float = 1.0,
    base_url: str = DEFAULT_BASE_URL
) -> List[Callable]:
    """
    Factory function: Returns a list of callable tools for autonomous AI agents.
    
    Usage:
        from agent_tools import get_x402_agent_tools
        tools = get_x402_agent_tools(private_key="0x...", max_daily_budget_usdc=2.0)
    """
    toolkit = X402AgentToolkit(
        private_key=private_key,
        base_url=base_url,
        max_daily_budget_usdc=max_daily_budget_usdc
    )
    return toolkit.get_tools_list()
