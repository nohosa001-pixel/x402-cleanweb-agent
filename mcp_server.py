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
    version="2.2.0",
    description="Deterministic Web3 x402 Micropayment MCP Suite for Web, YouTube Gemini AI, and PDF Papers on Polygon, Base, and Arbitrum."
)


@mcp.tool(
    name="get_payment_info",
    description="Returns the Web3 x402 micropayment pricing, multi-chain USDC details, and vault endpoints."
)
def get_payment_info() -> str:
    poly_cfg = multi_chain_manager.get_chain_config("polygon")
    base_cfg = multi_chain_manager.get_chain_config("base")
    arb_cfg = multi_chain_manager.get_chain_config("arbitrum")
    
    return f"""### 💳 CleanWeb Studio x402 Micropayment Architecture
- **Supported Networks**:
  1. **Polygon (137)**: USDC `{poly_cfg.usdc_address}`
  2. **Base (8453)**: USDC `{base_cfg.usdc_address}`
  3. **Arbitrum One (42161)**: USDC `{arb_cfg.usdc_address}`
- **Recipient Wallet**: `{multi_chain_manager.default_recipient}`

**Pricing Tiers**:
- `clean_web_content`: **0.001 USDC** (Markdown web extraction)
- `clean_youtube_transcript`: **0.010 USDC** (Gemini AI intelligence & full transcript)
- `clean_pdf_research`: **0.005 USDC** (PDF papers & whitepapers)
- `clean_batch_scrape`: **0.005 USDC** (Parallel batch scrape)
- `Pre-funded Vault`: Deposit once, execute queries with zero latency (<1ms)
"""


@mcp.tool(
    name="clean_web_content",
    description="Scrapes and converts any raw web page into clean, LLM-ready markdown, eliminating ads, navbars, and noise."
)
def clean_web_content(url: str, auth_token_or_tx: Optional[str] = None) -> str:
    try:
        data = web_cleaner_engine.fetch_and_clean(url)
        return f"✅ [CLEAN WEB SUCCESS]\n\n# {data['title']}\n\n{data['markdown_content']}"
    except Exception as e:
        return f"❌ [FETCH ERROR]: {str(e)}"


@mcp.tool(
    name="clean_youtube_transcript",
    description="Extracts high-precision subtitles, transcripts, or AI-powered comprehensive summaries for any YouTube video using Gemini AI."
)
def clean_youtube_transcript(url: str, lang: str = "ko,en", auth_token_or_tx: Optional[str] = None) -> str:
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
    description="Parses and extracts structured plain text and metadata from online PDF whitepapers and academic research papers."
)
def clean_pdf_research(url: str, max_pages: int = 30, auth_token_or_tx: Optional[str] = None) -> str:
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
    description="Checks the remaining pre-funded USDC balance and session status for an agent wallet address or session key."
)
def get_vault_balance(agent_address_or_key: str) -> str:
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
