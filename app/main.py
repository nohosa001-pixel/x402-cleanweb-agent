"""
Main FastAPI Application for x402-cleanweb-agent (CleanWeb Studio).
"""

import os
import hmac
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Request, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

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
)
from app.x402_verifier import x402_verifier
from app.cleaners.web_engine import web_cleaner_engine
from app.cleaners.youtube_engine import youtube_cleaner_engine
from app.cleaners.pdf_engine import pdf_cleaner_engine
from app.onchain_signer import onchain_signer
from app.vault_manager import vault_manager
from app.storage import storage_manager

load_dotenv()

app = FastAPI(
    title="CleanWeb Studio (x402 AI Agent Suite)",
    description="Deterministic Web3 x402 Micropayment MCP & AI Agent Tool Suite with Gemini 3.6 Flash Video Intelligence on Polygon, Base, and Arbitrum.",
    version="2.2.0",
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
        "version": "2.2.0",
        "protocol": "x402 (HTTP 402 Monetized)",
        "networks": ["Polygon (137)", "Base (8453)", "Arbitrum (42161)"],
        "pricing_tiers": {
            "web_clean": "0.001 USDC",
            "pdf_or_batch": "0.005 USDC",
            "youtube_gemini_ai": "0.010 USDC",
            "onchain_attestation": "0.020 USDC"
        },
        "interactive_dashboard": "/dashboard",
        "endpoints": {
            "clean_web": "/api/v1/clean-web?url=https://example.com",
            "clean_youtube": "/api/v1/clean-youtube?url=https://www.youtube.com/watch?v=aircAruvnKk",
            "clean_pdf": "/api/v1/clean-pdf?url=https://example.com/paper.pdf",
            "clean_batch": "/api/v1/clean-batch",
            "vault_deposit": "/api/v1/vault/deposit",
            "vault_balance": "/api/v1/vault/balance",
            "pass_status": "/api/v1/pass-status",
            "ap2_manifest": "/.well-known/ap2",
            "mcp_tools": "/mcp/tools",
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
    return {
        "status": "healthy",
        "service": "x402-cleanweb-agent",
        "version": "2.2.0",
        "storage": "sqlite3_ready",
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

        return WebCleanResponse(
            status="success",
            url=data["url"],
            title=data["title"],
            markdown_content=data["markdown_content"],
            word_count=data["word_count"],
            estimated_reading_time_sec=data["estimated_reading_time_sec"],
            onchain_proof=proof,
            payment_receipt=receipt
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

        return YouTubeCleanResponse(
            status="success",
            url=data["url"],
            video_id=data["video_id"],
            title=data["title"],
            channel=data["channel"],
            duration_sec=data["duration_sec"],
            method_used=data["method_used"],
            transcript=data["transcript"],
            ai_summary=data["ai_summary"],
            onchain_proof=proof,
            payment_receipt=receipt
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

        return PDFCleanResponse(
            status="success",
            url=data["url"],
            total_pages=data["total_pages"],
            parsed_pages=data["parsed_pages"],
            title=data["title"],
            text_content=data["text_content"],
            word_count=data["word_count"],
            onchain_proof=proof,
            payment_receipt=receipt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")


@app.post("/api/v1/clean-batch", response_model=BatchCleanResponse, tags=["Cleaners"])
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
            total_success=success_count,
            results=items,
            payment_receipt=receipt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch scraping failed: {str(e)}")


# =========================================================================
# 💰 Agent Vault & Pass Management Endpoints
# =========================================================================
@app.post("/api/v1/vault/deposit", response_model=VaultBalanceResponse, tags=["Vault"])
async def deposit_vault(body: VaultDepositRequest):
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
    # Check if pass exists
    pass_data = storage_manager.get_pass(agent_wallet)
    vault_data = storage_manager.get_vault(agent_wallet)

    has_pass = pass_data is not None
    pass_type = pass_data["pass_type"] if pass_data else None
    exp_utc = (
        storage_manager._get_conn()  # format
        and pass_data
        and time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(pass_data["expires_at"]))
    ) if pass_data else None

    v_bal = vault_data["balance_usdc"] if vault_data else None

    return PassStatusResponse(
        agent_wallet_or_token=agent_wallet,
        has_active_pass=has_pass,
        pass_type=pass_type,
        expires_at_utc=exp_utc,
        vault_balance_usdc=v_bal
    )


# =========================================================================
# 💳 Lemon Squeezy Webhook (Fiat / Credit Card Pass Issuance)
# =========================================================================
@app.post("/api/v1/webhook/lemonsqueezy", tags=["Webhook"])
async def lemonsqueezy_webhook(request: Request):
    body_bytes = await request.body()
    signature = request.headers.get("X-Signature", "")

    if LEMONSQUEEZY_WEBHOOK_SECRET:
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

            duration = 86400 if "24h" in variant_name or "day" in variant_name else 604800
            p_type = "24H_PASS" if duration == 86400 else "7D_UNLIMITED"
            pass_token = f"pass_{secrets.token_hex(16)}"

            storage_manager.create_pass(
                pass_token=pass_token,
                email=user_email,
                pass_type=p_type,
                duration_sec=duration,
                order_id=order_id
            )
            return {"status": "success", "message": "Pass created", "pass_token": pass_token}

        return {"status": "ignored", "event": event_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook processing error: {str(e)}")
