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
    MAP_SITE = "MAP_SITE"                  # Domain Sitemap & URL Tree Discovery ($0.002 USDC)
    SEARCH = "SEARCH"                      # Fast Agent Web Search & Snippets ($0.002 USDC)
    EXTRACT_JSON = "EXTRACT_JSON"          # Structured JSON schema extraction ($0.030 USDC)
    DEEP_RESEARCH = "DEEP_RESEARCH"        # Multi-source AI deep research ($0.150 USDC)
    SECURE_WEB_CLEAN = "SECURE_WEB_CLEAN"  # Web Clean + Security Gate AST/Prompt Audit ($0.005 USDC)
    SECURE_YOUTUBE_CLEAN = "SECURE_YOUTUBE_CLEAN"  # YouTube AI + Security Gate Audit ($0.015 USDC)
    SECURE_ORACLE_GROUNDING = "SECURE_ORACLE_GROUNDING"  # Oracle + Dual Security Gate Attestation ($0.040 USDC)


class PaymentMethod(str, Enum):
    USDC_ONCHAIN = "USDC_ONCHAIN"
    VAULT_BALANCE = "VAULT_BALANCE"
    SANDBOX_FREE_TRIAL = "SANDBOX_FREE_TRIAL"
    DEV_BYPASS = "DEV_BYPASS"


class SecurityAuditResult(BaseModel):
    enabled: bool = True
    status: str = "success"
    latency_ms: float = 0.0
    is_safe: bool = True
    verdict: str = "PASSED"
    risk_score: float = 0.0
    threats: List[str] = []
    attestation: Optional[Dict[str, Any]] = None
    payment_settled_usdc: Optional[str] = None


class SecurityInspectRequest(BaseModel):
    text: str = Field(..., description="Content or Python code to inspect")
    is_code: bool = Field(False, description="True if inspecting Python code AST, False for natural language/prompts")


class PaymentChallenge(BaseModel):
    protocol: str = "B2A_USDC_M2M"
    instructions: str = "Autonomous Agent Zone: Deposit 2.0+ USDC to recipient_wallet via Polygon/Base/Arbitrum or supply X-Vault-Key header."
    chain: str = "polygon"
    chain_id: int = 137
    recipient: Optional[str] = None
    recipient_wallet: str
    amount_usdc: str
    token_address: str
    payment_methods_accepted: List[str]
    networks: Optional[List[Dict[str, Any]]] = None
    pass_options: Dict[str, Any]
    vault_deposit_endpoint: str = "/api/v1/vault/deposit"
    min_deposit_usdc: float = 2.0
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
    remaining_trial_calls: Optional[int] = None
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
class CleanWebRequest(BaseModel):
    url: str = Field(..., description="Target webpage URL to scrape and convert to markdown")
    density: Optional[str] = Field("standard", description="Markdown density level ('standard', 'dense', 'light')")
    max_tokens: Optional[int] = Field(None, description="Max token limit for output markdown to prevent LLM context overflow")
    onchain_proof: bool = Field(False, description="Whether to generate EIP-712 cryptographic attestation")
    secure_audit: bool = Field(False, description="Run real-time AST, prompt injection, and EIP-712 security audit")
    respect_robots_txt: bool = Field(False, description="Whether to enforce target domain robots.txt compliance")


class WebCleanResponse(BaseModel):
    status: str = "success"
    url: str
    title: Optional[str] = None
    markdown_content: str
    content: Optional[str] = Field(None, description="Backward-compatibility alias for autonomous agents (equivalent to markdown_content)")
    word_count: int
    estimated_reading_time_sec: int
    engine: Optional[str] = "cleanweb_fast_parser"
    token_analytics: Optional[TokenAnalytics] = None
    metadata: Optional[ScrapeMetadata] = None
    onchain_proof: Optional[OnChainProof] = None
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None
    security_audit: Optional[SecurityAuditResult] = None


# --- YouTube Cleaner Schemas ---
class CleanYouTubeRequest(BaseModel):
    url: str = Field(..., description="Target YouTube video URL")
    lang: Optional[str] = Field("ko,en", description="Comma-separated language priority codes")
    onchain_proof: bool = Field(False, description="Whether to generate EIP-712 cryptographic attestation")
    secure_audit: bool = Field(False, description="Run real-time security audit")


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
    security_audit: Optional[SecurityAuditResult] = None


# --- PDF Cleaner Schemas ---
class CleanPDFRequest(BaseModel):
    url: str = Field(..., description="Direct HTTP/HTTPS URL pointing to an online PDF")
    max_pages: Optional[int] = Field(30, ge=1, le=100, description="Max pages to parse")
    onchain_proof: bool = Field(False, description="Whether to generate EIP-712 cryptographic attestation")


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
    security_audit: Optional[SecurityAuditResult] = None


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
    secure_audit: bool = Field(False, description="Whether to run dual EIP-712 security audit via Security Gate Agent")


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
    abi_calldata: Optional[str] = None


class OracleGroundingResponse(BaseModel):
    status: str = "success"
    query: str
    structured_data: Dict[str, Any]
    summary_markdown: str
    source_urls: List[str]
    oracle_attestation: OracleAttestation
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None
    security_audit: Optional[SecurityAuditResult] = None


class OracleVerifyRequest(BaseModel):
    query: Optional[str] = None
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


# --- Text Cleaner Schemas ---
class TextCleanResponse(BaseModel):
    status: str = "success"
    url: str
    title: Optional[str] = None
    plain_text: str
    word_count: int
    token_analytics: Optional[TokenAnalytics] = None
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None


# --- Structured JSON Extraction Schemas ---
class ExtractJsonRequest(BaseModel):
    url: str = Field(..., description="Target webpage URL to extract JSON from")
    schema_description: str = Field(..., description="Description or schema format of the desired JSON fields")


class ExtractJsonResponse(BaseModel):
    status: str = "success"
    url: str
    extracted_json: Dict[str, Any]
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None


# --- Deep Research Schemas ---
class DeepResearchResponse(BaseModel):
    status: str = "success"
    query: str
    research_brief_markdown: str
    sources: List[str]
    structured_data: Optional[Dict[str, Any]] = None
    oracle_attestation: Optional[OracleAttestation] = None
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None


# --- Site Mapping Schemas ---
class SiteMapRequest(BaseModel):
    url: str = Field(..., description="Target website domain or URL to map")
    max_links: Optional[int] = Field(50, ge=5, le=100, description="Max URLs to discover")


class SiteMapResponse(BaseModel):
    status: str = "success"
    url: str
    domain: str
    total_urls: int
    urls: List[str]
    sitemap_detected: bool = False
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None


# --- Fast Agent Web Search Schemas ---
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search keyword or question for agent")
    max_results: Optional[int] = Field(5, ge=1, le=10, description="Max search results")


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str


class SearchResponse(BaseModel):
    status: str = "success"
    query: str
    total_results: int
    results: List[SearchResultItem]
    payment_receipt: Optional[PaymentReceipt] = None
    auth: Optional[Dict[str, Any]] = None


