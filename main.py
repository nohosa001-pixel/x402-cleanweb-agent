import os
import re
import io
from typing import Optional, Set
from fastapi import FastAPI, Header, Query, HTTPException, status
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

# ERC20 Transfer(address from, address to, uint256 value) Topic0
TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def get_402_response_data(required_amount_usdc: float, service_name: str) -> dict:
    """x402 규격에 맞춘 402 Payment Required 응답 JSON"""
    required_raw_amount = int(required_amount_usdc * (10 ** USDC_DECIMALS))
    return {
        "status": "error",
        "error": "Payment Required",
        "service": service_name,
        "message": f"Payment of {required_amount_usdc} USDC is required on Polygon (Chain ID: {CHAIN_ID}).",
        "x402": {
            "version": "1.0",
            "chain_id": CHAIN_ID,
            "network": "Polygon Mainnet",
            "token": "USDC",
            "token_contract": USDC_CONTRACT_ADDRESS,
            "recipient": RECIPIENT_WALLET,
            "amount": str(required_amount_usdc),
            "amount_raw": str(required_raw_amount),
            "decimals": USDC_DECIMALS,
            "instructions": f"Transfer {required_amount_usdc} USDC to {RECIPIENT_WALLET} on Polygon, then retry with header 'X-Payment-Tx: <TX_HASH>'."
        }
    }

def verify_payment_tx(tx_hash: str, required_amount_usdc: float) -> tuple[bool, str]:
    """Polygon 메인넷 상의 USDC 입금 트랜잭션을 온체인 검증합니다."""
    if not tx_hash or not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
        return False, "Invalid transaction hash format. Expected 0x prefixed 64 hex string."

    tx_hash_lower = tx_hash.lower()
    if tx_hash_lower in processed_txs:
        return False, "Transaction hash has already been consumed (Replay protection)."

    required_raw_amount = int(required_amount_usdc * (10 ** USDC_DECIMALS))

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if not receipt:
            return False, f"Transaction '{tx_hash}' not found on Polygon Mainnet."

        if receipt.get("status") != 1:
            return False, "Transaction was reverted or failed on-chain (status == 0)."

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
            return False, f"No valid USDC Transfer to recipient '{RECIPIENT_WALLET}' for >= {required_amount_usdc} USDC in tx logs."

        processed_txs.add(tx_hash_lower)
        return True, "Payment verified successfully."

    except Exception as e:
        return False, f"On-chain verification error: {str(e)}"

def extract_clean_markdown_for_ai(html_content: str, source_url: str) -> tuple[str, str, str, dict]:
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

    for elem in container.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre", "code", "table"]):
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

    clean_markdown = "\n".join(lines).strip()
    clean_markdown = re.sub(r"\n{3,}", "\n\n", clean_markdown)

    cleaned_char_count = len(clean_markdown)
    cleaned_est_tokens = max(1, cleaned_char_count // 4)
    savings_pct = round(((raw_est_tokens - cleaned_est_tokens) / raw_est_tokens) * 100, 1)

    token_stats = {
        "raw_html_estimated_tokens": raw_est_tokens,
        "clean_markdown_estimated_tokens": cleaned_est_tokens,
        "token_savings_percentage": f"{savings_pct}%",
        "estimated_llm_cost_saved_usd": f"${round((raw_est_tokens - cleaned_est_tokens) * 0.00001, 4)}"
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

@app.get("/api/v1/clean-web")
def clean_web_endpoint(
    url: str = Query(..., description="Target web page URL to clean for AI ingestion"),
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Tx Hash for 0.01 USDC payment")
):
    price_usdc = 0.01
    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(price_usdc, "Clean Web Markdown")
        )

    is_valid, reason = verify_payment_tx(x_payment_tx, price_usdc)
    if not is_valid:
        res_data = get_402_response_data(price_usdc, "Clean Web Markdown")
        res_data["verification_error"] = reason
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=res_data
        )

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error fetching URL '{url}': {str(e)}")

    title, meta_desc, markdown_content, token_stats = extract_clean_markdown_for_ai(resp.text, url)

    return {
        "status": "success",
        "url": url,
        "title": title,
        "description": meta_desc,
        "token_analytics": token_stats,
        "payment": {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc},
        "markdown_content": markdown_content
    }

@app.get("/api/v1/clean-youtube")
def clean_youtube_endpoint(
    url: str = Query(..., description="YouTube Video URL"),
    language: str = Query("ko,en", description="Language codes comma-separated"),
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Tx Hash for 0.02 USDC payment")
):
    price_usdc = 0.02
    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(price_usdc, "YouTube Transcript Markdown")
        )

    is_valid, reason = verify_payment_tx(x_payment_tx, price_usdc)
    if not is_valid:
        res_data = get_402_response_data(price_usdc, "YouTube Transcript Markdown")
        res_data["verification_error"] = reason
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=res_data
        )

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

    return {
        "status": "success",
        "video_id": video_id,
        "title": video_title,
        "transcript_analytics": {"total_segments": len(transcript_list), "estimated_tokens": est_tokens, "word_count": total_words},
        "payment": {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc},
        "markdown_transcript": markdown_transcript
    }

@app.get("/api/v1/clean-pdf")
def clean_pdf_endpoint(
    url: str = Query(..., description="Direct PDF file URL (e.g. arXiv paper or company report)"),
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Tx Hash for 0.05 USDC payment")
):
    """
    [0.05 USDC] x402 PDF 논문/기업보고서 구조화 마크다운 정제 엔드포인트
    """
    price_usdc = 0.05
    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(price_usdc, "PDF Paper & Report Markdown")
        )

    is_valid, reason = verify_payment_tx(x_payment_tx, price_usdc)
    if not is_valid:
        res_data = get_402_response_data(price_usdc, "PDF Paper & Report Markdown")
        res_data["verification_error"] = reason
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=res_data
        )

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

    return {
        "status": "success",
        "url": url,
        "title": title,
        "pdf_analytics": stats,
        "payment": {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc},
        "markdown_content": markdown_content
    }

@app.get("/api/v1/clean-text")
def clean_text_endpoint(
    url: str = Query(..., description="Target web page URL to extract pure plain text"),
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Tx Hash for 0.005 USDC payment")
):
    """
    [0.005 USDC] x402 순수 플레인 텍스트 초경량 추출 엔드포인트
    """
    price_usdc = 0.005
    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data(price_usdc, "Pure Plain Text Extractor")
        )

    is_valid, reason = verify_payment_tx(x_payment_tx, price_usdc)
    if not is_valid:
        res_data = get_402_response_data(price_usdc, "Pure Plain Text Extractor")
        res_data["verification_error"] = reason
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=res_data
        )

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

    return {
        "status": "success",
        "url": url,
        "character_count": len(plain_text),
        "estimated_tokens": max(1, len(plain_text) // 4),
        "payment": {"tx_hash": x_payment_tx, "chain_id": CHAIN_ID, "token": "USDC", "amount": price_usdc},
        "plain_text": plain_text
    }

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
            "clean_web": {"price_usdc": 0.01, "price_raw": 10000},
            "clean_youtube": {"price_usdc": 0.02, "price_raw": 20000},
            "clean_pdf": {"price_usdc": 0.05, "price_raw": 50000},
            "clean_text": {"price_usdc": 0.005, "price_raw": 5000}
        },
        "gas_recommendations": {
            "recommended_gas_limit": 100000,
            "polygon_fast_gas_gwei": "30-50 Gwei",
            "estimated_gas_cost_usd": "< $0.003"
        },
        "agent_sdk": {
            "pip_install": "pip install git+https://github.com/nohosa001-pixel/x402-cleanweb-agent.git",
            "uvx_run": "uvx --from git+https://github.com/nohosa001-pixel/x402-cleanweb-agent x402-agent"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

