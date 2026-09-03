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
    ORACLE_GROUNDING = "ORACLE_GROUNDING"  # Agent Search + Clean JSON + EIP-712 Signed Oracle ($0.035 USDC)


class PaymentMethod(str, Enum):
    USDC_ONCHAIN = "USDC_ONCHAIN"
    VAULT_BALANCE = "VAULT_BALANCE"
    STRIPE_PASS = "STRIPE_PASS"
    STRIPE_VAULT_TOPUP = "STRIPE_VAULT_TOPUP"
    LEMON_SQUEEZY_PASS = "LEMON_SQUEEZY_PASS"  # Legacy compatibility
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
    remaining_credits: Optional[int] = None
    settled_at: str
    auth: Optional[Dict[str, Any]] = None


class OnChainProof(BaseModel):
    content_hash: str
    target_url: str
    timestamp: int
    oracle_signer: str
    v: int
    r: str
    s: str
    abi_calldata: str


# --- Universal Analytics & Metadata ---
class TokenAnalytics(BaseModel):
    raw_html_estimated_tokens: Optional[int] = None
    clean_markdown_estimated_tokens: int = 0
    token_reduction_percent: Optional[float] = None
    saved_tokens: Optional[int] = None


class ScrapeMetadata(BaseModel):
    engine: str = "default"
    latency_ms: Optional[float] = None
    status_code: int = 200
    timestamp_utc: Optional[str] = None


# --- Web Cleaner Schemas ---
class WebCleanResponse(BaseModel):
    status: str = "success"
    url: str
    title: Optional[str] = None
    markdown_content: str
    word_count: int
    estimated_reading_time_sec: int
    engine: Optional[str] = "cleanweb_fast_parser"
    token_analytics: Optional[TokenAnalytics] = None
    metadata: Optional[ScrapeMetadata] = None
    onchain_proof: Optional[OnChainProof] = None
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None


# --- YouTube Cleaner Schemas ---
class YouTubeCleanResponse(BaseModel):
    status: str = "success"
    url: str
    video_id: str
    title: Optional[str] = None
    channel: Optional[str] = None
    duration_sec: Optional[int] = None
    method_used: str  # "gemini_3.6_flash_ai", "invidious_subtitles", "youtube_transcript_api", "oembed_fallback"
    engine: Optional[str] = "hybrid_video_intelligence"
    transcript: str
    ai_summary: Optional[str] = None
    token_analytics: Optional[TokenAnalytics] = None
    onchain_proof: Optional[OnChainProof] = None
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None


# --- PDF Cleaner Schemas ---
class PDFAnalytics(BaseModel):
    total_pages: int
    parsed_pages: int
    word_count: int
    estimated_tokens: int


class PDFCleanResponse(BaseModel):
    status: str = "success"
    url: str
    total_pages: int
    parsed_pages: int
    title: Optional[str] = None
    text_content: str
    word_count: int
    engine: Optional[str] = "pypdf_stream_parser"
    pdf_analytics: Optional[PDFAnalytics] = None
    token_analytics: Optional[TokenAnalytics] = None
    onchain_proof: Optional[OnChainProof] = None
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None


# --- Batch Scrape Schemas ---
class BatchCleanRequest(BaseModel):
    urls: List[str] = Field(..., max_length=10, description="Up to 10 URLs to scrape concurrently")
    density: Optional[str] = "standard"


class BatchCleanItem(BaseModel):
    url: str
    status: str
    title: Optional[str] = None
    markdown_content: Optional[str] = None
    word_count: Optional[int] = None
    token_analytics: Optional[TokenAnalytics] = None
    error: Optional[str] = None


class BatchCleanResponse(BaseModel):
    status: str = "success"
    total_requested: int
    total_urls: Optional[int] = None
    total_success: int
    successful_count: Optional[int] = None
    results: List[BatchCleanItem]
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None


# --- Vault Schemas ---
class VaultDepositRequest(BaseModel):
    agent_address: str
    chain: str = "polygon"
    tx_hash: str
    amount_usdc: float = Field(..., ge=2.0, le=1000.0, description="Deposit amount must be between 2.0 and 1000.0 USDC")


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
    remaining_credits: Optional[int] = None
    credits: Optional[int] = None
    vault_balance_usdc: Optional[float] = None


# --- Oracle Grounding Schemas ---
class OracleGroundingRequest(BaseModel):
    query: str = Field(..., description="Natural language search or research query")
    target_schema: Optional[Dict[str, Any]] = Field(None, description="Optional target JSON schema to constrain output")
    max_sources: int = Field(3, ge=1, le=5, description="Number of top web sources to synthesize")


class OracleAttestation(BaseModel):
    query: str
    data_hash: str
    timestamp: int
    oracle_signer: str
    v: int
    r: str
    s: str
    signature: str
    domain_chain_id: int


class OracleGroundingResponse(BaseModel):
    status: str = "success"
    query: str
    structured_data: Dict[str, Any]
    summary_markdown: str
    source_urls: List[str]
    oracle_attestation: OracleAttestation
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None


class OracleVerifyRequest(BaseModel):
    data_hash: str
    timestamp: int
    signature: str
    oracle_signer: Optional[str] = None


class OracleVerifyResponse(BaseModel):
    valid: bool
    recovered_signer: str
    expected_signer: str
    timestamp_utc: str
    message: str

