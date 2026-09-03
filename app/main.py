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

from fastapi import FastAPI, Request, HTTPException, status, Query, Body, Response
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.schemas import (
    PricingTier,
    WebCleanResponse,
    YouTubeCleanResponse,
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
)
from app.x402_verifier import x402_verifier
from app.cleaners.web_engine import web_cleaner_engine
from app.cleaners.youtube_engine import youtube_cleaner_engine
from app.cleaners.pdf_engine import pdf_cleaner_engine
from app.onchain_signer import onchain_signer
from app.vault_manager import vault_manager
from app.storage import storage_manager
from app.multi_chain import multi_chain_manager
from app.oracle_engine import oracle_engine


load_dotenv()

app = FastAPI(
    title="CleanWeb Studio (x402 AI Agent Suite)",
    description="Deterministic Web3 x402 Micropayment MCP & AI Agent Tool Suite with Gemini 3.6 Flash Video Intelligence on Polygon, Base, and Arbitrum.",
    version="2.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML_PATH = STATIC_DIR / "index.html"
AP2_FILE_PATH = BASE_DIR / ".well-known" / "ap2.json"
GLAMA_FILE_PATH = BASE_DIR / "glama.json"
MCP_SPEC_FILE_PATH = BASE_DIR / "mcp_tool_spec.json"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "cleanweb-wh-secret-2026")


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
    # Skip rate limiting for static assets and metrics
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"

    if not path.startswith("/static") and path not in ("/metrics", "/health"):
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
        "name": "CleanWeb Studio",
        "version": "2.4.0",
        "protocol": "x402 (HTTP 402 Monetized)",
        "networks": ["Polygon (137)", "Base (8453)", "Arbitrum (42161)"],
        "pricing_tiers": {
            "web_clean": "0.001 USDC",
            "pdf_or_batch": "0.005 USDC",
            "youtube_gemini_ai": "0.010 USDC",
            "onchain_attestation": "0.020 USDC"
        },
        "interactive_dashboard": "/dashboard",
        "metrics_url": "/metrics",
        "endpoints": {
            "clean_web": "/api/v1/clean-web?url=https://example.com",
            "clean_youtube": "/api/v1/clean-youtube?url=https://www.youtube.com/watch?v=aircAruvnKk",
            "clean_pdf": "/api/v1/clean-pdf?url=https://example.com/paper.pdf",
            "clean_batch": "/api/v1/clean-batch",
            "batch_clean_alias": "/api/v1/batch-clean",
            "stripe_checkout": "/api/v1/checkout/stripe-session",
            "stripe_webhook": "/api/v1/webhook/stripe",
            "vault_deposit": "/api/v1/vault/deposit",
            "vault_balance": "/api/v1/vault/balance",
            "pass_status": "/api/v1/pass-status",
            "ap2_manifest": "/.well-known/ap2",
            "mcp_tools": "/mcp/tools",
            "metrics": "/metrics",
            "health": "/health"
        }
    }


@app.get("/dashboard", tags=["System"])
async def dashboard():
    if INDEX_HTML_PATH.exists():
        return FileResponse(INDEX_HTML_PATH, media_type="text/html")
    return HTMLResponse("<h1>CleanWeb Studio Dashboard</h1><p>Dashboard UI template not found.</p>")


@app.get("/health", tags=["System"])
async def health_check():
    db_stats = storage_manager.get_stats()
    return {
        "status": "healthy",
        "service": "x402-cleanweb-agent",
        "version": "2.3.0",
        "storage": "sqlite3_wal_ready",
        "storage_stats": db_stats,
        "chains_connected": ["Polygon(137)", "Base(8453)", "Arbitrum(42161)"]
    }


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


# =========================================================================
# 🌐 Core Cleaning API Endpoints (x402 Protected)
# =========================================================================
@app.get("/api/v1/clean-web", response_model=WebCleanResponse, tags=["Cleaners"])
async def clean_web(
    request: Request,
    url: str = Query(..., description="Target webpage URL to scrape and convert to markdown"),
    onchain_proof: bool = Query(False, description="Whether to generate EIP-712 cryptographic attestation")
):
    tier = PricingTier.ONCHAIN if onchain_proof else PricingTier.LIGHT
    is_auth, receipt, err_resp = x402_verifier.verify_request(request, tier=tier)
    if not is_auth:
        return err_resp

    try:
        data = web_cleaner_engine.fetch_and_clean(url)
        proof = None
        if onchain_proof:
            proof = onchain_signer.sign_cleanweb_attestation(
                target_url=url,
                content_text=data["markdown_content"]
            )

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
            word_count=data["word_count"],
            estimated_reading_time_sec=data["estimated_reading_time_sec"],
            engine=data.get("engine", "cleanweb_fast_parser"),
            token_analytics=t_obj,
            metadata=meta,
            onchain_proof=proof,
            payment_receipt=receipt,
            auth=receipt.auth if receipt else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape webpage: {str(e)}")


@app.get("/api/v1/clean-youtube", response_model=YouTubeCleanResponse, tags=["Cleaners"])
async def clean_youtube(
    request: Request,
    url: str = Query(..., description="YouTube Video URL"),
    lang: str = Query("ko,en", description="Preferred transcript language codes"),
    onchain_proof: bool = Query(False, description="Whether to generate EIP-712 cryptographic attestation")
):
    tier = PricingTier.ONCHAIN if onchain_proof else PricingTier.HEAVY
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
            auth=receipt.auth if receipt else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process YouTube video: {str(e)}")


@app.get("/api/v1/clean-pdf", response_model=PDFCleanResponse, tags=["Cleaners"])
async def clean_pdf(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")


# Supporting BOTH /api/v1/clean-batch AND /api/v1/batch-clean for 100% compatibility
@app.post("/api/v1/clean-batch", response_model=BatchCleanResponse, tags=["Cleaners"])
@app.post("/api/v1/batch-clean", response_model=BatchCleanResponse, tags=["Cleaners"])
async def clean_batch(request: Request, body: BatchCleanRequest):
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
        raise HTTPException(status_code=500, detail=f"Batch scraping failed: {str(e)}")


# =========================================================================
# 💰 B2A Autonomous Agent Vault & Pass Management Endpoints
# =========================================================================
@app.post("/api/v1/vault/deposit", response_model=VaultBalanceResponse, tags=["Vault"])
async def deposit_vault(body: VaultDepositRequest):
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


@app.get("/api/v1/vault/balance", response_model=VaultBalanceResponse, tags=["Vault"])
async def get_vault_balance(identifier: str = Query(..., description="Agent Wallet Address or Session Key")):
    acc = vault_manager.get_balance(identifier)
    if not acc:
        raise HTTPException(status_code=404, detail="Vault account not found for provided address or key.")
    return vault_manager.to_response(acc)


@app.get("/api/v1/pass-status", response_model=PassStatusResponse, tags=["Vault"])
async def get_pass_status(agent_wallet: str = Query(..., description="Agent Address or Pass Token")):
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
async def oracle_grounding(request: Request, body: OracleGroundingRequest):
    """
    Autonomous Agent Web3 Oracle Grounding Pipeline.
    Performs real-time web search, noise-free extraction, Gemini 3.6 Flash JSON structuring,
    and signs the payload with EIP-712 cryptographic attestation (0.035 USDC).
    """
    tier = PricingTier.ORACLE_GROUNDING

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
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Oracle Grounding failed: {str(e)}")


@app.post("/api/v1/oracle/verify", response_model=OracleVerifyResponse, tags=["Oracle Grounding"])
async def verify_oracle_attestation(body: OracleVerifyRequest, query: str = Query("", description="Original query")):
    """
    Verifies an EIP-712 signed Oracle attestation off-chain.
    """
    is_valid, recovered = onchain_signer.verify_oracle_grounding(
        query=query,
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




# =========================================================================
# 💳 Lemon Squeezy Webhook (Legacy Compatibility)
# =========================================================================
@app.post("/api/v1/webhook/lemonsqueezy", tags=["Webhook"])
async def lemonsqueezy_webhook(request: Request):
    body_bytes = await request.body()
    signature = request.headers.get("X-Signature", "")

    if LEMONSQUEEZY_WEBHOOK_SECRET and signature:
        digest = hmac.new(
            LEMONSQUEEZY_WEBHOOK_SECRET.encode("utf-8"),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(digest, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        data = json.loads(body_bytes.decode("utf-8"))
        event_name = data.get("meta", {}).get("event_name", "")
        
        if event_name == "order_created":
            order_data = data.get("data", {}).get("attributes", {})
            user_email = order_data.get("user_email", "")
            first_item = order_data.get("first_order_item", {})
            variant_name = first_item.get("variant_name", "").lower()
            order_id = str(data.get("data", {}).get("id", ""))

            credits_allocated = 100
            duration = 86400 if ("24h" in variant_name or "day" in variant_name) else 604800
            p_type = "24H_PASS" if duration == 86400 else "100_CREDIT_PASS"
            pass_token = f"pass_{secrets.token_hex(16)}"

            storage_manager.create_pass(
                pass_token=pass_token,
                email=user_email,
                pass_type=p_type,
                duration_sec=duration,
                order_id=order_id,
                credits=credits_allocated
            )
            return {
                "status": "success",
                "message": "Pass created successfully",
                "pass_token": pass_token,
                "credits": credits_allocated,
                "duration_sec": duration,
                "order_id": order_id
            }

        return {"status": "ignored", "event": event_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook processing error: {str(e)}")


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


@app.get("/api/v1/ping", tags=["System"])
async def ping_keepalive():
    """Ultra-low-latency keep-alive endpoint for automated agent health checks and warm instance polling."""
    return {"ping": "pong", "timestamp": time.time()}

