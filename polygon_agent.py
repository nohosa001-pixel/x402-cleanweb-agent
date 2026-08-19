import os
import re
from typing import Optional, Set
from fastapi import FastAPI, Header, Query, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3
from bs4 import BeautifulSoup
import requests

from dotenv import load_dotenv

# .env 로드 (환경변수 덮어쓰기 허용)
load_dotenv(override=True)

app = FastAPI(
    title="Polygon x402 Micro-Payment Clean Web Agent",
    description="x402 Protocol Implementation for Web3 Micropayments on Polygon",
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
# Native USDC on Polygon
USDC_CONTRACT_ADDRESS = Web3.to_checksum_address(
    os.getenv("USDC_CONTRACT_ADDRESS", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
)
USDC_DECIMALS = 6
REQUIRED_AMOUNT_USDC = float(os.getenv("PAYMENT_AMOUNT_USDC", "0.01"))
REQUIRED_RAW_AMOUNT = int(REQUIRED_AMOUNT_USDC * (10 ** USDC_DECIMALS)) # 10,000 units (0.01 USDC)

# Server Recipient Wallet
RECIPIENT_WALLET = Web3.to_checksum_address(
    os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")
)

def get_web3_instance():
    for rpc in POLYGON_RPC_URLS:
        try:
            w3_inst = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
            if w3_inst.is_connected():
                return w3_inst
        except Exception:
            continue
    return Web3(Web3.HTTPProvider(POLYGON_RPC_URLS[0]))

w3 = get_web3_instance()

# 중복 결제(Replay Attack) 방지용 처리된 트랜잭션 저장소 (메모리 캐시)
processed_txs: Set[str] = set()

# ERC20 Transfer 이벤트 토픽 keccak256("Transfer(address,address,uint256)")
TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def get_402_response_data():
    return {
        "status": "error",
        "error": "Payment Required",
        "message": f"Payment of {REQUIRED_AMOUNT_USDC} USDC required on Polygon network to access this resource.",
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
            "instructions": "Send 0.01 USDC on Polygon network to the recipient wallet and retry request with header 'X-Payment-Tx: <TX_HASH>'."
        }
    }

def verify_payment_tx(tx_hash: str) -> tuple[bool, str]:
    """
    Polygon 상의 트랜잭션 해시를 검증합니다.
    1. 트랜잭션 형식 및 중복 여부 확인
    2. 영수증(Receipt) 확인 (성공 상태 여부)
    3. USDC Transfer 이벤트 로그 확인 (수신 주소 및 결제 금액 확인)
    """
    if not tx_hash or not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
        return False, "Invalid transaction hash format. Must be 0x followed by 64 hex characters."

    tx_hash_normalized = tx_hash.lower()
    if tx_hash_normalized in processed_txs:
        return False, "Transaction hash has already been used (replay detected)."

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if not receipt:
            return False, "Transaction receipt not found on Polygon mainnet."

        if receipt.get("status") != 1:
            return False, "Transaction failed on-chain (status != 1)."

        # USDC Transfer 이벤트 로그 파싱
        payment_verified = False
        for log in receipt.get("logs", []):
            # 토큰 컨트랙트 검증
            if Web3.to_checksum_address(log.get("address")) != USDC_CONTRACT_ADDRESS:
                continue

            topics = log.get("topics", [])
            if not topics or topics[0].hex().lower() != TRANSFER_EVENT_TOPIC.lower():
                continue

            # Transfer(from, to, value)
            # topic[1]: from (indexed), topic[2]: to (indexed)
            if len(topics) >= 3:
                # topic[2]에서 수신자 주소 추출 (32바이트 중 마지막 20바이트)
                to_addr_hex = "0x" + topics[2].hex()[-40:]
                to_address = Web3.to_checksum_address(to_addr_hex)
                
                # data에서 금액 파싱
                raw_data = log.get("data")
                if isinstance(raw_data, bytes):
                    amount = int.from_bytes(raw_data, byteorder="big")
                elif isinstance(raw_data, str):
                    amount = int(raw_data, 16)
                else:
                    amount = 0

                if to_address == RECIPIENT_WALLET and amount >= REQUIRED_RAW_AMOUNT:
                    payment_verified = True
                    break

        if not payment_verified:
            return False, f"No valid USDC Transfer to {RECIPIENT_WALLET} with amount >= {REQUIRED_AMOUNT_USDC} USDC found in transaction logs."

        # 검증 성공 시 재사용 방지 목록에 추가
        processed_txs.add(tx_hash_normalized)
        return True, "Payment verified successfully."

    except Exception as e:
        return False, f"Failed to verify transaction on-chain: {str(e)}"

def html_to_clean_markdown(html_content: str, url: str) -> tuple[str, str]:
    """
    HTML 콘텐츠에서 불필요한 태그(스크립트, 스타일, 광고, 내비게이션 등)를 제거하고
    핵심 본문과 제목을 마크다운 텍스트로 변환합니다.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # 불필요한 태그 제거
    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe", "svg", "aside"]):
        element.decompose()

    # 페이지 제목 추출
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text().strip()
    else:
        title = url

    # 본문 영역 탐색 우선순위 (article, main, body)
    main_content = soup.find("article") or soup.find("main") or soup.find("body") or soup

    # 헤딩 및 텍스트 구조 변환
    lines = []
    if title:
        lines.append(f"# {title}\n")
        lines.append(f"> Source: [{url}]({url})\n")

    for elem in main_content.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre", "code"]):
        tag_name = elem.name
        text = elem.get_text().strip()
        if not text:
            continue

        if tag_name == "h1":
            lines.append(f"\n# {text}\n")
        elif tag_name == "h2":
            lines.append(f"\n## {text}\n")
        elif tag_name == "h3":
            lines.append(f"\n### {text}\n")
        elif tag_name in ["h4", "h5", "h6"]:
            lines.append(f"\n#### {text}\n")
        elif tag_name == "li":
            lines.append(f"- {text}")
        elif tag_name == "blockquote":
            lines.append(f"\n> {text}\n")
        elif tag_name in ["pre", "code"]:
            lines.append(f"\n```\n{text}\n```\n")
        else: # p
            lines.append(f"\n{text}\n")

    markdown_text = "\n".join(lines).strip()
    return title, markdown_text

@app.get("/")
def root():
    return {
        "service": "Polygon x402 Micro-Payment Clean Web Agent",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "/api/v1/clean-web": "Fetches and cleans web content in markdown after 0.01 USDC payment on Polygon."
        }
    }

@app.get("/api/v1/clean-web")
def clean_web(
    url: str = Query(..., description="Target web page URL to fetch and clean into Markdown"),
    x_payment_tx: Optional[str] = Header(None, alias="X-Payment-Tx", description="Polygon Transaction Hash for 0.01 USDC micropayment")
):
    """
    x402 마이크로 결제 기반 Clean Web 엔드포인트:
    - X-Payment-Tx 헤더가 없거나 검증에 실패하면 HTTP 402 반환
    - 검증 성공 시 타겟 URL의 HTML 본문을 파싱하여 클린 마크다운으로 반환
    """
    # 1. 결제 트랜잭션 헤더 존재 여부 확인
    if not x_payment_tx:
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=get_402_response_data()
        )

    # 2. 온체인 트랜잭션 유효성 검증
    is_valid, reason = verify_payment_tx(x_payment_tx)
    if not is_valid:
        response_data = get_402_response_data()
        response_data["verification_error"] = reason
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=response_data
        )

    # 3. URL 스크래핑 및 파싱
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch content from target URL '{url}': {str(e)}"
        )

    # 4. 마크다운 변환
    title, markdown_content = html_to_clean_markdown(res.text, url)

    return {
        "status": "success",
        "url": url,
        "title": title,
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
    uvicorn.run("polygon_agent:app", host="0.0.0.0", port=8000, reload=True)
