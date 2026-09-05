"""
Model Context Protocol (MCP) Server for CleanWeb Studio.
Supports Multi-Chain (Polygon/Base/Arbitrum) USDC Micropayments and Free Tier for Claude Desktop, Cursor, and Agentic Clients.
"""

import os
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

load_dotenv(override=True)

# MCP Server Initialization
mcp = MCPServer(
    name="x402-cleanweb-agent",
    version="2.4.0",
    description="Deterministic Web3 x402 Micropayment MCP Suite for Web, YouTube Gemini AI, and PDF Papers on Polygon, Base, and Arbitrum."
)


from pydantic import Field

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
def get_payment_info() -> str:
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
- `clean_youtube_transcript`: **0.010 USDC** (Gemini AI intelligence & full transcript)
- `clean_pdf_research`: **0.005 USDC** (PDF papers & whitepapers, up to 100 pages)
- `clean_batch_scrape`: **0.005 USDC** (Concurrent parallel batch scrape up to 10 URLs)
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
    )
) -> str:
    try:
        data = web_cleaner_engine.fetch_and_clean(url)
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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
