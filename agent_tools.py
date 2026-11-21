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

    def clean_web(self, url: str, density: str = "standard", max_tokens: Optional[int] = None, respect_robots_txt: bool = False) -> str:
        """
        [0.001 USDC] Scrapes any website, strips ads & clutter, and returns clean, LLM-ready Markdown.
        density: 'standard', 'compact', or 'tables_only'
        respect_robots_txt: bool to enforce target domain robots.txt Disallow rules.
        """
        price = 0.001
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"
        
        res = self.agent_client.clean_web(url, density=density, max_tokens=max_tokens, respect_robots_txt=respect_robots_txt)
        self.budget_guard.record_spend(price, f"clean_web: {url}", res.get("payment", {}).get("tx_hash"))
        
        md = res.get("markdown_content", "")
        savings = res.get("token_analytics", {}).get("token_savings_percentage", "N/A")
        return f"### {res.get('title', 'Web Content')}\n\n{md}\n\n*(Token savings: {savings})*"

    def batch_clean(self, urls: List[str], density: str = "standard", max_tokens_per_url: Optional[int] = None) -> str:
        """
        [0.005 USDC] Scrapes up to 10 URLs in parallel in a single batch transaction.
        """
        total_price = 0.005
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
        [0.010 USDC] Extracts full video transcript and timestamped segments from YouTube in Markdown with Gemini Flash.
        """
        price = 0.010
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"
        
        res = self.agent_client.clean_youtube(url, language=language)
        self.budget_guard.record_spend(price, f"clean_youtube: {url}", res.get("payment", {}).get("tx_hash"))
        return res.get("markdown_transcript", "")

    def clean_pdf(self, url: str) -> str:
        """
        [0.005 USDC] Extracts research papers (arXiv) and PDF reports into structured Markdown.
        """
        price = 0.005
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"
        
        res = self.agent_client.clean_pdf(url)
        self.budget_guard.record_spend(price, f"clean_pdf: {url}", res.get("payment", {}).get("tx_hash"))
        return res.get("markdown_content", "")

    def clean_text(self, url: str) -> str:
        """
        [0.001 USDC] Ultra-fast raw plain text scraper for vector embeddings and RAG search.
        """
        price = 0.001
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

    def map_site(self, url: str, max_links: int = 50, agent_pass: Optional[str] = None) -> str:
        """
        [0.002 USDC / 2 Credits] Discovers domain sitemap or internal URL tree. Firecrawl /map equivalent.
        """
        price = 0.002
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"

        res = self.agent_client.map_site(url, max_links=max_links, agent_pass=agent_pass)
        self.budget_guard.record_spend(price, f"map_site: {url}")
        return json.dumps({
            "url": res.get("url"),
            "domain": res.get("domain"),
            "total_urls": res.get("total_urls"),
            "sitemap_detected": res.get("sitemap_detected"),
            "urls": res.get("urls", [])
        }, indent=2)

    def search(self, query: str, max_results: int = 5, agent_pass: Optional[str] = None) -> str:
        """
        [0.002 USDC / 2 Credits] Fast real-time agent web search with snippets. Tavily / s.jina.ai equivalent.
        """
        price = 0.002
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"

        res = self.agent_client.search(query, max_results=max_results, agent_pass=agent_pass)
        self.budget_guard.record_spend(price, f"search: {query}")
        return json.dumps({
            "query": res.get("query"),
            "total_results": res.get("total_results"),
            "results": res.get("results", [])
        }, indent=2, ensure_ascii=False)

    def oracle_grounding(
        self,
        query: str,
        target_schema_json: Optional[str] = None,
        max_sources: int = 3,
        secure_audit: bool = False
    ) -> str:
        """
        [0.035 USDC] Real-time web search + Gemini JSON structuring + EIP-712 On-Chain Signed Attestation.
        """
        price = 0.040 if secure_audit else 0.035
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"

        schema_dict = None
        if target_schema_json:
            try:
                schema_dict = json.loads(target_schema_json)
            except Exception:
                schema_dict = None

        res = self.agent_client.oracle_grounding(
            query=query,
            target_schema=schema_dict,
            max_sources=max_sources,
            secure_audit=secure_audit
        )
        self.budget_guard.record_spend(price, f"oracle_grounding: {query}", res.get("payment_receipt", {}).get("tx_hash"))
        
        att = res.get("oracle_attestation", {})
        return (
            f"### 🔮 Oracle Grounding: {res.get('query')}\n\n"
            f"{res.get('summary_markdown', '')}\n\n"
            f"```json\n{json.dumps(res.get('structured_data', {}), indent=2, ensure_ascii=False)}\n```\n\n"
            f"*(EIP-712 Signature: {att.get('signature', 'N/A')})*"
        )

    def verify_oracle_attestation(self, query: str, data_hash: str, timestamp: int, signature: str) -> str:
        """
        [Free / Local] Verifies EIP-712 cryptographic oracle attestation without consuming budget.
        """
        res = self.agent_client.verify_attestation_offline(
            query=query,
            data_hash=data_hash,
            timestamp=timestamp,
            signature=signature
        )
        return json.dumps(res, indent=2)

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

    def get_legal_compliance_info(self) -> str:
        """
        [Free / Compliance] Returns machine-readable B2A terms of service, TDM fair use doctrine, and AS-IS liability disclaimer.
        """
        try:
            terms = self.agent_client.get_legal_terms()
            disclaimer = self.agent_client.get_legal_disclaimer()
            return json.dumps({
                "terms_of_service": terms,
                "legal_disclaimer": disclaimer
            }, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"Failed to retrieve compliance info: {str(e)}"})

    def clean_and_embed(
        self,
        url: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        onchain_proof: bool = False
    ) -> str:
        """
        [0.005 USDC] RAG Dense Vector Embedding Pipeline: Scrapes, noise-reduces, chunks semantically, and generates 768-dim embeddings.
        """
        price = 0.020 if onchain_proof else 0.005
        if not self.budget_guard.can_spend(price):
            return f"[ERROR: Budget limit exceeded ({self.budget_guard.spent_usdc:.4f}/{self.budget_guard.max_daily_budget_usdc} USDC)]"

        res = self.agent_client.clean_and_embed(
            url=url,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            onchain_proof=onchain_proof
        )
        self.budget_guard.record_spend(price, f"clean_and_embed: {url}", res.get("payment_receipt", {}).get("tx_hash"))
        return json.dumps({
            "status": "success",
            "url": res.get("url"),
            "total_chunks": res.get("total_chunks"),
            "dimension": res.get("dimension"),
            "chunks": res.get("chunks", [])[:5]  # first 5 for concise LLM response
        }, indent=2, ensure_ascii=False)

    def get_merkle_root(self) -> str:
        """
        [Free / Audit] Retrieves the latest cryptographic Keccak-256 Merkle root of settled ledger transactions.
        """
        res = self.agent_client.get_merkle_root()
        return json.dumps(res, indent=2)

    def get_merkle_proof(self, tx_hash: str) -> str:
        """
        [Free / Audit] Retrieves cryptographic inclusion audit proof for a transaction hash.
        """
        res = self.agent_client.get_merkle_proof(tx_hash)
        return json.dumps(res, indent=2)

    def get_tools_list(self, include_extended: bool = False) -> List[Callable]:
        """Returns a list of callables for LangChain/CrewAI/Smolagents. Returns 14 standard tools by default or 17 with include_extended=True."""
        base_tools = [
            self.clean_web,
            self.batch_clean,
            self.clean_youtube,
            self.clean_pdf,
            self.clean_text,
            self.map_site,
            self.search,
            self.extract_json,
            self.deep_research,
            self.oracle_grounding,
            self.verify_oracle_attestation,
            self.mint_credit_pass,
            self.get_budget_status,
            self.get_legal_compliance_info
        ]
        if include_extended:
            base_tools.extend([
                self.clean_and_embed,
                self.get_merkle_root,
                self.get_merkle_proof
            ])
        return base_tools

    def get_openai_function_schemas(self, include_extended: bool = False) -> List[Dict[str, Any]]:
        """Returns OpenAI / Anthropic standard Function Calling Tool Schemas."""
        schemas = [
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
                            "max_tokens": {"type": "integer", "description": "Optional max token limit"},
                            "respect_robots_txt": {"type": "boolean", "default": False, "description": "Enforce target domain robots.txt Disallow rules"}
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
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_oracle_grounding",
                    "description": "Performs live web search, extraction, Gemini JSON structuring, and generates EIP-712 on-chain verified attestation (0.035 USDC).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search or research topic to ground"},
                            "target_schema_json": {"type": "string", "description": "Optional JSON string constraining output schema"},
                            "max_sources": {"type": "integer", "default": 3, "description": "Number of sources to synthesize (1 to 5)"},
                            "secure_audit": {"type": "boolean", "default": False, "description": "Run Security Gate audit"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_verify_oracle_attestation",
                    "description": "Verifies an EIP-712 signed Oracle attestation off-chain without gas costs.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Original attested query"},
                            "data_hash": {"type": "string", "description": "SHA-256 data hash of JSON payload"},
                            "timestamp": {"type": "integer", "description": "Unix timestamp of attestation"},
                            "signature": {"type": "string", "description": "65-byte hex signature (0x...)"}
                        },
                        "required": ["query", "data_hash", "timestamp", "signature"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_map_site",
                    "description": "Discovers domain sitemap or internal URL tree of any website (0.002 USDC). Firecrawl /map equivalent.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Target website domain or URL to map"},
                            "max_links": {"type": "integer", "default": 50, "description": "Max URLs to discover (5 to 100)"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_search",
                    "description": "Fast real-time keyword web search returning verified URLs and snippets (0.002 USDC). Tavily equivalent.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Keyword or question to search"},
                            "max_results": {"type": "integer", "default": 5, "description": "Max search results (1 to 10)"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "x402_get_legal_compliance_info",
                    "description": "Returns machine-readable terms of service, TDM fair use doctrine, and liability disclaimer (Free).",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]
        if include_extended:
            schemas.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "x402_clean_embed",
                        "description": "RAG one-stop dense vector embedding pipeline: Scrapes, noise-reduces, chunks semantically, and generates 768-dim embeddings (0.005 USDC).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string", "description": "Target web page URL"},
                                "chunk_size": {"type": "integer", "default": 500, "description": "Max character length per chunk"},
                                "chunk_overlap": {"type": "integer", "default": 50, "description": "Overlap between consecutive chunks"}
                            },
                            "required": ["url"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "x402_treasury_merkle_proof",
                        "description": "Retrieves cryptographic Keccak-256 inclusion audit proof for a settled transaction hash (Free).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "tx_hash": {"type": "string", "description": "Settled transaction hash to audit"}
                            },
                            "required": ["tx_hash"]
                        }
                    }
                }
            ])
        return schemas


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
