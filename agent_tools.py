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

    def clean_web(self, url: str, density: str = "standard", max_tokens: Optional[int] = None) -> str:
        """
        [0.01 USDC] Scrapes any website, strips ads & clutter, and returns clean, LLM-ready Markdown.
        density: 'standard', 'compact', or 'tables_only'
        """
        price = 0.01
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"
        
        res = self.agent_client.clean_web(url, density=density, max_tokens=max_tokens)
        self.budget_guard.record_spend(price, f"clean_web: {url}", res.get("payment", {}).get("tx_hash"))
        
        md = res.get("markdown_content", "")
        savings = res.get("token_analytics", {}).get("token_savings_percentage", "N/A")
        return f"### {res.get('title', 'Web Content')}\n\n{md}\n\n*(Token savings: {savings})*"

    def batch_clean(self, urls: List[str], density: str = "standard", max_tokens_per_url: Optional[int] = None) -> str:
        """
        [0.01 USDC / URL] Scrapes up to 10 URLs in parallel in a single batch transaction.
        """
        total_price = round(len(urls) * 0.01, 4)
        if not self.budget_guard.can_spend(total_price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"
        
        res = self.agent_client.batch_clean(urls, density=density, max_tokens_per_url=max_tokens_per_url)
        self.budget_guard.record_spend(total_price, f"batch_clean ({len(urls)} URLs)", res.get("payment", {}).get("tx_hash"))
        
        out = [f"# 📦 Batch Clean Results ({res.get('successful_count', 0)}/{len(urls)} Success)\n"]
        for item in res.get("results", []):
            if item.get("status") == "success":
                out.append(f"## 🌐 {item.get('title', item.get('url'))}\n> URL: {item.get('url')}\n\n{item.get('markdown_content')}\n---")
            else:
                out.append(f"## ❌ Error: {item.get('url')}\n{item.get('error_message')}\n---")
        return "\n\n".join(out)

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

    def extract_json(self, url: str, schema_description: str, agent_pass: Optional[str] = None) -> str:
        """
        [0.03 USDC / 3 Credits] Extracts structured JSON schema data from any webpage.
        """
        price = 0.03
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"

        res = self.agent_client.extract_json(url, schema_description, agent_pass=agent_pass)
        self.budget_guard.record_spend(price, f"extract_json: {url}")
        return json.dumps(res.get("extracted_json", {}), indent=2, ensure_ascii=False)

    def deep_research(self, query: str, max_sources: int = 3, agent_pass: Optional[str] = None) -> str:
        """
        [0.15 USDC / 15 Credits] Multi-source AI deep research and synthesized executive briefing.
        """
        price = 0.15
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"

        res = self.agent_client.deep_research(query, max_sources=max_sources, agent_pass=agent_pass)
        self.budget_guard.record_spend(price, f"deep_research: {query}")
        return res.get("research_brief_markdown", "No briefing generated.")

    def mint_credit_pass(self, amount_usdc: float = 1.0) -> str:
        """
        [Zero-Latency Pass] Mints a reusable credit pass (1.0 USDC = 100 calls, 5.0 USDC = 600 calls).
        """
        if not self.budget_guard.can_spend(amount_usdc):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"

        token = self.agent_client.mint_credit_pass(amount_usdc=amount_usdc)
        self.budget_guard.record_spend(amount_usdc, f"mint_credit_pass: {amount_usdc} USDC")
        return token

    def get_spending_report(self) -> str:
        """Returns the current spending and budget status for this agent."""
        return json.dumps(self.budget_guard.get_report(), indent=2)

    def get_budget_status(self) -> str:
        """Alias for get_spending_report."""
        return self.get_spending_report()

    def get_tools_list(self) -> List[Callable]:
        """Returns a list of callables for LangChain/CrewAI/Smolagents."""
        return [
            self.clean_web,
            self.batch_clean,
            self.clean_youtube,
            self.clean_pdf,
            self.clean_text,
            self.extract_json,
            self.deep_research,
            self.mint_credit_pass,
            self.get_budget_status
        ]

    def get_openai_function_schemas(self) -> List[Dict[str, Any]]:
        """Returns OpenAI / Anthropic standard Function Calling Tool Schemas."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "x402_clean_web",
                    "description": "Scrapes and converts any website into LLM-ready structured Markdown (0.01 USDC / 1 credit).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Target web page URL"},
                            "density": {"type": "string", "enum": ["standard", "compact", "tables_only"], "description": "Extraction density mode"},
                            "max_tokens": {"type": "integer", "description": "Optional max token limit"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_batch_clean",
                    "description": "Batch cleans up to 10 web URLs in parallel in 1 transaction (0.01 USDC per URL).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "urls": {"type": "array", "items": {"type": "string"}, "description": "List of URLs to clean"},
                            "density": {"type": "string", "enum": ["standard", "compact", "tables_only"]}
                        },
                        "required": ["urls"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_clean_youtube",
                    "description": "Extracts full transcript and video chapters/timestamps from any YouTube video (0.02 USDC / 2 credits).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "YouTube video URL or Video ID"},
                            "language": {"type": "string", "default": "ko,en", "description": "Preferred subtitle languages comma-separated"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_clean_pdf",
                    "description": "Parses online PDF research papers, arXiv docs, and financial filings into clean Markdown (0.05 USDC / 5 credits).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Direct HTTP URL to PDF document"},
                            "max_pages": {"type": "integer", "default": 20, "description": "Max pages to parse"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_clean_text",
                    "description": "Extracts ultra-pure raw text stripped of HTML tags for RAG vector embeddings (0.005 USDC / 1 credit).",
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
                    "name": "x402_extract_json",
                    "description": "Extracts structured key-value JSON matching a schema description from any webpage (0.03 USDC / 3 credits).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Target webpage URL"},
                            "schema_description": {"type": "string", "description": "Description of target data fields"}
                        },
                        "required": ["url", "schema_description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_deep_research",
                    "description": "Generates multi-source AI synthesized deep research briefings on any topic (0.15 USDC / 15 credits).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Research topic or search query"},
                            "max_sources": {"type": "integer", "default": 3}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_mint_credit_pass",
                    "description": "Mints a prepaid zero-latency agent credit pass (1.0 USDC = 100 calls, 5.0 USDC = 600 calls with +20% bonus).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount_usdc": {"type": "number", "default": 1.0, "description": "Deposit amount in USDC"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_get_budget_status",
                    "description": "Retrieves the current agent spending, transaction history, and remaining budget limit.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
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
