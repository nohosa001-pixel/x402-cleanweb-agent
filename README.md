# Polygon x402 Micro-Payment AI Data Agent Suite

A production-grade Web3 AI Data Agent Suite powered by the **HTTP 402 Payment Required (x402)** protocol on **Polygon Mainnet**. It enables on-chain verified **0.005 ~ 0.05 USDC** micro-payments for converting raw web pages, **YouTube video transcripts**, **PDF research papers**, and **plain text** into AI/LLM-optimized clean Markdown.

---

## 🚀 Live Demo & Endpoints

- **Live Web3 DApp**: [https://x402-cleanweb-agent.onrender.com](https://x402-cleanweb-agent.onrender.com)
- **Interactive Swagger Docs**: [https://x402-cleanweb-agent.onrender.com/docs](https://x402-cleanweb-agent.onrender.com/docs)

| Service | Endpoint | Pricing | Description |
| :--- | :--- | :--- | :--- |
| **🌐 Clean Web** | `GET /api/v1/clean-web` | **0.01 USDC** | Ad/Noise removal + AI-ready Markdown + **Token savings analytics** |
| **🎬 YouTube Transcript** | `GET /api/v1/clean-youtube` | **0.02 USDC** | Complete video **transcripts with timestamps** formatted in Markdown |
| **📑 PDF Paper & Report** | `GET /api/v1/clean-pdf` | **0.05 USDC** | arXiv papers & financial reports converted to **structured Markdown** |
| **📝 Pure Plain Text** | `GET /api/v1/clean-text` | **0.005 USDC** | Ultra-lightweight raw text extraction |

---

## 💡 Key Features

1. **Autonomous HTTP 402 Protocol (x402)**
   - Requests without payment return `402 Payment Required` with complete on-chain transfer instructions.
   - Attach the transaction hash in the `X-Payment-Tx` header to unlock data.
2. **Polygon Mainnet On-Chain Verification (`web3.py`)**
   - Direct verification of native USDC (`0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359`) transfer logs.
   - Exact recipient verification (`0x255F9991233f86B29dB847c8d5b8CB9915e80dCf`) with replay attack protection.
3. **AI Token Savings & Analytics**
   - Calculates raw vs. cleaned token counts, percentage savings, and estimated LLM prompt cost savings ($).
4. **Global Web3 DApp UI**
   - Sleek dark-mode interface with MetaMask / Web3 wallet integration and bilingual (English / Korean) toggle support.
5. **Model Context Protocol (MCP) Ready**
   - Full MCP server support (`mcp_server.py`) for direct integration with Cursor, Claude Desktop, and AI agents.

---

## 🛠 Local Setup & Running

```bash
# 1. Clone repository & setup virtual environment
git clone https://github.com/nohosa001-pixel/x402-cleanweb-agent.git
cd x402-cleanweb-agent
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start server
python main.py
# Or run with batch script: run_server.bat
```

---

## 🤖 MCP (Model Context Protocol) Tools

- `get_payment_info()`: Retrieve pricing table and recipient wallet address.
- `fetch_clean_web_content(url, payment_tx_hash)`: Clean web scraper (0.01 USDC).
- `fetch_youtube_transcript(url, language, payment_tx_hash)`: YouTube transcript scraper (0.02 USDC).
- `fetch_pdf_markdown(url, payment_tx_hash)`: PDF paper to markdown converter (0.05 USDC).
- `fetch_plain_text(url, payment_tx_hash)`: Lightweight plain text extractor (0.005 USDC).

---

## 📄 License & Standards

- Protocol: [HTTP 402 Payment Required (x402)](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#402)
- Blockchain: Polygon Mainnet (Chain ID: `137`)
