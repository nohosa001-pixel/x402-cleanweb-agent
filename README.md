# Polygon x402 Micro-Payment AI Data Agent

폴리곤(Polygon Mainnet) 상에서 **0.01~0.02 USDC** 마이크로 결제를 온체인으로 검증하고, 웹페이지 본문 및 **YouTube 영상 자막/스크립트**를 AI/LLM 프롬프트에 최적화된 **Clean Markdown** 형태로 변환하여 반환하는 Web3 데이터 에이전트 서비스입니다.

---

## 🚀 제공 서비스 및 가격 (x402 Protocol)

| 엔드포인트 | 결제 금액 | 설명 |
| :--- | :--- | :--- |
| `GET /api/v1/clean-web` | **0.01 USDC** | 웹페이지 광고/노이즈 제거 + AI 마크다운 + **토큰 절감 통계** |
| `GET /api/v1/clean-youtube` | **0.02 USDC** | **유튜브 전체 자막 & 타임스탬프** 마크다운 정제 |

---

## 💡 주요 기능

1. **HTTP 402 Payment Required (x402 규격)**
   - `X-Payment-Tx` 헤더 누락 시 402 응답 및 0.01~0.02 USDC 입금 가이드 반환.
2. **Polygon 메인넷 온체인 검증 (`web3.py`)**
   - Native USDC (`0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359`) Transfer 이벤트 검증.
   - 수신 주소(`0x255F9991233f86B29dB847c8d5b8CB9915e80dCf`) 일치 및 Replay Attack 방지.
3. **AI 토큰 절감 통계 분석**
   - 원본 대비 마크다운 변환 시 절감된 토큰 수(%) 및 절약된 LLM 비용 추정치 반환.
4. **유튜브 자막 마크다운 파서 (`youtube-transcript-api`)**
   - 긴 영상도 타임스탬프별 마크다운 목록으로 즉시 정제.

---

## 🛠 실행 방법

### 1. 가상환경 활성화 및 패키지 설치

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (`.env`)

```env
POLYGON_RPC_URL=https://polygon-bor-rpc.publicnode.com
USDC_CONTRACT_ADDRESS=0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359
SERVER_WALLET_ADDRESS=0x255F9991233f86B29dB847c8d5b8CB9915e80dCf
```

### 3. 서버 실행

```bash
python main.py
# 또는 원클릭 실행: run_server.bat
```

---

## 🤖 MCP (Model Context Protocol) 도구

AI 에이전트(Claude Desktop, Cursor, Antigravity) 연동 도구:

- `get_payment_info()`: 결제 요금표 및 지갑 주소 안내
- `fetch_clean_web_content(url, payment_tx_hash)`: 0.01 USDC 웹 정제
- `fetch_youtube_transcript(url, language, payment_tx_hash)`: 0.02 USDC 유튜브 자막 추출

---

## 📡 API 요청 예시

### [1] 웹 정제 요청 (`/api/v1/clean-web`)

```bash
curl -H "X-Payment-Tx: 0xYourPolygonTxHash..." "http://localhost:8000/api/v1/clean-web?url=https://example.com"
```

### [2] 유튜브 자막 요청 (`/api/v1/clean-youtube`)

```bash
curl -H "X-Payment-Tx: 0xYourPolygonTxHash..." "http://localhost:8000/api/v1/clean-youtube?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```
