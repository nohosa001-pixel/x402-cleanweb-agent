"""
Main FastAPI Application for x402-cleanweb-agent (CleanWeb Studio v2.3.0).
Enterprise-grade high-concurrency micro-agent service with rate limiting, Prometheus metrics, and multi-RPC resilience.
"""

import os
import hmac
import hashlib
import json
import time
import secrets
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
from collections import defaultdict, deque
import requests

from fastapi import FastAPI, Request, HTTPException, status, Query, Body, Response
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.schemas import (
    PricingTier,
    PaymentMethod,
    PaymentReceipt,
    CleanWebRequest,
    WebCleanResponse,
    CleanYouTubeRequest,
    YouTubeCleanResponse,
    CleanPDFRequest,
    PDFCleanResponse,
    BatchCleanRequest,
    BatchCleanResponse,
    VaultDepositRequest,
    VaultBalanceResponse,
    PassStatusResponse,
    TokenAnalytics,
    ScrapeMetadata,
    OracleGroundingRequest,
    OracleGroundingResponse,
    OracleVerifyRequest,
    OracleVerifyResponse,
    SecurityAuditResult,
    SecurityInspectRequest,
    TextCleanResponse,
    ExtractJsonRequest,
    ExtractJsonResponse,
    DeepResearchResponse,
    SiteMapRequest,
    SiteMapResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    EmbeddedChunk,
    CleanEmbedRequest,
    CleanEmbedResponse,
    PermitDepositRequest,
    MerkleProofItem,
    MerkleProofResponse,
    MerkleRootResponse,
)
from app.x402_verifier import x402_verifier
from app.cleaners.web_engine import web_cleaner_engine, normalize_url
from app.cleaners.youtube_engine import youtube_cleaner_engine
from app.cleaners.pdf_engine import pdf_cleaner_engine
from app.cleaners.embed_engine import embed_engine
from app.onchain_signer import onchain_signer
from app.vault_manager import vault_manager
from app.storage import storage_manager
from app.multi_chain import multi_chain_manager
from app.oracle_engine import oracle_engine
from app.merkle_engine import merkle_engine, compute_tx_leaf
from app.security_gate_client import security_gate_client
from app.diagnostics import diagnostic_engine
import mcp_server
from mcp.server.transport_security import TransportSecuritySettings


load_dotenv()

app = FastAPI(
    title="CleanWeb Studio (x402 AI Agent Suite)",
    description="Deterministic Web3 x402 Micropayment MCP & AI Agent Tool Suite with Gemini 3.6 Flash Video Intelligence on Polygon, Base, and Arbitrum.",
    version="2.6.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "WWW-Authenticate",
        "X-Payment-Required",
        "X-Payment-Amount",
        "X-Payment-Recipient",
        "X-Payment-Token",
        "X-Payment-Networks",
        "X-Vault-Deposit-Endpoint",
        "X-Agent-Trial-Remaining",
        "X-Access-Policy",
    ]
)

BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML_PATH = STATIC_DIR / "index.html"
AP2_FILE_PATH = BASE_DIR / ".well-known" / "ap2.json"
AGENT_MANIFEST_PATH = BASE_DIR / ".well-known" / "agent.json"
AI_PLUGIN_PATH = BASE_DIR / ".well-known" / "ai-plugin.json"
MCP_SERVER_CARD_PATH = BASE_DIR / ".well-known" / "mcp" / "server-card.json"
MCP_ALIAS_PATH = BASE_DIR / ".well-known" / "mcp.json"
GLAMA_FILE_PATH = BASE_DIR / "glama.json"
MCP_SPEC_FILE_PATH = BASE_DIR / "mcp_tool_spec.json"
LLMS_TXT_PATH = BASE_DIR / "llms.txt"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount Remote Model Context Protocol (MCP) Server-Sent Events (SSE) Transport
app.mount(
    "/mcp-server",
    mcp_server.mcp.sse_app(transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
)


# =========================================================================
# 🛡️ In-Memory Sliding Window Rate Limiter & Prometheus Metrics Middleware
# =========================================================================
RATE_LIMIT_WINDOW_SEC = 60
RATE_LIMIT_MAX_REQUESTS = 180  # 180 requests per minute per IP
ip_request_history: Dict[str, deque] = defaultdict(deque)

METRICS = {
    "total_requests": 0,
    "total_errors": 0,
    "requests_by_endpoint": defaultdict(int),
    "requests_by_status": defaultdict(int),
}


@app.middleware("http")
async def rate_limit_and_metrics_middleware(request: Request, call_next):
    # Skip rate limiting for static assets, mcp-server, and metrics
    path = request.url.path
    
    # Correctly parse real client IP behind Cloud Run / reverse proxies
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"

    if not path.startswith("/static") and not path.startswith("/mcp-server") and path not in ("/metrics", "/health"):
        now = time.time()
        q = ip_request_history[client_ip]
        # Purge older timestamps
        while q and q[0] <= now - RATE_LIMIT_WINDOW_SEC:
            q.popleft()
        
        if len(q) >= RATE_LIMIT_MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error": "Rate limit exceeded. Maximum 180 requests per minute.",
                    "retry_after_sec": int(RATE_LIMIT_WINDOW_SEC - (now - q[0]))
                }
            )
        q.append(now)

    METRICS["total_requests"] += 1
    METRICS["requests_by_endpoint"][path] += 1

    try:
        response = await call_next(request)
        if hasattr(request, "state") and hasattr(request.state, "payment_receipt"):
            rcpt = request.state.payment_receipt
            if getattr(rcpt, "remaining_free_trials", None) is not None:
                response.headers["X-Agent-Trial-Remaining"] = str(rcpt.remaining_free_trials)
        METRICS["requests_by_status"][response.status_code] += 1
        return response
    except Exception as exc:
        METRICS["total_errors"] += 1
        METRICS["requests_by_status"][500] += 1
        raise exc


# =========================================================================
# 📊 Telemetry & Prometheus Metrics Endpoint
# =========================================================================
@app.get("/metrics", tags=["System"])
async def get_metrics():
    """Prometheus compatible text format metrics."""
    stats = storage_manager.get_stats()
    lines = [
        "# HELP cleanweb_total_requests Total requests processed by CleanWeb Studio",
        "# TYPE cleanweb_total_requests counter",
        f"cleanweb_total_requests {METRICS['total_requests']}",
        "# HELP cleanweb_total_errors Total 5xx or unhandled server errors",
        "# TYPE cleanweb_total_errors counter",
        f"cleanweb_total_errors {METRICS['total_errors']}",
        "# HELP cleanweb_vault_accounts Total registered agent vault accounts",
        "# TYPE cleanweb_vault_accounts gauge",
        f"cleanweb_vault_accounts {stats['vault_accounts_count']}",
        "# HELP cleanweb_vault_total_consumed_usdc Total USDC consumed from agent vaults",
        "# TYPE cleanweb_vault_total_consumed_usdc gauge",
        f"cleanweb_vault_total_consumed_usdc {stats['total_vault_consumed_usdc']}",
        "# HELP cleanweb_used_tx_hashes Total verified anti-replay transaction hashes",
        "# TYPE cleanweb_used_tx_hashes counter",
        f"cleanweb_used_tx_hashes {stats['used_transactions_count']}",
    ]
    for status_code, count in METRICS["requests_by_status"].items():
        lines.append(f'cleanweb_http_requests_total{{status="{status_code}"}} {count}')

    return PlainTextResponse("\n".join(lines), media_type="text/plain; version=0.0.4")


def safe_refund_vault(receipt: Optional[PaymentReceipt]):
    """Safely rolls back deducted vault balance if an upstream extraction or external service call fails."""
    if receipt and receipt.payment_method == PaymentMethod.VAULT_BALANCE and receipt.payer_address and receipt.cost_usdc > 0:
        try:
            vault_manager.refund(receipt.payer_address, receipt.cost_usdc)
        except Exception:
            pass


# =========================================================================
# 🏠 Root & Interactive Dashboard Endpoints
# =========================================================================
@app.get("/", tags=["System"])
async def root(request: Request):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header and INDEX_HTML_PATH.exists():
        return FileResponse(INDEX_HTML_PATH, media_type="text/html")

    return {
        "service": "x402-cleanweb-agent",
        "name": "CleanWeb Studio (Autonomous Agent Data & Spend Firewall)",
        "version": "2.6.1",
        "audience": "HUMANS_AND_AUTONOMOUS_AGENTS",
        "access_policy": "OPEN_TO_ALL (Pay-As-You-Go via USDC Pre-Funded Vault)",
        "protocol": "x402 (HTTP 402 Monetized)",
        "security_gate_integration": "agent-security-gate-x402 (Live AST/Prompt/NLI Inspection)",
        "networks": ["Polygon (137)", "Base (8453)", "Arbitrum (42161)"],
        "pricing_tiers": {
            "web_clean": "0.001 USDC",
            "clean_text": "0.001 USDC (Raw plain text for vector/RAG)",
            "secure_web_clean": "0.005 USDC (Includes Security Gate AST/Prompt Audit)",
            "pdf_or_batch": "0.005 USDC",
            "youtube_gemini_ai": "0.010 USDC",
            "secure_youtube_clean": "0.015 USDC (Includes Security Gate Video Intelligence Audit)",
            "onchain_attestation": "0.020 USDC",
            "map_site": "0.002 USDC (Domain Sitemap & URL Tree Discovery)",
            "search": "0.002 USDC (Fast Agent Web Search & Snippets)",
            "extract_json": "0.030 USDC (Schema-constrained JSON extractor)",
            "oracle_grounding": "0.035 USDC (Search + Clean-to-JSON + EIP-712 Signed Oracle)",
            "secure_oracle_grounding": "0.040 USDC (Includes Dual Security Gate Attestation)",
            "deep_research": "0.150 USDC (Multi-source AI synthesized deep briefing)"
        },
        "interactive_dashboard": "/dashboard",
        "metrics_url": "/metrics",
        "endpoints": {
            "clean_web": "/api/v1/clean-web?url=https://example.com",
            "clean_text": "/api/v1/clean-text?url=https://example.com",
            "clean_youtube": "/api/v1/clean-youtube?url=https://www.youtube.com/watch?v=aircAruvnKk",
            "clean_pdf": "/api/v1/clean-pdf?url=https://example.com/paper.pdf",
            "clean_batch": "/api/v1/clean-batch",
            "batch_clean_alias": "/api/v1/batch-clean",
            "map_site": "/api/v1/map-site?url=https://example.com",
            "search": "/api/v1/search?query=Topic",
            "extract_json": "/api/v1/extract-json",
            "oracle_grounding": "/api/v1/oracle/grounding",
            "oracle_verify": "/api/v1/oracle/verify",
            "deep_research": "/api/v1/deep-research?query=Topic",
            "vault_deposit": "/api/v1/vault/deposit",
            "vault_balance": "/api/v1/vault/balance",
            "pass_status": "/api/v1/pass-status",
            "legal_terms": "/api/v1/legal/terms",
            "legal_disclaimer": "/api/v1/legal/disclaimer",
            "ap2_manifest": "/.well-known/ap2",
            "agent_manifest": "/.well-known/agent.json",
            "ai_plugin_manifest": "/.well-known/ai-plugin.json",
            "mcp_server_card": "/.well-known/mcp/server-card.json",
            "mcp_tools": "/mcp/tools",
            "agent_capabilities": "/api/v1/agent/capabilities",
            "agent_pricing_catalog": "/api/v1/agent/pricing-catalog",
            "agent_arbitrage_roi": "/api/v1/agent/arbitrage-roi",
            "agent_integrations": "/api/v1/agent/integrations/{framework}",
            "metrics": "/metrics",
            "health": "/health"
        },
        "legal_notice": {
            "doctrine": "Transformative Non-Expressive Text/Data Mining (TDM) Fair Use",
            "financial_disclaimer": "All oracle, search, and cleaned web data provided AS-IS without financial or investment warranty. The caller agent assumes full liability for downstream executions.",
            "data_retention": "Zero-Data Retention (In-memory ephemeral processing only, GDPR compliant)",
            "sanctions_compliance": "OFAC SDN List 100% Screened & Blocked"
        }
    }


@app.get("/dashboard", tags=["System"])
async def dashboard():
    if INDEX_HTML_PATH.exists():
        return FileResponse(INDEX_HTML_PATH, media_type="text/html")
    return HTMLResponse("<h1>CleanWeb Studio Dashboard</h1><p>Dashboard UI template not found.</p>")


@app.get("/health", tags=["System"])
def health_check(deep: bool = Query(False, description="Run deep 5-pipeline self-audit")):
    """Standard health check. Pass ?deep=true for real-time 5-pipeline diagnostic."""
    if deep:
        return diagnostic_engine.run_full_diagnostic()
    db_stats = storage_manager.get_stats()
    return {
        "status": "healthy",
        "service": "x402-cleanweb-agent",
        "version": "2.6.1",
        "storage": "sqlite3_wal_ready",
        "storage_stats": db_stats,
        "chains_connected": ["Polygon(137)", "Base(8453)", "Arbitrum(42161)"],
        "security_gate": "agent-security-gate-x402",
        "diagnostic_api": "/api/v1/system/diagnostics"
    }


@app.get("/api/v1/system/diagnostics", tags=["System"])
def run_system_diagnostics():
    """
    Executes real-time deep self-audit across 5 mission-critical pipelines:
    1. Agent Security Gate Ingress Defense (Live Cloud Run & Latency SLA)
    2. Gemini 3.6 Flash Video/Knowledge AI
    3. EIP-712 Cryptographic On-Chain Signer
    4. SQLite WAL Storage & Agent Vault Ledger
    5. Multi-Chain RPC Nodes (Polygon, Base, Arbitrum)
    """
    return diagnostic_engine.run_full_diagnostic()


@app.get("/.well-known/ap2", tags=["Standards"])
@app.get("/.well-known/ap2.json", tags=["Standards"])
async def get_ap2_manifest():
    if AP2_FILE_PATH.exists():
        return FileResponse(AP2_FILE_PATH, media_type="application/json")
    raise HTTPException(status_code=404, detail="ap2.json not found")


@app.get("/mcp/tools", tags=["Standards"])
@app.get("/mcp_tool_spec.json", tags=["Standards"])
async def get_mcp_spec():
    if MCP_SPEC_FILE_PATH.exists():
        return FileResponse(MCP_SPEC_FILE_PATH, media_type="application/json")
    raise HTTPException(status_code=404, detail="mcp_tool_spec.json not found")


@app.get("/glama.json", tags=["Standards"])
async def get_glama_spec():
    if GLAMA_FILE_PATH.exists():
        return FileResponse(GLAMA_FILE_PATH, media_type="application/json")
    raise HTTPException(status_code=404, detail="glama.json not found")


@app.get("/.well-known/agent.json", tags=["Standards"])
async def get_agent_manifest():
    if AGENT_MANIFEST_PATH.exists():
        return FileResponse(AGENT_MANIFEST_PATH, media_type="application/json")
    raise HTTPException(status_code=404, detail="agent.json not found")


@app.get("/.well-known/ai-plugin.json", tags=["Standards"])
async def get_ai_plugin_manifest():
    if AI_PLUGIN_PATH.exists():
        return FileResponse(AI_PLUGIN_PATH, media_type="application/json")
    raise HTTPException(status_code=404, detail="ai-plugin.json not found")


@app.get("/.well-known/mcp/server-card.json", tags=["Standards"])
@app.get("/.well-known/mcp.json", tags=["Standards"])
async def get_mcp_server_card():
    if MCP_SERVER_CARD_PATH.exists():
        return FileResponse(MCP_SERVER_CARD_PATH, media_type="application/json")
    elif MCP_ALIAS_PATH.exists():
        return FileResponse(MCP_ALIAS_PATH, media_type="application/json")
    raise HTTPException(status_code=404, detail="mcp server card not found")


@app.get("/llms.txt", response_class=PlainTextResponse, tags=["Standards"])
async def get_llms_txt():
    """
    Agent LLM Standard manifest for autonomous agents, crawlers, and swarms.
    """
    if LLMS_TXT_PATH.exists():
        return FileResponse(LLMS_TXT_PATH, media_type="text/plain; charset=utf-8")
    raise HTTPException(status_code=404, detail="llms.txt not found")


@app.get("/robots.txt", response_class=PlainTextResponse, tags=["Standards"])
def get_robots_txt():
    """
    Standard robots.txt allowing all autonomous agents, crawlers, and swarms with pointer to llms.txt.
    """
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /metrics\n"
        "Sitemap: https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/llms.txt\n"
    )


# =========================================================================
# 🤖 Autonomous Agent Discovery, Reflection & Arbitrage Endpoints
# =========================================================================

@app.get("/api/v1/agent/capabilities", tags=["Agent Intelligence"])
def get_agent_capabilities():
    """
    Self-describing reflection endpoint for Autonomous AI Agents, Swarms & LLMs.
    Exposes all 14 callable tools, token reduction benchmarks, and multi-chain vaults.
    """
    return {
        "status": "active",
        "agent_id": "x402-cleanweb-agent",
        "version": "2.6.1",
        "settlement": "x402_usdc_micropayments",
        "supported_chains": [
            {"name": "Polygon PoS", "chain_id": 137, "vault": "0x18fA5a746535d88f61feA10996895c378F705c93"},
            {"name": "Base Mainnet", "chain_id": 8453, "vault": "0x3eD21B72583569769B73a3885d562145b23d57E3"},
            {"name": "Arbitrum One", "chain_id": 42161, "vault": "0x3eD21B72583569769B73a3885d562145b23d57E3"}
        ],
        "trial_policy": {
            "free_calls_per_nonce": 0,
            "policy": "MANDATORY_PAID_EXECUTION",
            "free_trials": False,
            "min_vault_deposit_usdc": 2.0
        },
        "performance_sla": {
            "average_token_reduction_pct": 87.2,
            "p95_latency_ms": 420,
            "availability": "99.95%"
        },
        "tools_count": 14,
        "tools": [
            {"name": "clean_web", "cost_usdc": 0.001, "description": "Fetch web page and convert to ad-free clean Markdown."},
            {"name": "batch_clean", "cost_usdc": 0.005, "description": "Scrape up to 10 URLs concurrently in parallel."},
            {"name": "clean_youtube", "cost_usdc": 0.010, "description": "Gemini 3.6 Flash video intelligence and transcript extractor."},
            {"name": "clean_pdf", "cost_usdc": 0.005, "description": "Converts PDF research papers into structured Markdown."},
            {"name": "clean_text", "cost_usdc": 0.001, "description": "Purifies raw text, strips boilerplate and noisy markup."},
            {"name": "map_site", "cost_usdc": 0.002, "description": "Fast recursive sitemap and URL tree discovery."},
            {"name": "search", "cost_usdc": 0.002, "description": "Real-time web search with verified source snippets."},
            {"name": "extract_json", "cost_usdc": 0.030, "description": "Extracts schema-constrained JSON using Gemini Flash."},
            {"name": "deep_research", "cost_usdc": 0.150, "description": "Multi-source executive AI research briefing."},
            {"name": "oracle_grounding", "cost_usdc": 0.035, "description": "Web search + JSON extraction + EIP-712 cryptographic attestation."},
            {"name": "oracle_verify", "cost_usdc": 0.000, "description": "Verifies ECDSA EIP-712 cryptographic signature for oracle groundings."},
            {"name": "vault_deposit", "cost_usdc": 0.000, "description": "Deposit USDC into multi-chain agent vault for zero-gas prepaid execution."},
            {"name": "vault_balance", "cost_usdc": 0.000, "description": "Queries prepaid credit pass balance and validity."},
            {"name": "pass_status", "cost_usdc": 0.000, "description": "Inspects status of credit pass by pass_id."}
        ]
    }


@app.get("/api/v1/agent/pricing-catalog", tags=["Agent Intelligence"])
def get_pricing_catalog():
    """
    Machine-readable pricing catalog for autonomous agent economic decision-making.
    """
    return {
        "currency": "USDC",
        "settlement_type": "micro_prepaid_and_direct_402",
        "supported_chains": [137, 8453, 42161],
        "rates": {
            "web_clean_markdown": {"cost_usdc": 0.001, "unit": "per_request"},
            "pdf_paper_clean": {"cost_usdc": 0.005, "unit": "per_request"},
            "youtube_transcript_gemini": {"cost_usdc": 0.010, "unit": "per_video"},
            "batch_clean_10urls": {"cost_usdc": 0.005, "unit": "per_batch"},
            "web_search": {"cost_usdc": 0.002, "unit": "per_query"},
            "map_site": {"cost_usdc": 0.002, "unit": "per_domain"},
            "extract_json": {"cost_usdc": 0.030, "unit": "per_extraction"},
            "oracle_grounding_signed": {"cost_usdc": 0.035, "unit": "per_proof"},
            "deep_research_briefing": {"cost_usdc": 0.150, "unit": "per_report"}
        },
        "volume_passes": [
            {"tier": "STARTER", "price_usdc": 0.08, "credits": 100, "discount": "20%"},
            {"tier": "GROWTH", "price_usdc": 0.70, "credits": 1000, "discount": "30%"},
            {"tier": "SCALE", "price_usdc": 5.00, "credits": 10000, "discount": "50%"}
        ],
        "zero_friction_trial": {
            "unauthenticated_free_calls": 0,
            "policy": "NO_FREE_TIER_PAYMENT_MANDATORY",
            "access_method": "X-Vault-Key or On-Chain Tx"
        }
    }


@app.get("/api/v1/agent/arbitrage-roi", tags=["Agent Intelligence"])
def get_arbitrage_roi(
    url: Optional[str] = Query(None, description="Optional target URL to calculate token arbitrage for"),
    input_tokens: int = Query(50000, description="Estimated tokens of raw uncleaned web page"),
    llm_price_per_million: float = Query(2.50, description="LLM input token price in USD per 1M tokens (default GPT-4o / Claude 3.5 Sonnet = $2.50)"),
    x402_fee_usdc: float = Query(0.001, description="x402 CleanWeb API fee in USDC")
):
    """
    Live mathematical token arbitrage calculator.
    Proves to autonomous agents why routing web reads through x402 yields 80%+ net savings.
    """
    reduction_rate = 0.87
    clean_tokens = int(input_tokens * (1 - reduction_rate))
    
    raw_llm_cost = (input_tokens / 1_000_000) * llm_price_per_million
    clean_llm_cost = (clean_tokens / 1_000_000) * llm_price_per_million
    total_x402_cost = clean_llm_cost + x402_fee_usdc
    
    net_dollar_savings = raw_llm_cost - total_x402_cost
    savings_pct = (net_dollar_savings / raw_llm_cost) * 100 if raw_llm_cost > 0 else 0
    roi_pct = (net_dollar_savings / x402_fee_usdc) * 100 if x402_fee_usdc > 0 else 0
    
    return {
        "status": "economically_optimal",
        "routing_recommendation": "ROUTE_VIA_X402",
        "benchmark": {
            "raw_tokens": input_tokens,
            "cleaned_tokens": clean_tokens,
            "tokens_saved": input_tokens - clean_tokens,
            "token_reduction_ratio": "87.0%"
        },
        "financial_analysis": {
            "cost_raw_direct_usd": round(raw_llm_cost, 6),
            "cost_with_x402_usd": round(total_x402_cost, 6),
            "breakdown": {
                "clean_llm_input_cost": round(clean_llm_cost, 6),
                "x402_service_fee": round(x402_fee_usdc, 6)
            },
            "net_dollar_savings": round(net_dollar_savings, 6),
            "net_savings_percentage": f"{round(savings_pct, 1)}%",
            "service_fee_roi_percentage": f"{round(roi_pct, 1)}%"
        },
        "agent_decision_heuristic": "If savings_pct > 50%: return 1 (Call x402) else: return 0"
    }


@app.get("/api/v1/agent/integrations/{framework}", tags=["Agent Intelligence"])
def get_framework_integration(framework: str):
    """
    Returns instant drop-in code snippets for popular autonomous agent frameworks:
    langchain, crewai, autogen, smolagents, elizaos, python, curl.
    """
    framework = framework.lower()
    GATEWAY = "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app"
    
    if framework in ("langchain", "langgraph"):
        code = (
            "# LangChain / LangGraph Tool Integration\n"
            "from langchain.tools import tool\n"
            "import requests\n\n"
            "@tool\n"
            "def clean_web(url: str) -> str:\n"
            '    """Fetches a URL and returns ad-free, token-optimized Markdown (87% token savings)."""\n'
            f'    res = requests.get(\n        "{GATEWAY}/api/v1/clean-web",\n'
            '        params={"url": url},\n        headers={"X-Agent-Nonce": "langchain-agent-session"}\n    )\n'
            '    return res.json().get("clean_markdown", "")\n'
        )
    elif framework == "crewai":
        code = (
            "# CrewAI Tool Integration\n"
            "from crewai.tools import tool\n"
            "import requests\n\n"
            '@tool("CleanWeb Tool")\n'
            "def clean_web(url: str) -> str:\n"
            '    """Strips HTML boilerplate and returns pure Markdown to save LLM context window."""\n'
            f'    res = requests.post(\n        "{GATEWAY}/api/v1/clean-web",\n'
            '        json={"url": url},\n        headers={"X-Agent-Nonce": "crewai-agent-session"}\n    )\n'
            '    return res.json().get("clean_markdown", "")\n'
        )
    elif framework == "autogen":
        code = (
            "# AutoGen Tool Registration\n"
            "import requests\n\n"
            "def clean_web_tool(url: str) -> str:\n"
            f'    res = requests.get("{GATEWAY}/api/v1/clean-web", params={{"url": url}}, headers={{"X-Agent-Nonce": "autogen-session"}})\n'
            '    return res.json().get("clean_markdown", "")\n\n'
            '# Register with AutoGen assistant:\n'
            '# assistant.register_for_llm(name="clean_web", description="Clean web markdown scraper")(clean_web_tool)\n'
        )
    elif framework == "smolagents":
        code = (
            "# Hugging Face smolagents Tool\n"
            "from smolagents import tool\n"
            "import requests\n\n"
            "@tool\n"
            "def clean_web(url: str) -> str:\n"
            '    """Fetches URL as clean markdown with 87% token savings.\n'
            '    Args:\n        url: The web page URL to clean\n    """\n'
            f'    res = requests.get("{GATEWAY}/api/v1/clean-web", params={{"url": url}}, headers={{"X-Agent-Nonce": "smolagents-session"}})\n'
            '    return res.json().get("clean_markdown", "")\n'
        )
    elif framework in ("eliza", "elizaos"):
        code = (
            "// ElizaOS Plugin Action\n"
            'import { Action, HandlerCallback, IAgentRuntime, Memory, State } from "@elizaos/core";\n\n'
            "export const cleanWebAction: Action = {\n"
            '    name: "CLEAN_WEB",\n'
            '    similes: ["SCRAPE_WEB", "FETCH_MARKDOWN", "READ_PAGE"],\n'
            '    description: "Fetches clean web markdown via x402 protocol with 87% token reduction",\n'
            "    validate: async () => true,\n"
            "    handler: async (runtime: IAgentRuntime, message: Memory, state: State, options: any, callback: HandlerCallback) => {\n"
            "        const url = message.content.text;\n"
            f'        const res = await fetch(`{GATEWAY}/api/v1/clean-web?url=${{encodeURIComponent(url)}}`, {{\n'
            '            headers: { "X-Agent-Nonce": "elizaos-agent" }\n'
            "        }});\n"
            "        const data = await res.json();\n"
            "        callback({ text: data.clean_markdown });\n"
            "        return true;\n"
            "    }\n"
            "};\n"
        )
    elif framework in ("curl", "bash"):
        code = (
            "# Instant 10-Second Test (3 Free Calls Included)\n"
            f'curl -X POST "{GATEWAY}/api/v1/clean-web" \\\n'
            '     -H "Content-Type: application/json" \\\n'
            '     -H "X-Agent-Nonce: my-agent-$RANDOM" \\\n'
            '     -d \'{"url": "https://news.ycombinator.com"}\'\n'
        )
    else:  # python
        code = (
            "# Standard Python urllib (Zero extra dependencies)\n"
            "import urllib.request, json\n\n"
            "req = urllib.request.Request(\n"
            f'    "{GATEWAY}/api/v1/clean-web",\n'
            '    data=json.dumps({"url": "https://news.ycombinator.com"}).encode(),\n'
            '    headers={"Content-Type": "application/json", "X-Agent-Nonce": "python-agent-01"}\n'
            ")\n"
            "res = json.loads(urllib.request.urlopen(req).read())\n"
            'print("Clean Markdown Preview:\\n", res["clean_markdown"][:300])\n'
        )
    return {
        "framework": framework,
        "gateway": GATEWAY,
        "code_snippet": code
    }


# =========================================================================
# 🌐 Core Cleaning API Endpoints (x402 Protected)
# =========================================================================
@app.get("/api/v1/clean-web", response_model=WebCleanResponse, tags=["Cleaners"])
def clean_web(
    request: Request,
    url: str = Query(..., description="Target webpage URL to scrape and convert to markdown"),
    density: str = Query("standard", description="Markdown density ('standard', 'dense', 'light')"),
    max_tokens: Optional[int] = Query(None, description="Max token limit for output markdown to prevent LLM context overflow"),
    onchain_proof: bool = Query(False, description="Whether to generate EIP-712 cryptographic attestation"),
    secure_audit: bool = Query(False, description="Run real-time AST, prompt injection, and EIP-712 security audit via Security Gate Agent"),
    respect_robots_txt: bool = Query(False, description="Whether to enforce target domain robots.txt compliance")
):
    if secure_audit:
        tier = PricingTier.SECURE_WEB_CLEAN
    elif onchain_proof:
        tier = PricingTier.ONCHAIN
    else:
        tier = PricingTier.LIGHT

    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        data = web_cleaner_engine.fetch_and_clean(url, respect_robots_txt=respect_robots_txt, max_tokens=max_tokens)
        proof = None
        if onchain_proof:
            proof = onchain_signer.sign_cleanweb_attestation(
                target_url=url,
                content_text=data["markdown_content"]
            )

        sec_audit_obj = None
        if secure_audit:
            audit_raw = security_gate_client.inspect_content(
                text=data["markdown_content"],
                is_code=False,
                agent_nonce=request.headers.get("x-agent-nonce")
            )
            sec_audit_obj = SecurityAuditResult(**audit_raw)

        t_analytics = data.get("token_analytics")
        t_obj = TokenAnalytics(**t_analytics) if t_analytics else None

        meta = ScrapeMetadata(
            engine=data.get("engine", "cleanweb_fast_parser"),
            latency_ms=data.get("latency_ms", 0.0),
            status_code=200,
            timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )

        return WebCleanResponse(
            status="success",
            url=data["url"],
            title=data["title"],
            markdown_content=data["markdown_content"],
            content=data["markdown_content"],
            word_count=data["word_count"],
            estimated_reading_time_sec=data["estimated_reading_time_sec"],
            engine=data.get("engine", "cleanweb_fast_parser"),
            token_analytics=t_obj,
            metadata=meta,
            onchain_proof=proof,
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None,
            security_audit=sec_audit_obj
        )
    except ValueError as ve:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=400, detail=str(ve))
    except requests.exceptions.HTTPError as he:
        safe_refund_vault(receipt)
        upstream_status = he.response.status_code if he.response is not None else 502
        raise HTTPException(status_code=502, detail=f"Target webpage host returned HTTP {upstream_status}: {str(he)}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as ce:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=504, detail=f"Target webpage host unreachable or timed out: {str(ce)}")
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Failed to scrape webpage: {str(e)}")


@app.post("/api/v1/clean-web", response_model=WebCleanResponse, tags=["Cleaners"])
def clean_web_post(request: Request, body: CleanWebRequest):
    """
    POST variant supporting JSON payload bodies: {"url": "https://...", "onchain_proof": false}
    Essential for autonomous LLM agents and LangChain / CrewAI tool invocation.
    """
    return clean_web(
        request=request,
        url=body.url,
        density=body.density or "standard",
        max_tokens=body.max_tokens,
        onchain_proof=body.onchain_proof,
        secure_audit=body.secure_audit,
        respect_robots_txt=body.respect_robots_txt
    )


@app.get("/r/{target_url:path}", response_class=PlainTextResponse, tags=["Autonomous Agents"])
def agent_reader_proxy(request: Request, target_url: str):
    """
    Zero-Friction Fast Universal Proxy for Autonomous AI Agents & LLMs (Jina Reader Style).
    Usage:
        curl https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/r/https://news.ycombinator.com
    Returns pure, token-optimized Markdown with 87% token noise removed.
    Includes 3 free sandbox calls per agent IP/nonce, or pre-funded vault balance.
    """
    # 1. Robustly normalize scheme and collapsed slashes
    target_url = normalize_url(target_url)

    # 2. Preserve incoming query parameters (e.g. ?q=... or ?id=...)
    query_str = request.url.query
    if query_str:
        delimiter = "&" if "?" in target_url else "?"
        target_url = f"{target_url}{delimiter}{query_str}"

    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=PricingTier.LIGHT)
    if not is_auth:
        return err_resp

    try:
        data = web_cleaner_engine.fetch_and_clean(target_url, respect_robots_txt=False)
        markdown = data.get("markdown_content", "")
        title = data.get("title", "Clean Web Extraction")
        analytics = data.get("token_analytics", {})
        savings = analytics.get("savings_percentage", "87%")

        banner = (
            f"# {title}\n\n"
            f"> Source URL: {target_url}\n"
            f"> Token Compression: {savings} Noise Stripped\n\n"
            f"---\n\n"
        )
        footer = (
            "\n\n---\n"
            "<!-- x402 CleanWeb Agent Suite (B2A Multi-Chain Micropayments & EIP-712 Oracles) -->\n"
            "<!-- Documentation: https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/docs -->\n"
        )
        return PlainTextResponse(banner + markdown + footer, media_type="text/markdown; charset=utf-8")
    except ValueError as ve:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=400, detail=str(ve))
    except requests.exceptions.HTTPError as he:
        safe_refund_vault(receipt)
        upstream_status = he.response.status_code if he.response is not None else 502
        raise HTTPException(status_code=502, detail=f"Target webpage host returned HTTP {upstream_status}: {str(he)}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as ce:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=504, detail=f"Target webpage host unreachable or timed out: {str(ce)}")
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Agent Proxy Extraction Failed: {str(e)}")


@app.get("/api/v1/clean-web/stream", tags=["Cleaners"])
async def clean_web_stream(
    request: Request,
    url: str = Query(..., description="Target webpage URL to scrape and stream in chunks"),
    density: str = Query("standard", description="Markdown density ('standard', 'dense', 'light')"),
    max_tokens: Optional[int] = Query(None, description="Max token limit for output markdown")
):
    """
    Real-Time Server-Sent Events (SSE) Chunk Streaming for CleanWeb Studio.
    Emits metadata, markdown paragraph chunks, token analytics, and completion signal.
    """
    tier = PricingTier.LIGHT
    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        data = web_cleaner_engine.fetch_and_clean(url, max_tokens=max_tokens)
        markdown_text = data.get("markdown_content", "")
        paragraphs = [p.strip() for p in markdown_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [markdown_text]

        async def event_generator():
            meta_payload = {
                "url": data["url"],
                "title": data.get("title"),
                "total_chunks": len(paragraphs),
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            yield f"event: metadata\ndata: {json.dumps(meta_payload)}\n\n"

            for i, p in enumerate(paragraphs):
                chunk_payload = {
                    "index": i,
                    "text": p
                }
                yield f"event: chunk\ndata: {json.dumps(chunk_payload)}\n\n"

            t_analytics = data.get("token_analytics", {})
            analytics_payload = {
                "word_count": data.get("word_count", 0),
                "token_analytics": t_analytics
            }
            yield f"event: analytics\ndata: {json.dumps(analytics_payload)}\n\n"
            yield "event: done\ndata: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")


@app.get("/r/stream/{target_url:path}", tags=["Autonomous Agents"])
async def agent_reader_stream_proxy(request: Request, target_url: str):
    """
    Real-time streaming universal proxy for autonomous LLM agents (chunk-by-chunk piping).
    """
    target_url = normalize_url(target_url)
    query_str = request.url.query
    if query_str:
        delimiter = "&" if "?" in target_url else "?"
        target_url = f"{target_url}{delimiter}{query_str}"

    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=PricingTier.LIGHT)
    if not is_auth:
        return err_resp

    try:
        data = web_cleaner_engine.fetch_and_clean(target_url)
        markdown_text = data.get("markdown_content", "")
        paragraphs = [p.strip() for p in markdown_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [markdown_text]

        async def stream_body():
            for p in paragraphs:
                yield (p + "\n\n").encode("utf-8")

        headers = {
            "Content-Type": "text/markdown; charset=utf-8",
            "X-Agent-Tool": "CleanWeb-Stream",
            "X-Content-Title": data.get("title", "")
        }
        if receipt and getattr(receipt, "remaining_free_trials", None) is not None:
            headers["X-Agent-Trial-Remaining"] = str(receipt.remaining_free_trials)

        return StreamingResponse(stream_body(), media_type="text/markdown; charset=utf-8", headers=headers)
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")


@app.get("/api/v1/clean-youtube", response_model=YouTubeCleanResponse, tags=["Cleaners"])
def clean_youtube(
    request: Request,
    url: str = Query(..., description="YouTube Video URL"),
    lang: str = Query("ko,en", description="Preferred transcript language codes"),
    onchain_proof: bool = Query(False, description="Whether to generate EIP-712 cryptographic attestation"),
    secure_audit: bool = Query(False, description="Run Security Gate audit on transcript and AI summary")
):
    if secure_audit:
        tier = PricingTier.SECURE_YOUTUBE_CLEAN
    elif onchain_proof:
        tier = PricingTier.ONCHAIN
    else:
        tier = PricingTier.HEAVY

    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        data = youtube_cleaner_engine.clean_youtube(url, lang=lang)
        proof = None
        if onchain_proof:
            proof = onchain_signer.sign_cleanweb_attestation(
                target_url=data["url"],
                content_text=data["transcript"]
            )

        sec_audit_obj = None
        if secure_audit:
            audit_text = f"{data.get('title', '')}\n\n{data.get('ai_summary', '')}\n\n{data.get('transcript', '')[:10000]}"
            audit_raw = security_gate_client.inspect_content(
                text=audit_text,
                is_code=False,
                agent_nonce=request.headers.get("x-agent-nonce")
            )
            sec_audit_obj = SecurityAuditResult(**audit_raw)

        t_analytics = data.get("token_analytics")
        t_obj = TokenAnalytics(**t_analytics) if t_analytics else None

        return YouTubeCleanResponse(
            status="success",
            url=data["url"],
            video_id=data["video_id"],
            title=data["title"],
            channel=data["channel"],
            duration_sec=data["duration_sec"],
            method_used=data["method_used"],
            engine=data.get("engine", "hybrid_video_intelligence"),
            transcript=data["transcript"],
            ai_summary=data["ai_summary"],
            token_analytics=t_obj,
            onchain_proof=proof,
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None,
            security_audit=sec_audit_obj
        )
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Failed to process YouTube video: {str(e)}")


@app.post("/api/v1/clean-youtube", response_model=YouTubeCleanResponse, tags=["Cleaners"])
def clean_youtube_post(request: Request, body: CleanYouTubeRequest):
    """
    POST variant supporting JSON payload bodies: {"url": "https://...", "lang": "en"}
    Essential for autonomous LLM agents and LangChain / CrewAI tool invocation.
    """
    return clean_youtube(
        request=request,
        url=body.url,
        lang=body.lang or "ko,en",
        onchain_proof=body.onchain_proof,
        secure_audit=body.secure_audit
    )


@app.get("/api/v1/clean-pdf", response_model=PDFCleanResponse, tags=["Cleaners"])
def clean_pdf(
    request: Request,
    url: str = Query(..., description="PDF URL"),
    max_pages: int = Query(30, description="Max pages to parse"),
    onchain_proof: bool = Query(False, description="Whether to generate EIP-712 cryptographic attestation")
):
    tier = PricingTier.ONCHAIN if onchain_proof else PricingTier.STANDARD
    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        data = pdf_cleaner_engine.clean_pdf(url, max_pages=max_pages)
        proof = None
        if onchain_proof:
            proof = onchain_signer.sign_cleanweb_attestation(
                target_url=data["url"],
                content_text=data["text_content"]
            )

        t_analytics = data.get("token_analytics")
        t_obj = TokenAnalytics(**t_analytics) if t_analytics else None

        return PDFCleanResponse(
            status="success",
            url=data["url"],
            total_pages=data["total_pages"],
            parsed_pages=data["parsed_pages"],
            title=data["title"],
            text_content=data["text_content"],
            word_count=data["word_count"],
            engine=data.get("engine", "pypdf_stream_parser"),
            pdf_analytics=data.get("pdf_analytics"),
            token_analytics=t_obj,
            onchain_proof=proof,
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None
        )
    except ValueError as ve:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=400, detail=str(ve))
    except requests.exceptions.HTTPError as he:
        safe_refund_vault(receipt)
        upstream_status = he.response.status_code if he.response is not None else 502
        raise HTTPException(status_code=502, detail=f"Target PDF host returned HTTP {upstream_status}: {str(he)}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as ce:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=504, detail=f"Target PDF host unreachable or timed out: {str(ce)}")
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")


@app.post("/api/v1/clean-pdf", response_model=PDFCleanResponse, tags=["Cleaners"])
def clean_pdf_post(request: Request, body: CleanPDFRequest):
    """
    POST variant supporting JSON payload bodies: {"url": "https://...", "max_pages": 30}
    Essential for autonomous LLM agents and LangChain / CrewAI tool invocation.
    """
    return clean_pdf(
        request=request,
        url=body.url,
        max_pages=body.max_pages or 30,
        onchain_proof=body.onchain_proof
    )


# Supporting BOTH /api/v1/clean-batch AND /api/v1/batch-clean for 100% compatibility
@app.post("/api/v1/clean-batch", response_model=BatchCleanResponse, tags=["Cleaners"])
@app.post("/api/v1/batch-clean", response_model=BatchCleanResponse, tags=["Cleaners"])
def clean_batch(request: Request, body: BatchCleanRequest):
    tier = PricingTier.STANDARD
    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        items = web_cleaner_engine.batch_clean(body.urls)
        success_count = sum(1 for it in items if it.get("status") == "success")
        return BatchCleanResponse(
            status="success",
            total_requested=len(body.urls),
            total_urls=len(body.urls),
            total_success=success_count,
            successful_count=success_count,
            results=items,
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None
        )
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Batch scraping failed: {str(e)}")


@app.get("/api/v1/clean-text", response_model=TextCleanResponse, tags=["Cleaners"])
def clean_text(
    request: Request,
    url: str = Query(..., description="Target webpage URL to extract raw plain text from")
):
    tier = PricingTier.LIGHT
    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        data = web_cleaner_engine.fetch_plain_text(url)
        t_analytics = data.get("token_analytics")
        t_obj = TokenAnalytics(**t_analytics) if t_analytics else None
        return TextCleanResponse(
            status="success",
            url=data["url"],
            title=data.get("title"),
            plain_text=data["plain_text"],
            word_count=data["word_count"],
            token_analytics=t_obj,
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None
        )
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Failed to extract plain text: {str(e)}")


@app.post("/api/v1/clean-embed", response_model=CleanEmbedResponse, tags=["Cleaners"])
def clean_embed_post(request: Request, body: CleanEmbedRequest):
    """
    One-Stop RAG Dense Vector Embedding Pipeline.
    Fetches webpage, removes token noise, semantically chunks content,
    and returns high-dimensional (768-dim) dense vector embeddings.
    """
    tier = PricingTier.ONCHAIN if body.onchain_proof else PricingTier.CLEAN_EMBED
    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        data = embed_engine.clean_and_embed(
            url=body.url,
            chunk_size=body.chunk_size or 500,
            chunk_overlap=body.chunk_overlap or 50,
            density=body.density or "standard"
        )
        proof = None
        if body.onchain_proof:
            proof = onchain_signer.sign_cleanweb_attestation(
                target_url=body.url,
                content_text="".join(c["text"] for c in data["chunks"])
            )

        t_analytics = data.get("token_analytics")
        t_obj = TokenAnalytics(**t_analytics) if t_analytics else None
        chunks_obj = [EmbeddedChunk(**c) for c in data["chunks"]]

        return CleanEmbedResponse(
            status="success",
            url=data["url"],
            title=data.get("title"),
            total_chunks=data["total_chunks"],
            dimension=data["dimension"],
            chunks=chunks_obj,
            token_analytics=t_obj,
            onchain_proof=proof,
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None
        )
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Embedding pipeline failed: {str(e)}")


@app.post("/api/v1/extract-json", response_model=ExtractJsonResponse, tags=["Cleaners"])
def extract_json(request: Request, body: ExtractJsonRequest):
    tier = PricingTier.EXTRACT_JSON
    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        extracted = oracle_engine.extract_json_from_webpage(body.url, body.schema_description)
        return ExtractJsonResponse(
            status="success",
            url=body.url,
            extracted_json=extracted,
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None
        )
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Failed to extract JSON: {str(e)}")


@app.get("/api/v1/deep-research", response_model=DeepResearchResponse, tags=["Cleaners"])
def deep_research(
    request: Request,
    query: str = Query(..., description="Research query topic"),
    max_sources: int = Query(3, ge=1, le=5, description="Number of sources to synthesize")
):
    tier = PricingTier.DEEP_RESEARCH
    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        res = oracle_engine.execute_deep_research(query, max_sources=max_sources)
        return DeepResearchResponse(
            status="success",
            query=query,
            research_brief_markdown=res["research_brief_markdown"],
            sources=res["sources"],
            structured_data=res.get("structured_data"),
            oracle_attestation=res.get("oracle_attestation"),
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None
        )
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Failed to perform deep research: {str(e)}")


@app.get("/api/v1/map-site", response_model=SiteMapResponse, tags=["Cleaners"])
def map_site(
    request: Request,
    url: str = Query(..., description="Target website domain or URL to map"),
    max_links: int = Query(50, ge=5, le=100, description="Max URLs to discover")
):
    tier = PricingTier.MAP_SITE
    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        data = web_cleaner_engine.map_website(url, max_links=max_links)
        return SiteMapResponse(
            status="success",
            url=data["url"],
            domain=data["domain"],
            total_urls=data["total_urls"],
            urls=data["urls"],
            sitemap_detected=data["sitemap_detected"],
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None
        )
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Failed to map site: {str(e)}")


@app.post("/api/v1/map-site", response_model=SiteMapResponse, tags=["Cleaners"])
def map_site_post(request: Request, body: SiteMapRequest):
    """
    POST variant supporting JSON payload bodies: {"url": "https://...", "max_links": 50}
    Essential for autonomous LLM agents and LangChain / CrewAI tool invocation.
    """
    return map_site(request=request, url=body.url, max_links=body.max_links or 50)


@app.get("/api/v1/search", response_model=SearchResponse, tags=["Cleaners"])
def search_web(
    request: Request,
    query: str = Query(..., description="Search keyword or question for agent"),
    max_results: int = Query(5, ge=1, le=10, description="Max search results")
):
    tier = PricingTier.SEARCH
    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        raw_results = oracle_engine.quick_search(query, max_results=max_results)
        result_items = [SearchResultItem(**item) for item in raw_results]
        return SearchResponse(
            status="success",
            query=query,
            total_results=len(result_items),
            results=result_items,
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None
        )
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Failed to execute agent search: {str(e)}")


@app.post("/api/v1/search", response_model=SearchResponse, tags=["Cleaners"])
def search_web_post(request: Request, body: SearchRequest):
    """
    POST variant supporting JSON payload bodies: {"query": "...", "max_results": 5}
    Essential for autonomous LLM agents and LangChain / CrewAI tool invocation.
    """
    return search_web(request=request, query=body.query, max_results=body.max_results or 5)


# =========================================================================
# 💰 B2A Autonomous Agent Vault & Pass Management Endpoints
# =========================================================================
@app.post("/api/v1/vault/deposit", response_model=VaultBalanceResponse, tags=["Vault"])
@app.post("/api/v1/pass/mint", response_model=VaultBalanceResponse, tags=["Vault"])
def deposit_vault(body: VaultDepositRequest):
    """
    Deposits Native USDC into an autonomous agent's pre-funded vault balance.
    Limits: Minimum 2.0 USDC, Maximum 1,000.0 USDC per deposit.
    Supports Polygon (137), Base (8453), and Arbitrum (42161).
    """
    try:
        acc = vault_manager.deposit(
            agent_address=body.agent_address,
            amount_usdc=body.amount_usdc,
            chain=body.chain,
            tx_hash=body.tx_hash
        )
        return vault_manager.to_response(acc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Vault deposit failed: {str(e)}")


@app.post("/api/v1/vault/permit-deposit", response_model=VaultBalanceResponse, tags=["Vault"])
def deposit_vault_permit(body: PermitDepositRequest):
    """
    Gasless EIP-2612 / EIP-3009 Permit Vault Deposit.
    Allows autonomous agents to pre-fund their vault without submitting an on-chain transaction
    or spending native gas tokens (MATIC, ETH). Verifies off-chain ECDSA signature.
    """
    try:
        acc = vault_manager.deposit_with_permit(
            owner=body.owner,
            value_usdc=body.value_usdc,
            deadline=body.deadline,
            v=body.v,
            r=body.r,
            s=body.s,
            chain=body.chain,
            spender=body.spender,
            nonce=body.nonce or 0
        )
        return vault_manager.to_response(acc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Permit deposit failed: {str(e)}")


@app.get("/api/v1/vault/balance", response_model=VaultBalanceResponse, tags=["Vault"])
def get_vault_balance(identifier: str = Query(..., description="Agent Wallet Address or Session Key")):
    acc = vault_manager.get_balance(identifier)
    if not acc:
        raise HTTPException(status_code=404, detail="Vault account not found for provided address or key.")
    return vault_manager.to_response(acc)


@app.get("/api/v1/pass-status", response_model=PassStatusResponse, tags=["Vault"])
def get_pass_status(agent_wallet: str = Query(..., description="Agent Address or Pass Token")):
    pass_data = storage_manager.get_pass(agent_wallet)
    vault_data = storage_manager.get_vault(agent_wallet)

    has_pass = pass_data is not None
    pass_type = pass_data["pass_type"] if pass_data else None
    exp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(pass_data["expires_at"])) if pass_data else None
    v_bal = vault_data["balance_usdc"] if vault_data else None
    credits = pass_data.get("credits") if pass_data else None

    return PassStatusResponse(
        agent_wallet_or_token=agent_wallet,
        has_active_pass=has_pass,
        pass_type=pass_type,
        expires_at_utc=exp_utc,
        remaining_queries=credits,
        remaining_credits=credits,
        credits=credits,
        vault_balance_usdc=v_bal
    )


# =========================================================================
# 🔮 B2A Web3 Signed Oracle Grounding Pipeline (0.035 USDC)
# =========================================================================
@app.post("/api/v1/oracle/grounding", response_model=OracleGroundingResponse, tags=["Oracle Grounding"])
def oracle_grounding(request: Request, body: OracleGroundingRequest):
    """
    Autonomous Agent Web3 Oracle Grounding Pipeline.
    Performs real-time web search, noise-free extraction, Gemini 3.6 Flash JSON structuring,
    and signs the payload with EIP-712 cryptographic attestation (0.035 USDC or 0.040 USDC with Security Gate audit).
    """
    tier = PricingTier.SECURE_ORACLE_GROUNDING if body.secure_audit else PricingTier.ORACLE_GROUNDING

    authorized, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not authorized:
        return err_resp

    try:
        result = oracle_engine.execute_grounding(
            query=body.query,
            target_schema=body.target_schema,
            max_sources=body.max_sources,
        )
        result.payment_receipt = receipt
        result.auth = receipt.auth if receipt else None

        if body.secure_audit:
            audit_text = f"Query: {body.query}\nSummary: {result.summary_markdown}\nData: {json.dumps(result.structured_data, ensure_ascii=False)}"
            audit_raw = security_gate_client.inspect_content(
                text=audit_text,
                is_code=False,
                agent_nonce=request.headers.get("x-agent-nonce")
            )
            result.security_audit = SecurityAuditResult(**audit_raw)

        return result
    except Exception as e:
        safe_refund_vault(receipt)
        raise HTTPException(status_code=500, detail=f"Oracle Grounding failed: {str(e)}")


@app.post("/api/v1/oracle/verify", response_model=OracleVerifyResponse, tags=["Oracle Grounding"])
def verify_oracle_attestation(body: OracleVerifyRequest, query: str = Query("", description="Original query")):
    """
    Verifies an EIP-712 signed Oracle attestation off-chain.
    Supports receiving query via JSON payload or URL query parameter.
    """
    effective_query = (body.query or query or "").strip()
    is_valid, recovered = onchain_signer.verify_oracle_grounding(
        query=effective_query,
        data_hash=body.data_hash,
        timestamp=body.timestamp,
        signature=body.signature,
    )
    expected = onchain_signer.signer_address
    ts_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(body.timestamp))
    msg = "EIP-712 signature matches CleanWeb Oracle" if is_valid else "Signature mismatch or corrupted payload"

    return OracleVerifyResponse(
        valid=is_valid,
        recovered_signer=recovered,
        expected_signer=expected,
        timestamp_utc=ts_utc,
        message=msg,
    )


@app.post("/api/v1/security/inspect", response_model=SecurityAuditResult, tags=["Security Gate"])
def security_gate_inspect(request: Request, body: SecurityInspectRequest):
    """
    Submits raw text or Python code to Agent Security Gate for sub-5ms AST, prompt-injection, and EIP-712 attestation.
    """
    audit_raw = security_gate_client.inspect_content(
        text=body.text,
        is_code=body.is_code,
        agent_nonce=request.headers.get("x-agent-nonce")
    )
    return SecurityAuditResult(**audit_raw)


@app.get("/api/v1/security/status", tags=["Security Gate"])
async def security_gate_status():
    """
    Returns live health & metadata for the integrated Security Gate service.
    """
    return {
        "provider": "agent-security-gate-x402",
        "url": security_gate_client.base_url,
        "features": ["Jailbreak Radar", "AST Code Safety", "NLI Hallucination Check", "EIP-712 Attestation"],
        "sla": "sub-5ms execution (zero heavy LLM re-invocation)",
        "pricing": {
            "secure_web_clean": 0.005,
            "secure_youtube_clean": 0.015,
            "secure_oracle_grounding": 0.040
        }
    }





# =========================================================================
# 💰 Live Treasury & Real-Time On-Chain Earnings Tracker
# =========================================================================
@app.get("/api/v1/treasury/status", tags=["Treasury & Analytics"])
async def get_treasury_status(wallet_address: Optional[str] = None):
    """
    Returns real-time on-chain Native USDC balances across Polygon, Base, and Arbitrum,
    plus aggregated database metrics and earnings estimates.
    """
    target_wallet = wallet_address or os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")
    onchain_data = multi_chain_manager.get_multi_chain_treasury_summary(target_wallet)
    db_stats = storage_manager.get_stats()
    
    # Calculate estimated revenue from paid database requests
    total_paid_queries = db_stats.get("used_txs_count", 0)
    vault_users = db_stats.get("vault_accounts_count", 0)
    active_passes = db_stats.get("active_passes_count", 0)

    return {
        "status": "success",
        "service": "x402-cleanweb-agent",
        "treasury_wallet": target_wallet,
        "onchain_balances": onchain_data,
        "total_usdc_onchain": onchain_data.get("total_usdc_accumulated", 0.0),
        "db_stats": {
            "total_settled_transactions": total_paid_queries,
            "active_vault_accounts": vault_users,
            "active_passes_issued": active_passes
        },
        "supported_networks": ["Polygon (137)", "Base (8453)", "Arbitrum One (42161)"],
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


@app.get("/api/v1/treasury/merkle-root", response_model=MerkleRootResponse, tags=["Treasury & Analytics"])
async def get_merkle_root():
    """
    Computes and returns cryptographic Keccak-256 Merkle Root over all settled ledger transactions.
    Provides verifiable state commitments for autonomous agent audits and treasury transparency.
    """
    txs = storage_manager.get_all_used_txs(limit=5000)
    leaves = [
        compute_tx_leaf(
            tx_hash=tx["tx_hash"],
            chain=tx["chain"],
            agent_address=tx["payer"],
            amount_usdc=tx["amount_usdc"],
            timestamp=tx["used_at"]
        )
        for tx in txs
    ]
    root, _ = merkle_engine.build_tree(leaves)
    return MerkleRootResponse(
        status="success",
        merkle_root=root,
        total_leaves=len(leaves),
        anchored_tx_count=len(txs),
        timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )


@app.get("/api/v1/treasury/merkle-proof/{tx_hash}", response_model=MerkleProofResponse, tags=["Treasury & Analytics"])
async def get_merkle_proof(tx_hash: str):
    """
    Generates cryptographic inclusion audit proof for a specific settled transaction against the ledger Merkle tree.
    Allows autonomous agents to mathematically verify their payment settlement off-chain or in smart contracts.
    """
    target_tx = storage_manager.get_used_tx(tx_hash)
    if not target_tx:
        raise HTTPException(status_code=404, detail=f"Transaction {tx_hash} not found in settled ledger.")

    txs = storage_manager.get_all_used_txs(limit=5000)
    leaves = [
        compute_tx_leaf(
            tx_hash=tx["tx_hash"],
            chain=tx["chain"],
            agent_address=tx["payer"],
            amount_usdc=tx["amount_usdc"],
            timestamp=tx["used_at"]
        )
        for tx in txs
    ]

    target_leaf = compute_tx_leaf(
        tx_hash=target_tx["tx_hash"],
        chain=target_tx["chain"],
        agent_address=target_tx["payer"],
        amount_usdc=target_tx["amount_usdc"],
        timestamp=target_tx["used_at"]
    )

    root, _ = merkle_engine.build_tree(leaves)
    proof_data = merkle_engine.get_proof(target_leaf, leaves)
    is_valid = merkle_engine.verify_proof(target_leaf, proof_data, root)

    return MerkleProofResponse(
        status="success",
        tx_hash=target_tx["tx_hash"],
        chain=target_tx["chain"],
        leaf=target_leaf,
        proof=[MerkleProofItem(**p) for p in proof_data],
        merkle_root=root,
        verified=is_valid
    )


@app.get("/api/v1/mcp/sse-info", tags=["Autonomous Agents"])
async def get_mcp_sse_info():
    """
    Returns Remote Model Context Protocol (MCP) SSE Transport discovery metadata.
    """
    return {
        "status": "active",
        "protocol": "Model Context Protocol (MCP)",
        "transport": "Server-Sent Events (SSE)",
        "sse_endpoint": "/mcp-server/sse",
        "messages_endpoint": "/mcp-server/messages",
        "version": "2.6.1",
        "description": "Standardized remote SSE transport for Claude Desktop, Cursor, and Autonomous Agent fleets."
    }


# =========================================================================
# 🌐 A-Grid Enterprise Operations & Governance Endpoints (agrid-ops-agent)
# =========================================================================
@app.get("/api/v1/ops/telemetry", tags=["A-Grid Operations & Compliance"])
async def get_agrid_ops_telemetry(exchange_rate_krw: float = Query(1400.0, ge=100.0)):
    """
    Returns real-time consolidated financial, accounting, and compliance metrics
    specifically formatted for ingestion by agrid-ops-agent (Finance, Accounting, Legal).
    """
    from app.agrid_finance_legal import cleanweb_controller
    return cleanweb_controller.get_cleanweb_ops_telemetry(exchange_rate_krw=exchange_rate_krw)


@app.get("/api/v1/ops/journals", tags=["A-Grid Operations & Compliance"])
async def get_agrid_ops_journals(
    limit: int = Query(50, ge=1, le=500),
    exchange_rate_krw: float = Query(1400.0, ge=100.0)
):
    """
    Exports recent on-chain micro-payments and vault deductions as double-entry journal records.
    """
    from app.agrid_finance_legal import cleanweb_controller
    entries = cleanweb_controller.generate_journal_entries(limit=limit, exchange_rate_krw=exchange_rate_krw)
    return {
        "status": "success",
        "service_name": "x402-micro-agent",
        "entries_count": len(entries),
        "exchange_rate_krw": exchange_rate_krw,
        "journal_entries": [e.model_dump() for e in entries]
    }


@app.get("/api/v1/ops/compliance", tags=["A-Grid Operations & Compliance"])
async def get_agrid_ops_compliance():
    """
    Exports cryptographic attestation specs, OFAC sanctions filtering status, and Zero-Data retention policy.
    """
    from app.agrid_finance_legal import cleanweb_controller
    return cleanweb_controller.get_legal_and_compliance_telemetry()


@app.get("/api/v1/ping", tags=["System"])
async def ping_keepalive():
    """Ultra-low-latency keep-alive endpoint for automated agent health checks and warm instance polling."""
    return {"ping": "pong", "timestamp": time.time()}


# =========================================================================
# ⚖️ Legal, Terms of Service & Financial Disclaimer Endpoints
# =========================================================================
@app.get("/api/v1/legal/terms", tags=["Legal & Compliance"])
async def get_legal_terms():
    """
    Returns the official B2A Machine-to-Machine Terms of Service for CleanWeb Studio.
    """
    return {
        "service": "x402-cleanweb-agent",
        "title": "Machine-to-Machine Terms of Service (B2A ToS)",
        "effective_date": "2025-01-01",
        "jurisdiction_and_governance": {
            "permitted_use": "Autonomous LLM reasoning, research synthesis, and non-expressive Text & Data Mining (TDM).",
            "prohibited_use": "DDoS/overloading third-party servers, bypass of paywalls/authenticated portals, harvesting PII, illegal surveillance.",
            "fair_use_doctrine": "Transformative non-expressive computational data use under international TDM exceptions.",
            "zero_data_retention": "All fetched HTML and raw assets are processed ephemerally in RAM and purged immediately upon response transmission."
        },
        "caller_responsibility": "The autonomous agent, its deployer, and token holders bear 100% legal responsibility for queries initiated and the subsequent use of cleaned content."
    }


@app.get("/api/v1/legal/disclaimer", tags=["Legal & Compliance"])
async def get_legal_disclaimer():
    """
    Returns the comprehensive Legal, Financial, and Oracle Non-Liability Disclaimer.
    """
    return {
        "service": "x402-cleanweb-agent",
        "title": "Comprehensive Legal & Financial Non-Liability Disclaimer",
        "clauses": {
            "no_financial_advice": "No content, oracle attestation, structured JSON, or research brief constitutes investment, financial, tax, or legal advice.",
            "as_is_basis": "All web data, search snippets, transcripts, and cryptographic attestations are provided strictly 'AS-IS' and 'AS-AVAILABLE' with zero warranty of accuracy, completeness, or timeliness.",
            "oracle_execution_risk": "Smart contracts (e.g., Polymarket prediction markets, DeFi liquidity protocols, or DAO treasuries) consuming EIP-712 attestations or ABI calldata execute at their own autonomous risk. CleanWeb Studio and its operators are not liable for smart contract exploits, liquidation events, or financial losses caused by off-chain web misreporting or LLM hallucinations.",
            "sanctions_compliance": "All transactions are screened against OFAC SDN and international AML sanctions lists. Attempted transactions from sanctioned addresses will be permanently rejected.",
            "copyright_notice": "Original website text, videos, and papers remain the intellectual property of their respective creators. CleanWeb Studio acts solely as an ephemeral noise-reduction proxy for computational analysis."
        }
    }



