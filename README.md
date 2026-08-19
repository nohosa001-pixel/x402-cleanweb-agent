# Polygon x402 Micro-Payment AI Clean Web Agent

폴리곤(Polygon Mainnet) 상에서 **0.01 USDC** 결제를 온체인으로 검증하고, 웹페이지 본문을 AI/LLM 프롬프트에 바로 주입 가능한 구조화된 **Clean Markdown** 형태로 변환하여 반환하는 Web3 마이크로 결제 서버입니다.

---

## 🚀 주요 기능

1. **HTTP 402 Payment Required (x402 규격)**
   - `X-Payment-Tx` 헤더가 없거나 유효하지 않은 트랜잭션일 경우 HTTP 402 응답.
   - 내 폴리곤 지갑 주소, 체인 ID(137), 0.01 USDC 컨트랙트 주소 및 입금 안내 반환.
2. **Polygon 메인넷 온체인 검증 (`web3.py`)**
   - 네이티브 USDC 컨트랙트 (`0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359`)의 `Transfer` 이벤트 검증.
   - 수신 주소 일치 여부 및 0.01 USDC (10,000 raw unit) 입금 확인.
   - 재사용 공격(Replay Attack) 방지.
3. **AI용 마크다운 정제 파서 (`beautifulsoup4`)**
   - 스크립트, 광고, 내비게이션, 푸터 등 불필요한 노이즈 태그 제거.
   - 제목, 메타 디스크립션, 헤딩 계층, 코드블록, 인용구 등을 마크다운으로 깔끔하게 변환.

---

## 🛠 실행 방법

### 1. 가상환경 활성화 및 패키지 설치

```bash
# 가상환경 생성 및 패키지 설치
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (`.env`)

`.env` 파일에서 본인의 수신 지갑 주소를 설정합니다.

```env
POLYGON_RPC_URL=https://polygon-bor-rpc.publicnode.com
USDC_CONTRACT_ADDRESS=0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359
SERVER_WALLET_ADDRESS=0x255F9991233f86B29dB847c8d5b8CB9915e80dCf
PAYMENT_AMOUNT_USDC=0.01
```

### 3. 서버 실행

```bash
python main.py
# 또는
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🤖 MCP (Model Context Protocol) 서버로 사용하기

AI 에이전트(Antigravity, Claude Desktop, Cursor 등)가 도구를 호출할 때마다 지갑으로 USDC 결제가 이루어지는 **Agent-to-Agent Micro-Payment Tool**로 사용할 수 있습니다.

### MCP 도구 목록

- `get_payment_info()`: 결제 수신 지갑, 네트워크, 금액 안내
- `fetch_clean_web_content(url, payment_tx_hash)`:
  - `payment_tx_hash`가 없으면 **HTTP 402 결제 안내** 반환
  - `payment_tx_hash` 제공 시 온체인 0.01 USDC 검증 후 AI 마크다운 반환

### MCP 서버 설정 예시 (`mcp_config.json`)

```json
{
  "mcpServers": {
    "polygon-x402-cleanweb": {
      "command": "python",
      "args": [
        "c:/Users/nohos/OneDrive/바탕 화면/x402-micro-agent/mcp_server.py"
      ]
    }
  }
}
```

---

## 📡 API 사용 예시

### [엔드포인트] `GET /api/v1/clean-web?url=<TARGET_URL>`

#### 1. 결제 전 요청 (HTTP 402 반환)

```bash
curl -i "http://localhost:8000/api/v1/clean-web?url=https://example.com"
```

**응답:**

```json
{
  "status": "error",
  "error": "Payment Required",
  "message": "Payment of 0.01 USDC is required on Polygon (Chain ID: 137).",
  "x402": {
    "version": "1.0",
    "chain_id": 137,
    "network": "Polygon Mainnet",
    "token": "USDC",
    "token_contract": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    "recipient": "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf",
    "amount": "0.01",
    "amount_raw": "10000",
    "decimals": 6,
    "instructions": "Transfer 0.01 USDC to 0x255F9991233f86B29dB847c8d5b8CB9915e80dCf on Polygon, then include header 'X-Payment-Tx: <TX_HASH>'."
  }
}
```

#### 2. 결제 후 트랜잭션 해시 포함 요청 (HTTP 200)

```bash
curl -H "X-Payment-Tx: 0xYourPolygonTxHash..." "http://localhost:8000/api/v1/clean-web?url=https://example.com"
```

**응답:**

```json
{
  "status": "success",
  "url": "https://example.com",
  "title": "Example Domain",
  "description": "",
  "payment": {
    "tx_hash": "0xYourPolygonTxHash...",
    "chain_id": 137,
    "token": "USDC",
    "amount": 0.01
  },
  "markdown_content": "# Example Domain\n\n> **Source URL**: https://example.com\n\nThis domain is for use in illustrative examples in documents..."
}
```
