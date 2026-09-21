"""
Model Context Protocol (MCP) Server for CleanWeb Studio.
Supports Multi-Chain (Polygon/Base/Arbitrum) USDC Micropayments and Free Tier for Claude Desktop, Cursor, and Agentic Clients.
"""

import os
import sys
import time

# Force UTF-8 stdio encoding on Windows to prevent UnicodeEncodeError in MCP JSON-RPC pipes
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

from typing import Optional, List
from mcp.server import MCPServer
from dotenv import load_dotenv

from app.cleaners.web_engine import web_cleaner_engine
from app.cleaners.youtube_engine import youtube_cleaner_engine
from app.cleaners.pdf_engine import pdf_cleaner_engine
from app.onchain_signer import onchain_signer
from app.multi_chain import multi_chain_manager
from app.vault_manager import vault_manager
from app.storage import storage_manager
from app.oracle_engine import oracle_engine

load_dotenv(override=True)

# MCP Server Initialization
mcp = MCPServer(
    name="x402-cleanweb-agent",
    version="2.6.0",
    description="Deterministic Web3 x402 Micropayment MCP Suite for Web, YouTube Gemini AI, and PDF Papers on Polygon, Base, and Arbitrum."
)


from pydantic import Field


def _coerce_val(val, default_val):
    """Safely extracts default from Pydantic FieldInfo if invoked directly in Python."""
    if hasattr(val, "default") and val.default is not ...:
        return val.default
    if type(val) is type(default_val):
        return val
    return default_val

@mcp.tool(
    name="get_payment_info",
    description=(
        "Returns complete Web3 x402 micropayment configuration, supported multi-chain USDC contract addresses, "
        "EVM network chain IDs (Polygon: 137, Base: 8453, Arbitrum: 42161), recipient wallet address, "
        "and pricing tiers for all CleanWeb Studio agent tools.\n\n"
        "Usage Guidelines:\n"
        "- Use this tool to discover network parameters and deposit requirements before making x402 paid queries.\n"
        "- Returns: Structured pricing markdown table, contract addresses, and pre-funded vault endpoints.\n"
        "- Do NOT use for checking individual wallet balances (use `get_vault_balance`)."
    )
)
def get_payment_info(
    tier: Optional[str] = Field(default=None, description="Optional specific pricing tier to inspect."),
    chain: Optional[str] = Field(default=None, description="Optional specific chain name (polygon, base, arbitrum).")
) -> str:
    poly_cfg = multi_chain_manager.get_chain_config("polygon")
    base_cfg = multi_chain_manager.get_chain_config("base")
    arb_cfg = multi_chain_manager.get_chain_config("arbitrum")
    
    return f"""### 💳 CleanWeb Studio x402 Micropayment Architecture
- **Supported Networks**:
  1. **Polygon (Chain ID: 137)**: USDC `{poly_cfg.usdc_address}`
  2. **Base (Chain ID: 8453)**: USDC `{base_cfg.usdc_address}`
  3. **Arbitrum One (Chain ID: 42161)**: USDC `{arb_cfg.usdc_address}`
- **Recipient Wallet Address**: `{multi_chain_manager.default_recipient}`

**Pricing Tiers (USDC per call)**:
- `clean_web_content`: **0.001 USDC** (Markdown web extraction & noise stripping)
- `clean_text_raw`: **0.001 USDC** (Raw plain text for vector/RAG embeddings)
- `map_site`: **0.002 USDC** (Domain sitemap & internal URL tree discovery)
- `search_web_quick`: **0.002 USDC** (Fast real-time agent web search & snippets)
- `clean_youtube_transcript`: **0.010 USDC** (Gemini AI intelligence & full transcript)
- `clean_pdf_research`: **0.005 USDC** (PDF papers & whitepapers, up to 100 pages)
- `clean_batch_scrape`: **0.005 USDC** (Concurrent parallel batch scrape up to 10 URLs)
- `oracle_grounding`: **0.035 USDC** (Search + Clean-to-JSON + EIP-712 Signed Oracle)
- `extract_json_schema`: **0.030 USDC** (Webpage to structured JSON schema extractor)
- `deep_research_topic`: **0.150 USDC** (Multi-source synthesized AI executive briefing)
- `Pre-funded Vault`: Deposit once, execute queries with zero latency (<1ms)
"""


@mcp.tool(
    name="clean_web_content",
    description=(
        "Scrapes and converts any target web page into clean, LLM-ready structured Markdown, stripping ads, "
        "cookie banners, navigation clutter, modals, and script noise.\n\n"
        "Usage Guidelines:\n"
        "- Use this tool to ingest real-time web articles, blogs, and documentation into LLM context windows.\n"
        "- Returns: Clean markdown body, page title, word count, and extraction metadata.\n"
        "- Do NOT use for YouTube video parsing (use `clean_youtube_transcript`).\n"
        "- Do NOT use for PDF whitepapers or academic papers (use `clean_pdf_research`).\n"
        "- Do NOT use for paywalled, login-required, or bot-blocked sites."
    )
)
def clean_web_content(
    url: str = Field(
        ...,
        description="The target HTTP or HTTPS website URL to scrape and convert to markdown.",
        examples=["https://en.wikipedia.org/wiki/Web_scraping", "https://news.ycombinator.com/"],
        pattern=r"^https?:\/\/[^\s/$.?#].[^\s]*$"
    ),
    auth_token_or_tx: Optional[str] = Field(
        default=None,
        description="Optional x402 micropayment authorization token or EVM transaction hash."
    ),
    respect_robots_txt: bool = Field(
        default=False,
        description="Whether to enforce target domain robots.txt Disallow rules (compliance-mode)."
    )
) -> str:
    respect_robots_txt = _coerce_val(respect_robots_txt, False)
    try:
        data = web_cleaner_engine.fetch_and_clean(url, respect_robots_txt=respect_robots_txt)
        return f"✅ [CLEAN WEB SUCCESS]\n\n# {data['title']}\n\n{data['markdown_content']}"
    except Exception as e:
        return f"❌ [FETCH ERROR]: {str(e)}"


@mcp.tool(
    name="clean_youtube_transcript",
    description=(
        "Extracts high-precision subtitles, timestamped transcripts, and comprehensive AI summaries for public YouTube videos "
        "using Google Gemini Flash intelligence.\n\n"
        "Usage Guidelines:\n"
        "- Use this tool to ingest YouTube lecture, tutorial, tech talk, or podcast transcripts into agent workflows.\n"
        "- Returns: Video metadata (title, channel, URL), AI Knowledge Summary, and cleaned transcript.\n"
        "- Do NOT use for general web pages or articles (use `clean_web_content`).\n"
        "- Do NOT use for PDF documents or papers (use `clean_pdf_research`).\n"
        "- Do NOT use for private, unlisted, age-restricted, or live streams without existing closed captions.\n"
        "- If captions are missing or auto-captions fail, the tool reports a detailed fallback error."
    )
)
def clean_youtube_transcript(
    url: str = Field(
        ...,
        description="Public YouTube video URL (standard watch, short youtu.be, or Shorts format).",
        examples=[
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/abcdef12345"
        ],
        pattern=r"^https?:\/\/(www\.)?(youtube\.com\/(watch\?v=|shorts\/)|youtu\.be\/)[\w-]+.*$"
    ),
    lang: str = Field(
        default="ko,en",
        description="Comma-separated ISO 639-1 language priority codes for transcript extraction (e.g., 'ko,en', 'en', 'ja').",
        examples=["ko,en", "en", "ja,en"],
        pattern=r"^[a-z]{2}(,[a-z]{2})*$"
    ),
    auth_token_or_tx: Optional[str] = Field(
        default=None,
        description="Optional x402 micropayment authorization token or EVM transaction hash."
    )
) -> str:
    lang = _coerce_val(lang, "ko,en")
    try:
        data = youtube_cleaner_engine.clean_youtube(url, lang=lang)
        return (
            f"✅ [YOUTUBE CLEAN SUCCESS - Method: {data['method_used']}]\n\n"
            f"# 🎬 {data['title']}\n"
            f"> Channel: {data['channel']} | URL: {data['url']}\n\n"
            f"## 💡 AI Knowledge Summary\n{data['ai_summary']}\n\n"
            f"## 📜 Transcript\n{data['transcript'][:4000]}"
        )
    except Exception as e:
        return f"❌ [YOUTUBE ERROR]: {str(e)}"


@mcp.tool(
    name="clean_pdf_research",
    description=(
        "Parses and extracts structured plain text, sections, and academic metadata from online PDF whitepapers and research papers.\n\n"
        "Usage Guidelines:\n"
        "- Use this tool to ingest scientific papers (e.g., arXiv), technical documentation, or financial reports.\n"
        "- Constraint: Target document must be a direct HTTP/HTTPS URL pointing to a PDF file under 15MB.\n"
        "- Returns: Title, total/parsed page count, word count, and extracted text.\n"
        "- Do NOT use for general HTML web pages (use `clean_web_content`).\n"
        "- Do NOT use for YouTube videos (use `clean_youtube_transcript`).\n"
        "- Do NOT use for password-protected, DRM-encrypted, or scanned image-only PDFs without OCR."
    )
)
def clean_pdf_research(
    url: str = Field(
        ...,
        description="Direct HTTP/HTTPS URL pointing to an online PDF document.",
        examples=[
            "https://arxiv.org/pdf/1706.03762.pdf",
            "https://bitcoin.org/bitcoin.pdf"
        ],
        pattern=r"^https?:\/\/[^\s/$.?#].[^\s]*\.pdf(\?.*)?$"
    ),
    max_pages: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Maximum number of pages to parse (1 to 100, default: 30) to control token budget."
    ),
    auth_token_or_tx: Optional[str] = Field(
        default=None,
        description="Optional x402 micropayment authorization token or EVM transaction hash."
    )
) -> str:
    max_pages = _coerce_val(max_pages, 30)
    try:
        data = pdf_cleaner_engine.clean_pdf(url, max_pages=max_pages)
        return (
            f"✅ [PDF CLEAN SUCCESS]\n\n"
            f"# 📄 {data['title']}\n"
            f"> Total Pages: {data['total_pages']} (Parsed: {data['parsed_pages']}) | Word Count: {data['word_count']}\n\n"
            f"{data['text_content'][:5000]}"
        )
    except Exception as e:
        return f"❌ [PDF ERROR]: {str(e)}"


@mcp.tool(
    name="get_vault_balance",
    description=(
        "Checks the remaining pre-funded USDC balance, total usage, and session status for an agent wallet address or session key.\n\n"
        "Usage Guidelines:\n"
        "- Use this tool before executing heavy tasks to verify sufficient balance for zero-latency execution.\n"
        "- Returns: Agent address, available balance in USDC, total deposited, total consumed, queries handled, and session key.\n"
        "- Do NOT use for querying pricing or chain parameters (use `get_payment_info`)."
    )
)
def get_vault_balance(
    agent_address_or_key: str = Field(
        ...,
        description="Ethereum/Polygon address (0x...) or session key (sk_...) to query balance for.",
        examples=["0x71C...397", "sk_cleanweb_agent_01"],
        pattern=r"^(0x[a-fA-F0-9]{40}|sk_[a-zA-Z0-9_-]+)$"
    )
) -> str:
    acc = vault_manager.get_balance(agent_address_or_key)
    if not acc:
        return f"⚠️ Vault account not found for '{agent_address_or_key}'. You can create one via POST /api/v1/vault/deposit"
    return (
        f"💳 [VAULT BALANCE REPORT]\n"
        f"- **Agent Address**: `{acc['agent_address']}`\n"
        f"- **Available Balance**: **${acc['balance_usdc']:.4f} USDC**\n"
        f"- **Total Deposited**: ${acc['total_deposited']:.4f} USDC\n"
        f"- **Total Consumed**: ${acc['total_consumed']:.4f} USDC\n"
        f"- **Queries Handled**: {acc.get('query_count', 0)}\n"
        f"- **Session Key**: `{acc.get('session_key')}`"
    )


@mcp.tool(
    name="oracle_grounding",
    description=(
        "Executes real-time web search, noise-free markdown extraction, Gemini AI JSON structuring, "
        "and cryptographically signs the result with an on-chain verifiable EIP-712 attestation (0.035 USDC).\n\n"
        "Usage Guidelines:\n"
        "- Use this tool when an autonomous agent or smart contract requires verified, tamper-proof ground truth from the live web.\n"
        "- Returns: Structured facts JSON, human/LLM readable summary markdown, source URLs, and EIP-712 cryptographic signature (v, r, s).\n"
        "- Smart contracts can verify this off-chain or on-chain using CleanWebOracleVerifier.sol."
    )
)
def oracle_grounding(
    query: str = Field(
        ...,
        description="Search topic or question to ground with live web sources (e.g., 'Latest Fed interest rate decision')."
    ),
    target_schema_json: Optional[str] = Field(
        default=None,
        description="Optional JSON string defining the expected schema or fields (e.g., '{\"rate\": \"float\", \"date\": \"string\"}')."
    ),
    max_sources: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of web sources to synthesize (1 to 5, default: 3)."
    ),
    auth_token_or_tx: Optional[str] = Field(
        default=None,
        description="Optional x402 micropayment authorization token or EVM transaction hash."
    )
) -> str:
    max_sources = _coerce_val(max_sources, 3)
    try:
        schema_dict = None
        if target_schema_json:
            try:
                import json
                schema_dict = json.loads(target_schema_json)
            except Exception:
                schema_dict = None

        res = oracle_engine.execute_grounding(
            query=query,
            target_schema=schema_dict,
            max_sources=max_sources
        )

        import json
        att = res.oracle_attestation
        return (
            f"✅ [ORACLE GROUNDING SUCCESS]\n\n"
            f"### 🔮 Query: {res.query}\n\n"
            f"{res.summary_markdown}\n\n"
            f"### 📊 Structured JSON Data\n```json\n{json.dumps(res.structured_data, indent=2, ensure_ascii=False)}\n```\n\n"
            f"### 🛡️ EIP-712 Cryptographic Attestation\n"
            f"- **Data Hash**: `{att.data_hash}`\n"
            f"- **Signer**: `{att.oracle_signer}`\n"
            f"- **Timestamp**: `{att.timestamp}`\n"
            f"- **Signature**: `{att.signature}`\n"
            f"- **ABI Calldata**: `{att.abi_calldata or 'N/A'}`\n"
            f"- **Sources**: {', '.join(res.source_urls)}"
        )
    except Exception as e:
        return f"❌ [ORACLE ERROR]: {str(e)}"


@mcp.tool(
    name="verify_oracle_attestation",
    description=(
        "Verifies an EIP-712 cryptographic attestation produced by CleanWeb Oracle off-chain without consuming gas.\n\n"
        "Usage Guidelines:\n"
        "- Use this tool to mathematically verify that data received from CleanWeb Oracle has not been tampered with.\n"
        "- Returns: Verification status (valid/invalid), recovered signer address, expected oracle address, and message."
    )
)
def verify_oracle_attestation(
    query: str = Field(..., description="The original query string that was attested."),
    data_hash: str = Field(..., description="The SHA-256 data hash of the canonical JSON payload (0x...)."),
    timestamp: int = Field(..., description="The Unix epoch timestamp from the attestation."),
    signature: str = Field(..., description="The 65-byte hex signature (0x...) from the attestation.")
) -> str:
    try:
        is_valid, recovered = onchain_signer.verify_oracle_grounding(
            query=query,
            data_hash=data_hash,
            timestamp=timestamp,
            signature=signature
        )
        status_icon = "✅ VALID" if is_valid else "❌ INVALID"
        return (
            f"🛡️ [ORACLE ATTESTATION VERIFICATION - {status_icon}]\n"
            f"- **Valid**: {is_valid}\n"
            f"- **Recovered Signer**: `{recovered}`\n"
            f"- **Expected Oracle**: `{onchain_signer.signer_address}`\n"
            f"- **Timestamp**: {timestamp}\n"
            f"- **Result**: {'Signature matches CleanWeb Master Oracle' if is_valid else 'SIGNATURE MISMATCH / TAMPERED'}"
        )
    except Exception as e:
        return f"❌ [VERIFICATION ERROR]: {str(e)}"


@mcp.tool(
    name="clean_text_raw",
    description=(
        "Extracts pure, tag-free plain text optimized for RAG embedding and vector indexing (0.001 USDC).\n\n"
        "Usage Guidelines:\n"
        "- Use this tool when ingesting raw webpage text directly into vector databases (Pinecone, Chroma, Qdrant).\n"
        "- Returns: Page title, word count, clean text, and token metrics."
    )
)
def clean_text_raw(
    url: str = Field(..., description="The target website URL to extract raw text from."),
    auth_token_or_tx: Optional[str] = Field(default=None, description="Optional x402 auth token or tx hash.")
) -> str:
    try:
        data = web_cleaner_engine.fetch_plain_text(url)
        return (
            f"✅ [RAW TEXT SUCCESS]\n\n"
            f"# {data['title']}\n"
            f"> Word Count: {data['word_count']} | URL: {data['url']}\n\n"
            f"{data['plain_text'][:5000]}"
        )
    except Exception as e:
        return f"❌ [RAW TEXT ERROR]: {str(e)}"


@mcp.tool(
    name="map_site",
    description=(
        "Discovers domain sitemap or traverses internal anchor links to return a canonical URL tree (0.002 USDC).\n\n"
        "Usage Guidelines:\n"
        "- Use this tool to map an entire website or documentation site before scraping.\n"
        "- Firecrawl /map equivalent for autonomous web navigation agents.\n"
        "- Returns: Target URL, domain, total URL count, list of discovered URLs, and sitemap detection status."
    )
)
def map_site(
    url: str = Field(..., description="Target website domain or URL to map (e.g., 'https://docs.github.com' or 'example.com')."),
    max_links: int = Field(default=50, ge=5, le=100, description="Maximum internal URLs to discover (default: 50, max: 100)."),
    auth_token_or_tx: Optional[str] = Field(default=None, description="Optional x402 auth token or tx hash.")
) -> str:
    max_links = _coerce_val(max_links, 50)
    try:
        data = web_cleaner_engine.map_website(url, max_links=max_links)
        urls_preview = "\n".join(f"- {u}" for u in data["urls"][:25])
        remaining = data["total_urls"] - 25
        more_text = f"\n... and {remaining} more URLs" if remaining > 0 else ""
        return (
            f"🗺️ [SITE MAP SUCCESS]\n\n"
            f"- **Target URL**: {data['url']}\n"
            f"- **Domain**: `{data['domain']}`\n"
            f"- **Total URLs Discovered**: {data['total_urls']}\n"
            f"- **Sitemap.xml Detected**: {data['sitemap_detected']}\n\n"
            f"### Discovered URL Tree:\n"
            f"{urls_preview}{more_text}"
        )
    except Exception as e:
        return f"❌ [SITE MAP ERROR]: {str(e)}"


@mcp.tool(
    name="search_web_quick",
    description=(
        "Performs fast real-time keyword web search returning titles, links, and text snippets (0.002 USDC).\n\n"
        "Usage Guidelines:\n"
        "- Tavily / s.jina.ai competitor designed specifically for LLM autonomous agent retrieval.\n"
        "- Returns: Concise search result list with title, verified URL, and text snippet."
    )
)
def search_web_quick(
    query: str = Field(..., description="Search query or keyword for real-time web discovery."),
    max_results: int = Field(default=5, ge=1, le=10, description="Maximum results to return (default: 5, max: 10)."),
    auth_token_or_tx: Optional[str] = Field(default=None, description="Optional x402 auth token or tx hash.")
) -> str:
    max_results = _coerce_val(max_results, 5)
    try:
        results = oracle_engine.quick_search(query, max_results=max_results)
        items_md = []
        for i, item in enumerate(results, 1):
            items_md.append(f"{i}. **[{item['title']}]({item['url']})**\n   > {item['snippet']}")
        return (
            f"🔍 [SEARCH SUCCESS]\n\n"
            f"### Query: `{query}` (Total Results: {len(results)})\n\n"
            + "\n\n".join(items_md)
        )
    except Exception as e:
        return f"❌ [SEARCH ERROR]: {str(e)}"


@mcp.tool(
    name="extract_json_schema",
    description=(
        "Extracts schema-constrained structured JSON data from any webpage using Gemini AI (0.030 USDC).\n\n"
        "Usage Guidelines:\n"
        "- Use when an agent needs structured attributes (e.g. pricing, specs, event dates) directly from a URL.\n"
        "- Returns: Clean JSON dictionary matching the requested schema description."
    )
)
def extract_json_schema(
    url: str = Field(..., description="Target webpage URL to extract JSON from."),
    schema_description: str = Field(..., description="Description or format of the fields to extract (e.g., 'price, product_name, in_stock')."),
    auth_token_or_tx: Optional[str] = Field(default=None, description="Optional x402 auth token or tx hash.")
) -> str:
    try:
        import json
        extracted = oracle_engine.extract_json_from_webpage(url, schema_description)
        return (
            f"📊 [JSON EXTRACTION SUCCESS]\n\n"
            f"**URL**: {url}\n\n"
            f"```json\n{json.dumps(extracted, indent=2, ensure_ascii=False)}\n```"
        )
    except Exception as e:
        return f"❌ [JSON EXTRACTION ERROR]: {str(e)}"


@mcp.tool(
    name="deep_research_topic",
    description=(
        "Performs multi-source web crawling and AI synthesis to generate an executive research briefing (0.150 USDC).\n\n"
        "Usage Guidelines:\n"
        "- Use when an agent needs a comprehensive deep dive into a topic with verified source citations.\n"
        "- Returns: Full executive briefing markdown with source citations and key takeaways."
    )
)
def deep_research_topic(
    query: str = Field(..., description="Research topic or complex question to investigate."),
    max_sources: int = Field(default=3, ge=1, le=5, description="Number of top web sources to synthesize (1 to 5)."),
    auth_token_or_tx: Optional[str] = Field(default=None, description="Optional x402 auth token or tx hash.")
) -> str:
    max_sources = _coerce_val(max_sources, 3)
    try:
        res = oracle_engine.execute_deep_research(query, max_sources=max_sources)
        sources_list = "\n".join(f"- {s}" for s in res.get("sources", []))
        return (
            f"🧠 [DEEP RESEARCH SUCCESS]\n\n"
            f"### Topic: `{res.get('query', query)}`\n\n"
            f"{res.get('research_brief_markdown', '')}\n\n"
            f"### 🌐 Sources Synthesized:\n{sources_list}"
        )
    except Exception as e:
        return f"❌ [DEEP RESEARCH ERROR]: {str(e)}"


@mcp.tool(
    name="clean_batch_scrape",
    description=(
        "Concurrently scrapes and extracts clean markdown from up to 10 URLs in parallel with high-speed async processing (0.005 USDC).\n\n"
        "Usage Guidelines:\n"
        "- Use when an agent needs to perform multi-source research across multiple search results simultaneously.\n"
        "- Returns: Formatted summary and content preview of parsed web documents."
    )
)
def clean_batch_scrape(
    urls: List[str] = Field(..., description="List of target URLs to scrape in parallel (up to 10)."),
    auth_token_or_tx: Optional[str] = Field(default=None, description="Optional x402 auth token, vault key, or tx hash.")
) -> str:
    try:
        if len(urls) > 10:
            urls = urls[:10]
        results = web_cleaner_engine.batch_clean(urls)
        summary = f"📦 [BATCH CLEAN SUCCESS] Parsed {len(results)} URLs concurrently:\n\n"
        for idx, r in enumerate(results, 1):
            status = r.get("status", "unknown")
            url = r.get("url", "")
            title = r.get("title", "Untitled")
            content = r.get("markdown_content", "")[:300]
            summary += f"### {idx}. [{title}]({url}) (Status: {status})\n{content}...\n\n"
        return summary
    except Exception as e:
        return f"❌ [BATCH CLEAN ERROR]: {str(e)}"


@mcp.tool(
    name="get_pass_status",
    description=(
        "Checks the active subscription status, remaining query quota, and validity period for an agent EVM wallet address (0x...) or Agent VIP Pass Token.\n\n"
        "Usage Guidelines:\n"
        "- Use to verify micropayment allowance or query entitlements before dispatching heavy scrape batches.\n"
        "- Returns: Pass tier, remaining balance, and expiration timestamp."
    )
)
def get_pass_status(
    agent_wallet_or_token: str = Field(..., description="Agent EVM wallet address (0x...) or Pass Token (e.g. 'WELCOME100').")
) -> str:
    try:
        pass_data = storage_manager.get_pass(agent_wallet_or_token)
        vault_data = storage_manager.get_vault(agent_wallet_or_token)
        has_pass = pass_data is not None
        pass_type = pass_data["pass_type"] if pass_data else "None"
        exp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(pass_data["expires_at"])) if pass_data else "N/A"
        credits = pass_data.get("credits", 0) if pass_data else 0
        v_bal = vault_data["balance_usdc"] if vault_data else 0.0

        return (
            f"🎫 [AGENT PASS STATUS]\n"
            f"- **Identifier**: `{agent_wallet_or_token}`\n"
            f"- **Active Pass**: {'✅ YES' if has_pass else '❌ NO'}\n"
            f"- **Pass Type**: {pass_type}\n"
            f"- **Remaining Credits**: {credits}\n"
            f"- **Pre-funded Vault Balance**: ${v_bal:.4f} USDC\n"
            f"- **Expires At**: {exp_utc}"
        )
    except Exception as e:
        return f"❌ [PASS STATUS ERROR]: {str(e)}"


def main():
    mcp.run()


if __name__ == "__main__":
    main()
