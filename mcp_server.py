import os
import re
import io
from typing import Optional, Set
from mcp.server import MCPServer
from web3 import Web3
from bs4 import BeautifulSoup, Comment
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from pypdf import PdfReader

load_dotenv(override=True)

# MCP Server 초기화
mcp = MCPServer(
    name="Polygon-x402-AI-Data-Agent",
    version="1.2.0",
    description="Web3 x402 Micropayment MCP Suite for Web, YouTube, PDF Papers & Plain Text on Polygon Mainnet"
)

# Polygon & Token Config
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")
POLYGON_RPC_URLS = [
    POLYGON_RPC_URL,
    "https://polygon.llamarpc.com",
    "https://1rpc.io/matic",
    "https://polygon-rpc.com"
]
CHAIN_ID = 137
USDC_CONTRACT_ADDRESS = Web3.to_checksum_address(
    os.getenv("USDC_CONTRACT_ADDRESS", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
)
USDC_DECIMALS = 6

RECIPIENT_WALLET = Web3.to_checksum_address(
    os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")
)

TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
processed_txs: Set[str] = set()

def get_web3_instance() -> Web3:
    for rpc in POLYGON_RPC_URLS:
        try:
            w3_inst = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if w3_inst.is_connected():
                return w3_inst
        except Exception:
            continue
    return Web3(Web3.HTTPProvider(POLYGON_RPC_URLS[0]))

w3 = get_web3_instance()

def verify_payment_tx(tx_hash: str, required_amount_usdc: float) -> tuple[bool, str]:
    if not tx_hash or not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
        return False, "Invalid tx hash format. Must be 0x followed by 64 hex characters."

    tx_hash_lower = tx_hash.lower()
    if tx_hash_lower in processed_txs:
        return False, "Transaction hash has already been used (Replay protection)."

    required_raw_amount = int(required_amount_usdc * (10 ** USDC_DECIMALS))

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if not receipt:
            return False, f"Transaction '{tx_hash}' not found on Polygon Mainnet."

        if receipt.get("status") != 1:
            return False, "Transaction failed on-chain (status == 0)."

        payment_found = False
        for log in receipt.get("logs", []):
            if Web3.to_checksum_address(log.get("address")) != USDC_CONTRACT_ADDRESS:
                continue

            topics = log.get("topics", [])
            if not topics or topics[0].hex().lower() != TRANSFER_EVENT_TOPIC.lower():
                continue

            if len(topics) >= 3:
                to_addr_hex = "0x" + topics[2].hex()[-40:]
                to_address = Web3.to_checksum_address(to_addr_hex)

                raw_data = log.get("data")
                if isinstance(raw_data, bytes):
                    amount = int.from_bytes(raw_data, byteorder="big")
                elif isinstance(raw_data, str):
                    amount = int(raw_data, 16)
                else:
                    amount = 0

                if to_address == RECIPIENT_WALLET and amount >= required_raw_amount:
                    payment_found = True
                    break

        if not payment_found:
            return False, f"No valid USDC Transfer to '{RECIPIENT_WALLET}' for >= {required_amount_usdc} USDC found."

        processed_txs.add(tx_hash_lower)
        return True, "Payment verified."
    except Exception as e:
        return False, f"On-chain verification error: {str(e)}"

def extract_clean_markdown_for_ai(html_content: str, source_url: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    noise_tags = ["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe", "svg", "form"]
    for tag in soup(noise_tags):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else (soup.find("h1").get_text().strip() if soup.find("h1") else source_url)
    container = soup.find("article") or soup.find("main") or soup.find("body") or soup

    lines = [f"# {title}\n", f"> **Source**: {source_url}\n"]
    for elem in container.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre", "code"]):
        tag = elem.name
        text = elem.get_text().strip()
        if not text:
            continue
        if tag == "h1":
            lines.append(f"\n# {text}\n")
        elif tag == "h2":
            lines.append(f"\n## {text}\n")
        elif tag == "h3":
            lines.append(f"\n### {text}\n")
        elif tag in ["h4", "h5", "h6"]:
            lines.append(f"\n#### {text}\n")
        elif tag == "li":
            lines.append(f"- {text}")
        elif tag == "blockquote":
            lines.append(f"\n> {text}\n")
        elif tag in ["pre", "code"]:
            lines.append(f"\n```\n{text}\n```\n")
        elif tag == "p":
            lines.append(f"\n{text}\n")

    markdown_text = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", markdown_text)

def extract_youtube_video_id(url: str) -> Optional[str]:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:shorts\/)([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def format_timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

@mcp.tool(
    name="get_payment_info",
    description="Returns the Polygon Web3 micropayment pricing and recipient details for tools in this server."
)
def get_payment_info() -> str:
    return f"""### 💳 Polygon x402 Micropayment Services & Pricing
- **Network**: Polygon Mainnet (Chain ID: {CHAIN_ID})
- **Token**: Native USDC (`{USDC_CONTRACT_ADDRESS}`)
- **Recipient Wallet**: `{RECIPIENT_WALLET}`

**Available Paid Tools**:
1. `fetch_clean_web_content`: **0.01 USDC** (Clean webpage into AI Markdown)
2. `fetch_youtube_transcript`: **0.02 USDC** (Full YouTube timestamps & transcript Markdown)
3. `fetch_pdf_markdown`: **0.05 USDC** (PDF papers & corporate reports into structured Markdown)
4. `fetch_plain_text`: **0.005 USDC** (Pure lightweight plain text extraction)
"""

@mcp.tool(
    name="fetch_clean_web_content",
    description="Fetches and transforms any webpage into AI-ready clean Markdown. Requires 0.01 USDC on Polygon."
)
def fetch_clean_web_content(url: str, payment_tx_hash: Optional[str] = None) -> str:
    price_usdc = 0.01
    if not payment_tx_hash:
        return f"""⚠️ [HTTP 402 - PAYMENT REQUIRED]
To access clean web content for '{url}', a micropayment of {price_usdc} USDC on Polygon Mainnet is required.
👉 Recipient Wallet: `{RECIPIENT_WALLET}` (Chain ID: {CHAIN_ID})"""

    is_valid, reason = verify_payment_tx(payment_tx_hash, price_usdc)
    if not is_valid:
        return f"❌ [PAYMENT VERIFICATION FAILED]: {reason}"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        markdown = extract_clean_markdown_for_ai(res.text, url)
        return f"✅ [PAYMENT VERIFIED (Tx: {payment_tx_hash})]\n\n{markdown}"
    except Exception as e:
        return f"❌ [FETCH ERROR]: {str(e)}"

@mcp.tool(
    name="fetch_youtube_transcript",
    description="Extracts full transcript and timestamps from any YouTube video into AI-ready Markdown. Requires 0.02 USDC on Polygon."
)
def fetch_youtube_transcript(url: str, language: str = "ko,en", payment_tx_hash: Optional[str] = None) -> str:
    price_usdc = 0.02
    if not payment_tx_hash:
        return f"""⚠️ [HTTP 402 - PAYMENT REQUIRED]
To extract YouTube transcript for '{url}', a micropayment of {price_usdc} USDC on Polygon Mainnet is required.
👉 Recipient Wallet: `{RECIPIENT_WALLET}` (Chain ID: {CHAIN_ID})"""

    is_valid, reason = verify_payment_tx(payment_tx_hash, price_usdc)
    if not is_valid:
        return f"❌ [PAYMENT VERIFICATION FAILED]: {reason}"

    video_id = extract_youtube_video_id(url)
    if not video_id:
        return "❌ [INVALID URL]: Could not parse YouTube video ID."

    try:
        pref_langs = [l.strip() for l in language.split(",") if l.strip()]
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=pref_langs)
        except Exception:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

        lines = [f"# 🎬 YouTube Transcript ({video_id})\n", f"> **Source**: https://www.youtube.com/watch?v={video_id}\n", "## 📜 Transcript & Timestamps\n"]
        for item in transcript_list:
            start_sec = item.get("start", 0)
            lines.append(f"- **`[{format_timestamp(start_sec)}]`** {item.get('text', '').strip()}")

        return f"✅ [PAYMENT VERIFIED (Tx: {payment_tx_hash})]\n\n" + "\n".join(lines)
    except Exception as e:
        return f"❌ [TRANSCRIPT ERROR]: {str(e)}"

@mcp.tool(
    name="fetch_pdf_markdown",
    description="Extracts structured Markdown from PDF research papers and reports. Requires 0.05 USDC on Polygon."
)
def fetch_pdf_markdown(url: str, payment_tx_hash: Optional[str] = None) -> str:
    price_usdc = 0.05
    if not payment_tx_hash:
        return f"""⚠️ [HTTP 402 - PAYMENT REQUIRED]
To extract PDF document for '{url}', a micropayment of {price_usdc} USDC on Polygon Mainnet is required.
👉 Recipient Wallet: `{RECIPIENT_WALLET}` (Chain ID: {CHAIN_ID})"""

    is_valid, reason = verify_payment_tx(payment_tx_hash, price_usdc)
    if not is_valid:
        return f"❌ [PAYMENT VERIFICATION FAILED]: {reason}"

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
        res.raise_for_status()
        reader = PdfReader(io.BytesIO(res.content))
        lines = [f"# 📑 PDF Document ({url.split('/')[-1]})\n", f"> **Pages**: {len(reader.pages)}\n"]
        for idx, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if text:
                lines.append(f"\n## 📄 Page {idx + 1}\n{text}")
        return f"✅ [PAYMENT VERIFIED (Tx: {payment_tx_hash})]\n\n" + "\n".join(lines)
    except Exception as e:
        return f"❌ [PDF ERROR]: {str(e)}"

@mcp.tool(
    name="fetch_plain_text",
    description="Extracts ultra-lightweight pure plain text from any web page. Requires 0.005 USDC on Polygon."
)
def fetch_plain_text(url: str, payment_tx_hash: Optional[str] = None) -> str:
    price_usdc = 0.005
    if not payment_tx_hash:
        return f"""⚠️ [HTTP 402 - PAYMENT REQUIRED]
To extract plain text for '{url}', a micropayment of {price_usdc} USDC on Polygon Mainnet is required.
👉 Recipient Wallet: `{RECIPIENT_WALLET}` (Chain ID: {CHAIN_ID})"""

    is_valid, reason = verify_payment_tx(payment_tx_hash, price_usdc)
    if not is_valid:
        return f"❌ [PAYMENT VERIFICATION FAILED]: {reason}"

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
            tag.decompose()
        plain_text = re.sub(r"\s+", " ", soup.get_text()).strip()
        return f"✅ [PAYMENT VERIFIED (Tx: {payment_tx_hash})]\n\n{plain_text}"
    except Exception as e:
        return f"❌ [TEXT ERROR]: {str(e)}"

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()

