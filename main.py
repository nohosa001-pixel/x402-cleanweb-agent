import os
import re
import io
import time
from typing import Optional, Set, List
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import FastAPI, Header, Query, Body, HTTPException, status

from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3
from bs4 import BeautifulSoup, Comment
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from pypdf import PdfReader

# .env 로드 (환경변수 덮어쓰기 허용)
load_dotenv(override=True)

app = FastAPI(
    title="Polygon x402 Micro-Payment AI Data Agent Suite",
    description="Web3 x402 Micropayment gateway on Polygon for AI-ready Clean Web, YouTube Transcripts, PDF Papers & Plain Text.",
    version="1.2.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Native USDC on Polygon Mainnet
USDC_CONTRACT_ADDRESS = Web3.to_checksum_address(
    os.getenv("USDC_CONTRACT_ADDRESS", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
)
USDC_DECIMALS = 6

# Server Recipient Wallet
RECIPIENT_WALLET = Web3.to_checksum_address(
    os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")
)

# Web3 연결 초기화 (Fallback RPC 적용)
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

# 중복 결제(Replay Attack) 방지용 처리된 트랜잭션 저장소
processed_txs: Set[str] = set()

# In-memory Agent Response Cache (LRU TTL Cache)
CACHE_TTL_SECONDS = 3600
agent_cache: dict[str, tuple[float, dict]] = {}

def get_from_cache(cache_key: str) -> Optional[dict]:
    if cache_key in agent_cache:
        timestamp, data = agent_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            return data
        else:
            del agent_cache[cache_key]
    return None

def set_to_cache(cache_key: str, data: dict):
    if len(agent_cache) > 2000:
        oldest_key = min(agent_cache.keys(), key=lambda k: agent_cache[k][0])
        del agent_cache[oldest_key]
    agent_cache[cache_key] = (time.time(), data)

# ERC20 Transfer(address from, address to, uint256 value) Topic0
TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def get_402_response_data(
    required_amount_usdc: float,
    service_name: str,
    error_code: str = "PAYMENT_REQUIRED",
    error_message: Optional[str] = None,
    suggested_action: Optional[str] = None,
    received_amount_usdc: float = 0.0
) -> dict:
    """x402 Agent Self-Healing Structured 402 Payment Required Response JSON"""
    required_raw_amount = int(required_amount_usdc * (10 ** USDC_DECIMALS))
    msg = error_message or f"Payment of {required_amount_usdc} USDC is required on Polygon (Chain ID: {CHAIN_ID})."
    action = suggested_action or (
        f"Send {required_amount_usdc} USDC to '{RECIPIENT_WALLET}' on Polygon Mainnet (Chain ID 137), "
        f"then retry request with header 'X-Payment-Tx: <TX_HASH>'."
    )
    return {
        "status": "error",
        "error_code": error_code,
        "error": "Payment Required",
        "service": service_name,
        "message": msg,
        "required_usdc": required_amount_usdc,
        "received_usdc": received_amount_usdc,
        "suggested_action": action,
        "actionable_fix": {
            "action": "TRANSFER_USDC",
            "chain_id": CHAIN_ID,
            "network": "Polygon Mainnet (PoS)",
            "token": "USDC",
            "token_contract": USDC_CONTRACT_ADDRESS,
            "recipient_wallet": RECIPIENT_WALLET,
            "amount_usdc": required_amount_usdc,
            "amount_raw": str(required_raw_amount),
            "decimals": USDC_DECIMALS,
            "retry_header": "X-Payment-Tx: 0x<POLYGON_TX_HASH>"
        },
        "x402": {
            "version": "1.2",
            "chain_id": CHAIN_ID,
            "network": "Polygon Mainnet",
            "token": "USDC",
            "token_contract": USDC_CONTRACT_ADDRESS,
            "recipient": RECIPIENT_WALLET,
            "amount": str(required_amount_usdc),
            "amount_raw": str(required_raw_amount),
            "decimals": USDC_DECIMALS,
            "instructions": action
        }
    }

def verify_payment_tx(tx_hash: str, required_amount_usdc: float) -> tuple[bool, str, str, str]:
    """
    Polygon 메인넷 상의 USDC 입금 트랜잭션을 온체인 검증합니다.
    Returns: (is_valid, error_code, reason, suggested_action)
    """
    if not tx_hash or not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
        return (
            False,
            "INVALID_TX_FORMAT",
            "Invalid transaction hash format. Expected 0x followed by 64 hex characters.",
            "Provide a valid 64-character hexadecimal Polygon transaction hash starting with '0x'."
        )

    tx_hash_lower = tx_hash.lower()
    if tx_hash_lower in processed_txs:
        return (
            False,
            "TX_ALREADY_CONSUMED",
            "Transaction hash has already been consumed (Replay protection).",
            "Generate a new USDC transfer on Polygon. Used transaction hashes cannot be reused."
        )

    required_raw_amount = int(required_amount_usdc * (10 ** USDC_DECIMALS))

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if not receipt:
            return (
                False,
                "TX_NOT_FOUND",
                f"Transaction '{tx_hash}' not found on Polygon Mainnet.",
                "Wait 3-5 seconds for Polygon node propagation or confirm transaction on PolygonScan."
            )

        if receipt.get("status") != 1:
            return (
                False,
                "TX_FAILED_ONCHAIN",
                "Transaction was reverted or failed on-chain (status == 0).",
                "Check wallet gas (POL) and USDC balance, then re-execute the transfer transaction."
            )

        payment_found = False
        received_raw_amount = 0

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

                if to_address == RECIPIENT_WALLET:
                    received_raw_amount = amount
                    if amount >= required_raw_amount:
                        payment_found = True
                        break

        if not payment_found:
            received_usdc = received_raw_amount / (10 ** USDC_DECIMALS)
            if received_raw_amount > 0:
                shortage = required_amount_usdc - received_usdc
                return (
                    False,
                    "INSUFFICIENT_FEE",
                    f"Received {received_usdc:.4f} USDC, but {required_amount_usdc} USDC is required.",
                    f"Send remaining {shortage:.4f} USDC to '{RECIPIENT_WALLET}' and retry with the new Tx hash."
                )
            else:
                return (
                    False,
                    "NO_TRANSFER_TO_RECIPIENT",
                    f"No USDC Transfer event to recipient '{RECIPIENT_WALLET}' found in tx logs.",
                    f"Ensure recipient address is set to '{RECIPIENT_WALLET}'."
                )

        processed_txs.add(tx_hash_lower)
        return (True, "OK", "Payment verified successfully.", "")

    except Exception as e:
        return (
            False,
            "ONCHAIN_RPC_ERROR",
            f"On-chain verification error: {str(e)}",
            "Polygon RPC node temporarily busy. Please retry with the same Tx hash."
        )


def extract_clean_markdown_for_ai(
    html_content: str,
    source_url: str,
    density: str = "standard",
    max_tokens: Optional[int] = None
) -> tuple[str, str, str, dict]:
    raw_char_count = len(html_content)
    raw_est_tokens = max(1, raw_char_count // 4)

    soup = BeautifulSoup(html_content, "html.parser")

    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    noise_tags = [
        "script", "style", "nav", "footer", "header", "aside",
        "noscript", "iframe", "svg", "form", "button", "input"
    ]
    for tag in soup(noise_tags):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text().strip()
    else:
        title = source_url

    meta_desc = ""
    desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or \
               soup.find("meta", attrs={"property": "og:description"})
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    container = soup.find("article") or soup.find("main") or soup.find("body") or soup

    lines = []
    lines.append(f"# {title}\n")
    lines.append(f"> **Source URL**: {source_url}")
    if meta_desc:
        lines.append(f"> **Summary/Description**: {meta_desc}\n")
    else:
        lines.append("")

    if density == "tables_only":
        tables = container.find_all("table")
        if not tables:
            lines.append("*(No data tables found on page)*")
        for idx, table in enumerate(tables):
            lines.append(f"\n### Table {idx + 1}\n")
            rows = table.find_all("tr")
            for r_idx, row in enumerate(rows):
                cols = [c.get_text().strip().replace("\n", " ") for c in row.find_all(["th", "td"])]
                if cols:
                    lines.append("| " + " | ".join(cols) + " |")
                    if r_idx == 0:
                        lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    else:
        for elem in container.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre", "code", "table"]):
            tag = elem.name
            text = elem.get_text().strip()
            if not text:
                continue

            if density == "compact":
                if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    lines.append(f"\n**{text}**:")
                elif tag == "li":
                    lines.append(f"- {text}")
                else:
                    lines.append(text)
            else:
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

    clean_markdown = "\n".join(lines).strip()
    clean_markdown = re.sub(r"\n{3,}", "\n\n", clean_markdown)

    if max_tokens and max_tokens > 0:
        max_chars = max_tokens * 4
        if len(clean_markdown) > max_chars:
            clean_markdown = clean_markdown[:max_chars].rsplit("\n", 1)[0] + "\n\n*(Trimmed to agent max_tokens budget)*"

    cleaned_char_count = len(clean_markdown)
    cleaned_est_tokens = max(1, cleaned_char_count // 4)
    savings_pct = round(((raw_est_tokens - cleaned_est_tokens) / raw_est_tokens) * 100, 1)

    token_stats = {
        "raw_html_estimated_tokens": raw_est_tokens,
        "clean_markdown_estimated_tokens": cleaned_est_tokens,
        "token_savings_percentage": f"{savings_pct}%",
        "estimated_llm_cost_saved_usd": f"${round((raw_est_tokens - cleaned_est_tokens) * 0.00001, 4)}",
        "density_mode": density
    }

    return title, meta_desc, clean_markdown, token_stats


def extract_pdf_to_markdown(pdf_bytes: bytes, source_url: str) -> tuple[str, str, dict]:
    """PDF 바이트 데이터를 읽고 AI 최적화 마크다운 및 메타데이터를 추출합니다."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    num_pages = len(reader.pages)
    
    info = reader.metadata or {}
    pdf_title = info.title if info and info.title else source_url.split("/")[-1]

    lines = [
        f"# 📑 {pdf_title}\n",
        f"> **Source PDF**: {source_url}",
        f"> **Total Pages**: {num_pages} pages\n"
    ]

    total_words = 0
    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        text = page.extract_text() or ""
        cleaned_text = text.strip()
        if not cleaned_text:
            continue

        total_words += len(cleaned_text.split())
        lines.append(f"\n## 📄 Page {page_num}\n")
        lines.append(cleaned_text)

    markdown_pdf = "\n".join(lines).strip()
    est_tokens = max(1, len(markdown_pdf) // 4)

    stats = {
        "total_pages": num_pages,
        "word_count": total_words,
        "estimated_tokens": est_tokens
    }

    return pdf_title, markdown_pdf, stats

def extract_youtube_video_id(url: str) -> Optional[str]:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
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

@app.get("/")
def read_root():
    static_file_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_file_path):
        return FileResponse(static_file_path)
    return {
        "service": "Polygon x402 Micro-Payment AI Data Agent Suite",
        "version": "1.2.0",
        "chain_id": CHAIN_ID,
        "token": "USDC",
        "recipient": RECIPIENT_WALLET,
        "pricing_and_services": {
            "clean_web_markdown": {"endpoint": "/api/v1/clean-web?url=<URL>", "price": "0.01 USDC"},
            "youtube_transcript": {"endpoint": "/api/v1/clean-youtube?url=<YOUTUBE_URL>", "price": "0.02 USDC"},
            "pdf_markdown": {"endpoint": "/api/v1/clean-pdf?url=<PDF_URL>", "price": "0.05 USDC"},
            "plain_text": {"endpoint": "/api/v1/clean-text?url=<URL>", "price": "0.005 USDC"}
        },
        "docs": "/docs"
    }

class BatchCleanRequest(BaseModel):
    urls: List[str] = Field(..., description="List of target URLs to clean (max 10 URLs per batch)")
    density: str = Field("standard", description="'standard', 'compact', or 'tables_only'")
    max_tokens_per_url: Optional[int] = Field(None, description="Optional maximum tokens per URL")

@app.get("/api/v1/clean-web")
def clean_web_endpoint(
    url: str = Query(..., description="Target web page URL to clean for AI ingestion"),
    density: str = Query("standard", description="Extraction density: 'standard', 'compact', or 'tables_only'"),
    max_tokens: Optional[int] = Query(None, description="Optional maximum token budget"),
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Tx Hash for 0.01 USDC payment")
):
    price_usdc = 0.01
    cache_key = f"clean_web:{url}:{density}:{max_tokens}"

    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(price_usdc, "Clean Web Markdown", error_code="PAYMENT_REQUIRED")
        )

    is_valid, err_code, reason, action = verify_payment_tx(x_payment_tx, price_usdc)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(
                price_usdc,
                "Clean Web Markdown",
                error_code=err_code,
                error_message=reason,
                suggested_action=action
            )
        )

    cached_res = get_from_cache(cache_key)
    if cached_res:
        cached_res["payment"] = {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc}
        cached_res["cached"] = True
        return cached_res

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error fetching URL '{url}': {str(e)}")

    title, meta_desc, markdown_content, token_stats = extract_clean_markdown_for_ai(
        resp.text,
        url,
        density=density,
        max_tokens=max_tokens
    )

    result_data = {
        "status": "success",
        "url": url,
        "title": title,
        "description": meta_desc,
        "token_analytics": token_stats,
        "payment": {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc},
        "markdown_content": markdown_content,
        "cached": False
    }

    set_to_cache(cache_key, result_data)
    return result_data

@app.post("/api/v1/batch-clean")
def batch_clean_endpoint(
    req: BatchCleanRequest,
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Tx Hash for (0.01 * count) USDC payment")
):
    """
    [Agent Swarm Optimized] Batch scrape and clean multiple URLs in a single request.
    Pricing: 0.01 USDC per URL.
    """
    if not req.urls:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No URLs provided in batch request.")

    if len(req.urls) > 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch limit is 10 URLs per request.")

    total_price_usdc = round(len(req.urls) * 0.01, 4)

    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(
                total_price_usdc,
                f"Batch Clean Web ({len(req.urls)} URLs)",
                error_code="PAYMENT_REQUIRED"
            )
        )

    is_valid, err_code, reason, action = verify_payment_tx(x_payment_tx, total_price_usdc)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(
                total_price_usdc,
                f"Batch Clean Web ({len(req.urls)} URLs)",
                error_code=err_code,
                error_message=reason,
                suggested_action=action
            )
        )

    def fetch_and_clean(single_url: str):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(single_url, headers=headers, timeout=12)
            resp.raise_for_status()
            title, meta_desc, md, stats = extract_clean_markdown_for_ai(
                resp.text,
                single_url,
                density=req.density,
                max_tokens=req.max_tokens_per_url
            )
            return {
                "status": "success",
                "url": single_url,
                "title": title,
                "token_analytics": stats,
                "markdown_content": md
            }
        except Exception as e:
            return {
                "status": "error",
                "url": single_url,
                "error_message": str(e)
            }

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_and_clean, u): u for u in req.urls}
        for future in as_completed(future_to_url):
            results.append(future.result())

    total_raw = sum(r.get("token_analytics", {}).get("raw_html_estimated_tokens", 0) for r in results if r.get("status") == "success")
    total_clean = sum(r.get("token_analytics", {}).get("clean_markdown_estimated_tokens", 0) for r in results if r.get("status") == "success")

    return {
        "status": "success",
        "total_urls": len(req.urls),
        "successful_count": sum(1 for r in results if r.get("status") == "success"),
        "total_token_analytics": {
            "total_raw_tokens": total_raw,
            "total_clean_tokens": total_clean,
            "total_tokens_saved": max(0, total_raw - total_clean)
        },
        "payment": {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": total_price_usdc},
        "results": results
    }

@app.get("/api/v1/clean-youtube")
def clean_youtube_endpoint(
    url: str = Query(..., description="YouTube Video URL"),
    language: str = Query("ko,en", description="Language codes comma-separated"),
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Tx Hash for 0.02 USDC payment")
):
    price_usdc = 0.02
    cache_key = f"clean_yt:{url}:{language}"

    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(price_usdc, "YouTube Transcript Markdown", error_code="PAYMENT_REQUIRED")
        )

    is_valid, err_code, reason, action = verify_payment_tx(x_payment_tx, price_usdc)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(
                price_usdc,
                "YouTube Transcript Markdown",
                error_code=err_code,
                error_message=reason,
                suggested_action=action
            )
        )

    cached_res = get_from_cache(cache_key)
    if cached_res:
        cached_res["payment"] = {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc}
        cached_res["cached"] = True
        return cached_res

    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid YouTube video URL.")

    video_title = f"YouTube Video ({video_id})"
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        oembed_res = requests.get(oembed_url, timeout=5)
        if oembed_res.status_code == 200:
            video_title = oembed_res.json().get("title", video_title)
    except Exception:
        pass

    pref_langs = [l.strip() for l in language.split(",") if l.strip()]
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=pref_langs)
    except Exception:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transcript unavailable: {str(e)}")

    lines = [f"# 🎬 {video_title}\n", f"> **YouTube URL**: https://www.youtube.com/watch?v={video_id}\n", "## 📜 Transcript & Timestamps\n"]
    total_words = 0
    for item in transcript_list:
        start_sec = item.get("start", 0)
        time_str = format_timestamp(start_sec)
        text = item.get("text", "").strip()
        total_words += len(text.split())
        lines.append(f"- **`[{time_str}]`** {text}")

    markdown_transcript = "\n".join(lines)
    est_tokens = max(1, len(markdown_transcript) // 4)

    result_data = {
        "status": "success",
        "video_id": video_id,
        "title": video_title,
        "transcript_analytics": {"total_segments": len(transcript_list), "estimated_tokens": est_tokens, "word_count": total_words},
        "payment": {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc},
        "markdown_transcript": markdown_transcript,
        "cached": False
    }

    set_to_cache(cache_key, result_data)
    return result_data

@app.get("/api/v1/clean-pdf")
def clean_pdf_endpoint(
    url: str = Query(..., description="Direct PDF file URL (e.g. arXiv paper or company report)"),
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Tx Hash for 0.05 USDC payment")
):
    """
    [0.05 USDC] x402 PDF 논문/기업보고서 구조화 마크다운 정제 엔드포인트
    """
    price_usdc = 0.05
    cache_key = f"clean_pdf:{url}"

    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(price_usdc, "PDF Paper & Report Markdown", error_code="PAYMENT_REQUIRED")
        )

    is_valid, err_code, reason, action = verify_payment_tx(x_payment_tx, price_usdc)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(
                price_usdc,
                "PDF Paper & Report Markdown",
                error_code=err_code,
                error_message=reason,
                suggested_action=action
            )
        )

    cached_res = get_from_cache(cache_key)
    if cached_res:
        cached_res["payment"] = {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc}
        cached_res["cached"] = True
        return cached_res

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        pdf_res = requests.get(url, headers=headers, timeout=25)
        pdf_res.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to download PDF from '{url}': {str(e)}")

    try:
        title, markdown_content, stats = extract_pdf_to_markdown(pdf_res.content, url)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to parse PDF content: {str(e)}")

    result_data = {
        "status": "success",
        "url": url,
        "title": title,
        "pdf_analytics": stats,
        "payment": {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc},
        "markdown_content": markdown_content,
        "cached": False
    }

    set_to_cache(cache_key, result_data)
    return result_data

@app.get("/api/v1/clean-text")
def clean_text_endpoint(
    url: str = Query(..., description="Target web page URL to extract pure plain text"),
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Tx Hash for 0.005 USDC payment")
):
    """
    [0.005 USDC] x402 순수 플레인 텍스트 초경량 추출 엔드포인트
    """
    price_usdc = 0.005
    cache_key = f"clean_text:{url}"

    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(price_usdc, "Pure Plain Text Extractor", error_code="PAYMENT_REQUIRED")
        )

    is_valid, err_code, reason, action = verify_payment_tx(x_payment_tx, price_usdc)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(
                price_usdc,
                "Pure Plain Text Extractor",
                error_code=err_code,
                error_message=reason,
                suggested_action=action
            )
        )

    cached_res = get_from_cache(cache_key)
    if cached_res:
        cached_res["payment"] = {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc}
        cached_res["cached"] = True
        return cached_res

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error fetching URL: {str(e)}")

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "form"]):
        tag.decompose()

    plain_text = re.sub(r"\s+", " ", soup.get_text()).strip()

    result_data = {
        "status": "success",
        "url": url,
        "character_count": len(plain_text),
        "estimated_tokens": max(1, len(plain_text) // 4),
        "payment": {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc},
        "plain_text": plain_text,
        "cached": False
    }

    set_to_cache(cache_key, result_data)
    return result_data


@app.get("/.well-known/agent.json")
def agent_discovery_endpoint():
    """
    Standard AI Agent Discovery Metadata (Machine-Readable Manifest)
    """
    return {
        "name": "Polygon x402 AI Data Agent",
        "description": "Zero-human Web3 micropayment MCP agent for LLM-ready clean web scraping, YouTube transcripts, PDF paper extraction, and plain text on Polygon Mainnet.",
        "version": "1.2.0",
        "protocol": "x402-v1",
        "supported_chains": [
            {
                "chain_id": CHAIN_ID,
                "chain_name": "Polygon Mainnet (PoS)",
                "currency": "USDC",
                "token_contract": USDC_CONTRACT_ADDRESS,
                "token_decimals": USDC_DECIMALS,
                "recipient_wallet": RECIPIENT_WALLET,
                "rpc_urls": POLYGON_RPC_URLS
            }
        ],
        "services": [
            {
                "id": "clean_web",
                "name": "Clean Web Markdown",
                "endpoint": "/api/v1/clean-web",
                "method": "GET",
                "price_usdc": 0.01,
                "description": "Removes noise, ads, banners, and returns AI-ready structured Markdown with token analytics."
            },
            {
                "id": "clean_youtube",
                "name": "YouTube Transcript Extractor",
                "endpoint": "/api/v1/clean-youtube",
                "method": "GET",
                "price_usdc": 0.02,
                "description": "Extracts timestamps and complete video transcripts into structured Markdown."
            },
            {
                "id": "clean_pdf",
                "name": "PDF Paper & Report Extractor",
                "endpoint": "/api/v1/clean-pdf",
                "method": "GET",
                "price_usdc": 0.05,
                "description": "Parses arXiv research papers and technical PDF reports into clean Markdown."
            },
            {
                "id": "clean_text",
                "name": "Pure Plain Text Extractor",
                "endpoint": "/api/v1/clean-text",
                "method": "GET",
                "price_usdc": 0.005,
                "description": "Ultra-lightweight raw plain text for vector embeddings and fast RAG search."
            }
        ],
        "auth": {
            "type": "http_402_onchain",
            "header": "X-Payment-Tx",
            "format": "0x<64_hex_polygon_tx_hash>"
        },
        "docs_url": "https://x402-cleanweb-agent.onrender.com/docs",
        "github_url": "https://github.com/nohosa001-pixel/x402-cleanweb-agent"
    }

@app.get("/api/v1/agent/pricing-catalog")
def agent_pricing_catalog_endpoint():
    """
    Real-time Machine-Readable Pricing Catalog with Gas Recommendations
    """
    return {
        "status": "active",
        "timestamp": os.getenv("SERVER_TIME", "2026-08-21T00:00:00Z"),
        "chain_id": CHAIN_ID,
        "payment_token": {
            "symbol": "USDC",
            "address": USDC_CONTRACT_ADDRESS,
            "decimals": USDC_DECIMALS
        },
        "recipient_wallet": RECIPIENT_WALLET,
        "pricing_table": {
            "clean_web": {"price_usdc": 0.01, "price_raw": 10000, "description": "Single URL web clean markdown"},
            "batch_clean": {"price_usdc": "0.01 / URL", "price_raw_per_url": 10000, "description": "Multi-URL batch scraping (up to 10 URLs in 1 tx)"},
            "clean_youtube": {"price_usdc": 0.02, "price_raw": 20000, "description": "YouTube full transcript and timestamps"},
            "clean_pdf": {"price_usdc": 0.05, "price_raw": 50000, "description": "arXiv & research papers PDF extractor"},
            "clean_text": {"price_usdc": 0.005, "price_raw": 5000, "description": "Ultra-fast raw text extractor for vector search"}
        },
        "gas_recommendations": {
            "recommended_gas_limit": 100000,
            "polygon_fast_gas_gwei": "30-50 Gwei",
            "estimated_gas_cost_usd": "< $0.003"
        },
        "agent_sdk": {
            "pypi_package": "x402-cleanweb-agent",
            "pip_install": "pip install x402-cleanweb-agent",
            "uvx_run": "uvx x402-cleanweb-agent",
            "pypi_url": "https://pypi.org/project/x402-cleanweb-agent/"
        }
    }

@app.get("/health")
def health_check():
    """Service Health & Status Check"""
    return {
        "status": "healthy",
        "version": "1.2.0",
        "chain_id": CHAIN_ID,
        "network": "Polygon Mainnet",
        "pypi": "https://pypi.org/project/x402-cleanweb-agent/"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


