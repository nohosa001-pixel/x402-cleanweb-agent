"""
Pydantic Schemas and Data Models for x402-cleanweb-agent.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class PricingTier(str, Enum):
    LIGHT = "LIGHT"          # Single Web Clean ($0.001 USDC)
    STANDARD = "STANDARD"    # PDF Paper / Batch Clean ($0.005 USDC)
    HEAVY = "HEAVY"          # Gemini AI YouTube Audio Summary ($0.010 USDC)
    ONCHAIN = "ONCHAIN"      # EIP-712 Signed Attestation ($0.020 USDC)


class PaymentMethod(str, Enum):
    USDC_ONCHAIN = "USDC_ONCHAIN"
    VAULT_BALANCE = "VAULT_BALANCE"
    LEMON_SQUEEZY_PASS = "LEMON_SQUEEZY_PASS"
    SANDBOX_FREE_TRIAL = "SANDBOX_FREE_TRIAL"
    DEV_BYPASS = "DEV_BYPASS"


class PaymentChallenge(BaseModel):
    chain: str = "polygon"
    chain_id: int = 137
    recipient_wallet: str
    amount_usdc: str
    token_address: str
    payment_methods_accepted: List[str]
    pass_options: Dict[str, Any]
    vault_deposit_endpoint: str = "/api/v1/vault/deposit"
    free_trial_remaining: Optional[int] = None
    nonce: str
    timestamp: int


class PaymentReceipt(BaseModel):
    receipt_id: str
    tier: PricingTier
    payment_method: PaymentMethod
    payer_address: Optional[str] = None
    tx_hash: Optional[str] = None
    cost_usdc: float
    remaining_vault_balance: Optional[float] = None
    remaining_free_trials: Optional[int] = None
    settled_at: str


class OnChainProof(BaseModel):
    content_hash: str
    target_url: str
    timestamp: int
    oracle_signer: str
    v: int
    r: str
    s: str
    abi_calldata: str


# --- Web Cleaner Schemas ---
class WebCleanResponse(BaseModel):
    status: str = "success"
    url: str
    title: Optional[str] = None
    markdown_content: str
    word_count: int
    estimated_reading_time_sec: int
    onchain_proof: Optional[OnChainProof] = None
    payment_receipt: Optional[PaymentReceipt] = None


# --- YouTube Cleaner Schemas ---
class YouTubeCleanResponse(BaseModel):
    status: str = "success"
    url: str
    video_id: str
    title: Optional[str] = None
    channel: Optional[str] = None
    duration_sec: Optional[int] = None
    method_used: str  # "gemini_3.6_flash_ai", "invidious_subtitles", "youtube_transcript_api", "oembed_fallback"
    transcript: str
    ai_summary: Optional[str] = None
    onchain_proof: Optional[OnChainProof] = None
    payment_receipt: Optional[PaymentReceipt] = None


# --- PDF Cleaner Schemas ---
class PDFCleanResponse(BaseModel):
    status: str = "success"
    url: str
    total_pages: int
    parsed_pages: int
    title: Optional[str] = None
    text_content: str
    word_count: int
    onchain_proof: Optional[OnChainProof] = None
    payment_receipt: Optional[PaymentReceipt] = None


# --- Batch Scrape Schemas ---
class BatchCleanRequest(BaseModel):
    urls: List[str] = Field(..., max_length=10, description="Up to 10 URLs to scrape concurrently")


class BatchCleanItem(BaseModel):
    url: str
    status: str
    title: Optional[str] = None
    markdown_content: Optional[str] = None
    error: Optional[str] = None


class BatchCleanResponse(BaseModel):
    status: str = "success"
    total_requested: int
    total_success: int
    results: List[BatchCleanItem]
    payment_receipt: Optional[PaymentReceipt] = None


# --- Vault Schemas ---
class VaultDepositRequest(BaseModel):
    agent_address: str
    chain: str = "polygon"
    tx_hash: str
    amount_usdc: float


class VaultBalanceResponse(BaseModel):
    agent_address: str
    balance_usdc: float
    total_deposited_usdc: float
    total_consumed_usdc: float
    session_key: str
    last_active_utc: str
    query_count: int


# --- Pass Status Schema ---
class PassStatusResponse(BaseModel):
    agent_wallet_or_token: str
    has_active_pass: bool
    pass_type: Optional[str] = None
    expires_at_utc: Optional[str] = None
    remaining_queries: Optional[int] = None
    vault_balance_usdc: Optional[float] = None
