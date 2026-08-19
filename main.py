import os
import re
from typing import Optional, Set
from fastapi import FastAPI, Header, Query, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3
from bs4 import BeautifulSoup, Comment
import requests
from dotenv import load_dotenv

# .env 로드 (환경변수 덮어쓰기 허용)
load_dotenv(override=True)

app = FastAPI(
    title="Polygon x402 Micro-Payment AI Clean Web Agent",
    description="Web3 x402 Micropayment gateway on Polygon network for AI-ready Clean Markdown content.",
    version="1.0.0"
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
REQUIRED_AMOUNT_USDC = float(os.getenv("PAYMENT_AMOUNT_USDC", "0.01"))
REQUIRED_RAW_AMOUNT = int(REQUIRED_AMOUNT_USDC * (10 ** USDC_DECIMALS)) # 0.01 USDC = 10,000 raw units

# Server Recipient Wallet (환경 변수 또는 기본 수신 주소)
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

def get_402_response_data() -> dict:
    """x402 규격에 맞춘 402 Payment Required 응답 JSON"""
    return {
        "status": "error",
        "error": "Payment Required",
        "message": f"Payment of {REQUIRED_AMOUNT_USDC} USDC is required on Polygon (Chain ID: {CHAIN_ID}).",
        "x402": {
            "version": "1.0",
            "chain_id": CHAIN_ID,
            "network": "Polygon Mainnet",
            "token": "USDC",
            "token_contract": USDC_CONTRACT_ADDRESS,
            "recipient": RECIPIENT_WALLET,
            "amount": str(REQUIRED_AMOUNT_USDC),
            "amount_raw": str(REQUIRED_RAW_AMOUNT),
            "decimals": USDC_DECIMALS,
            "instructions": f"Transfer {REQUIRED_AMOUNT_USDC} USDC to {RECIPIENT_WALLET} on Polygon, then include header 'X-Payment-Tx: <TX_HASH>'."
        }
    }

def verify_payment_tx(tx_hash: str) -> tuple[bool, str]:
    """
    Polygon 메인넷 상의 USDC 입금 트랜잭션을 온체인 검증합니다.
    1. 해시 포맷 및 재사용(Replay) 검사
    2. 트랜잭션 실행 성공(status == 1) 여부
    3. USDC 컨트랙트 및 Transfer 로그 확인 (수신 주소 및 0.01 USDC 이상)
    """
    if not tx_hash or not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
        return False, "Invalid transaction hash format. Expected 0x prefixed 64 hex string."

    tx_hash_lower = tx_hash.lower()
    if tx_hash_lower in processed_txs:
        return False, "Transaction hash has already been consumed (Replay protection)."

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if not receipt:
            return False, f"Transaction '{tx_hash}' not found on Polygon Mainnet."

        if receipt.get("status") != 1:
            return False, "Transaction was reverted or failed on-chain (status == 0)."

        payment_found = False
        for log in receipt.get("logs", []):
            # 컨트랙트 주소 확인
            if Web3.to_checksum_address(log.get("address")) != USDC_CONTRACT_ADDRESS:
                continue

            topics = log.get("topics", [])
            if not topics or topics[0].hex().lower() != TRANSFER_EVENT_TOPIC.lower():
                continue

            # Transfer(from, to, value) -> topic[1]=from, topic[2]=to
            if len(topics) >= 3:
                to_addr_hex = "0x" + topics[2].hex()[-40:]
                to_address = Web3.to_checksum_address(to_addr_hex)

                # Transfer value 파싱
                raw_data = log.get("data")
                if isinstance(raw_data, bytes):
                    amount = int.from_bytes(raw_data, byteorder="big")
                elif isinstance(raw_data, str):
                    amount = int(raw_data, 16)
                else:
                    amount = 0

                # 수신 주소 및 결제 금액 확인
                if to_address == RECIPIENT_WALLET and amount >= REQUIRED_RAW_AMOUNT:
                    payment_found = True
                    break

        if not payment_found:
            return False, f"No valid USDC Transfer to recipient '{RECIPIENT_WALLET}' for >= {REQUIRED_AMOUNT_USDC} USDC in tx logs."

        # 유효한 결제 트랜잭션 기록
        processed_txs.add(tx_hash_lower)
        return True, "Payment verified successfully."

    except Exception as e:
        return False, f"On-chain verification error: {str(e)}"

def extract_clean_markdown_for_ai(html_content: str, source_url: str) -> tuple[str, str, str]:
    """
    HTML 웹 문서를 AI/LLM에 최적화된 마크다운 구조로 정제합니다.
    - 광고, 내비게이션, 스크립트, 푸터, iframe, SVG, 주석 등 노이즈 태그 제거
    - 구조화된 헤딩(h1~h6), 목록(ul/ol), 인용구, 코드블록, 본문 단락 추출
    - 메타 디스크립션 및 본문 텍스트 요약 지원
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # 주석 및 노이즈 요소 제거
    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    noise_tags = [
        "script", "style", "nav", "footer", "header", "aside",
        "noscript", "iframe", "svg", "form", "button", "input"
    ]
    for tag in soup(noise_tags):
        tag.decompose()

    # 제목 추출
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text().strip()
    else:
        title = source_url

    # 메타 디스크립션 추출
    meta_desc = ""
    desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or \
               soup.find("meta", attrs={"property": "og:description"})
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    # 주요 본문 컨테이너 선택
    container = soup.find("article") or soup.find("main") or soup.find("body") or soup

    # AI 친화적 마크다운 변환
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
    # 연속된 빈 줄 정리
    clean_markdown = re.sub(r"\n{3,}", "\n\n", clean_markdown)

    return title, meta_desc, clean_markdown

@app.get("/")
def read_root():
    return {
        "service": "Polygon x402 Micro-Payment AI Clean Web Agent",
        "chain_id": CHAIN_ID,
        "token": "USDC (0.01 required)",
        "recipient": RECIPIENT_WALLET,
        "endpoint": "/api/v1/clean-web?url=<URL>",
        "docs": "/docs"
    }

@app.get("/api/v1/clean-web")
def clean_web_endpoint(
    url: str = Query(..., description="Target web page URL to clean for AI ingestion"),
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Tx Hash for 0.01 USDC payment")
):
    """
    x402 결제 검증 및 AI용 마크다운 웹 스크래핑 엔드포인트:
    - X-Payment-Tx 헤더가 없거나 온체인 결제 미확인 시: HTTP 402 및 지갑/결제 안내 반환
    - 결제 확인 완료 시: 대상 URL 콘텐츠를 AI에 최적화된 마크다운 텍스트로 정제하여 반환
    """
    # 1. 헤더 존재 여부 확인
    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data()
        )

    # 2. 온체인 트랜잭션 검증
    is_valid, reason = verify_payment_tx(x_payment_tx)
    if not is_valid:
        res_data = get_402_response_data()
        res_data["verification_error"] = reason
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=res_data
        )

    # 3. 타겟 URL 콘텐츠 수집
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching target URL '{url}': {str(e)}"
        )

    # 4. AI용 마크다운 정제
    title, meta_desc, markdown_content = extract_clean_markdown_for_ai(resp.text, url)

    return {
        "status": "success",
        "url": url,
        "title": title,
        "description": meta_desc,
        "payment": {
            "tx_hash": x_payment_tx,
            "chain_id": CHAIN_ID,
            "token": "USDC",
            "amount": REQUIRED_AMOUNT_USDC
        },
        "markdown_content": markdown_content
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
