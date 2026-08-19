# Polygon x402 Micro-Payment AI Data Agent Suite

폴리곤(Polygon Mainnet) 상에서 **0.005~0.05 USDC** 마이크로 결제를 온체인으로 검증하고, 웹페이지, **YouTube 영상 자막**, **PDF 논문/보고서**, **순수 텍스트**를 AI/LLM 프롬프트에 최적화된 형태로 변환하여 반환하는 종합 Web3 AI 데이터 에이전트 서비스입니다.

---

## 🚀 제공 서비스 및 가격표 (x402 Protocol)

| 서비스 | 엔드포인트 | 결제 금액 | 기능 설명 |
| :--- | :--- | :--- | :--- |
| **🌐 Clean Web** | `GET /api/v1/clean-web` | **0.01 USDC** | 광고/노이즈 제거 + AI 마크다운 + **토큰 절감 통계** |
| **🎬 YouTube Transcript** | `GET /api/v1/clean-youtube` | **0.02 USDC** | 유튜브 영상 **전체 자막 & 타임스탬프** 마크다운 정제 |
| **📑 PDF Paper & Report** | `GET /api/v1/clean-pdf` | **0.05 USDC** | arXiv 논문, 공시 보고서 PDF **페이지별 구조화 마크다운** |
| **📝 Pure Plain Text** | `GET /api/v1/clean-text` | **0.005 USDC** | 초경량 순수 텍스트 추출 |

---

## 💡 주요 특징

1. **HTTP 402 Payment Required (x402 규격)**
   - `X-Payment-Tx` 헤더 누락 시 402 응답 및 결제 가이드 반환.
2. **Polygon 메인넷 온체인 검증 (`web3.py`)**
   - Native USDC (`0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359`) Transfer 이벤트 검증.
   - 수신 주소(`0x255F9991233f86B29dB847c8d5b8CB9915e80dCf`) 일치 및 Replay Attack 방지.
3. **AI 토큰 절감 통계 분석**
   - 원본 대비 마크다운 변환 시 절감된 토큰 수(%) 및 절약된 LLM 비용 추정치 반환.
4. **Web3 DApp UI 제공**
   - 메타마스크 지갑 연결 후 브라우저에서 원클릭 결제 및 결과 복사 가능.

---

## 🛠 실행 방법

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
# 또는 원클릭 실행: run_server.bat
```

---

## 🤖 MCP (Model Context Protocol) 도구 목록

- `get_payment_info()`: 결제 요금표 및 지갑 주소 안내
- `fetch_clean_web_content(url, payment_tx_hash)`: 0.01 USDC 웹 정제
- `fetch_youtube_transcript(url, language, payment_tx_hash)`: 0.02 USDC 유튜브 자막 추출
- `fetch_pdf_markdown(url, payment_tx_hash)`: 0.05 USDC PDF 논문/보고서 추출
- `fetch_plain_text(url, payment_tx_hash)`: 0.005 USDC 순수 텍스트 추출
