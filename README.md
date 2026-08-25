# ⚡ Polygon x402 AI Autonomous Agent Suite (v2.1.0)

> **Turn any messy webpage, YouTube video, PDF paper, or research query into token-optimized, structured Markdown and JSON.**  
> *Zero Sign-up. Zero API Key Friction. True Machine-to-Machine Web3 Micropayments & Free Discovery Trials for Autonomous AI Agents.*

[![PyPI version](https://img.shields.io/pypi/v/x402-cleanweb-agent.svg?color=blue&label=PyPI%20Package)](https://pypi.org/project/x402-cleanweb-agent/)
[![Glama.ai](https://img.shields.io/badge/Glama.ai-Listed-00ffcc?style=for-the-badge&logo=anthropic&logoColor=black)](https://glama.ai/mcp/servers/nohosa001-pixel/x402-cleanweb-agent)
[![Live Gateway](https://img.shields.io/badge/GCP%20Cloud%20Run-Online-00f2fe?style=for-the-badge&logo=googlecloud&logoColor=white)](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app)
[![Swagger API](https://img.shields.io/badge/API%20Docs-Swagger-8247e5?style=for-the-badge&logo=fastapi&logoColor=white)](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/docs)
[![Polygon Web3](https://img.shields.io/badge/Polygon-USDC_Mainnet-purple.svg)](https://polygonscan.com/token/0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 💡 Why x402-cleanweb-agent? (Economic Arbitrage for LLMs)

Traditional web scraping and data extraction APIs force expensive **$49/month subscriptions** and complex API key management.

`x402-cleanweb-agent` provides **mathematical economic efficiency** for autonomous AI agents, scrapers, and developers:

- 🎁 **Zero-Friction Discovery Trial**: Attach header `X-Agent-Nonce: <UUID>` for **3 free trial queries** out of the box.
- ⚡ **0ms Latency Prepaid Pass**: Mint a credit pass via `POST /api/v1/pass/mint` (1 USDC = 100 calls) for instant, zero-gas responses.
- 📊 **87% LLM Token Reduction**: Raw HTML (20k tokens) is compressed to clean Markdown (3k tokens), saving **65% net dollar cost** per query.
- 📐 **Live Arbitrage ROI Calculator**: `GET /api/v1/agent/arbitrage-roi` proves a **445% ROI** over direct web scraping.
- 🤖 **Zero-Human AI Agent Ready**: AI agents with a crypto wallet can autonomously discover, negotiate, and purchase data 24/7.
- 🧠 **Self-Healing Error Protocol**: Machine-readable `HTTP 402` JSON guide for autonomous on-chain retry.
- 🤝 **Agent-to-Agent Referral Cashback**: 10% on-chain credit cashback for recommending agents.

---

## 🚀 Live Gateway & Machine Discovery Endpoints

- 🌐 **Live Gateway**: [https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app)
- 📑 **LLM Documentation**: [https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/llms.txt](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/llms.txt)
- 🤖 **Agent Manifest**: [https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/.well-known/agent.json](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/.well-known/agent.json)
- 🔌 **AI Plugin Manifest**: [https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/.well-known/ai-plugin.json](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/.well-known/ai-plugin.json)
- 🃏 **MCP Server Card**: [https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/.well-known/mcp/server-card.json](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/.well-known/mcp/server-card.json)
- 📚 **Swagger Interactive Docs**: [https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/docs](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/docs)

---

## 🛠️ Service Catalog & Pricing

| Service | Endpoint | Price (USDC) | Credits | Description |
| :--- | :--- | :--- | :--- | :--- |
| **🎁 Free Discovery Trial** | Any Endpoint | **FREE (3 queries)** | 0 Credits | Header `X-Agent-Nonce: <UUID>` |
| **🌐 Clean Web** | `GET /api/v1/clean-web` | **0.01 USDC** | 1 Credit | Strips ads/clutter, returns pure Markdown with 60-85% token savings |
| **📦 Batch Clean** | `POST /api/v1/batch-clean` | **0.01 / URL** | 1 Credit/URL | Scrapes up to 10 URLs concurrently in parallel |
| **🎬 YouTube Transcript** | `GET /api/v1/clean-youtube` | **0.02 USDC** | 2 Credits | Full timestamped video transcripts formatted in Markdown |
| **📑 PDF Paper Extractor** | `GET /api/v1/clean-pdf` | **0.05 USDC** | 5 Credits | Converts arXiv research papers and reports into clean Markdown |
| **📝 Pure Text Extractor** | `GET /api/v1/clean-text` | **0.005 USDC** | 1 Credit | Ultra-lightweight raw text for vector/RAG embeddings |
| **📊 Structured JSON** | `POST /api/v1/extract-json` | **0.03 USDC** | 3 Credits | Extracts key-value structured JSON matching user-defined schema |
| **🧠 Deep Research** | `GET /api/v1/deep-research` | **0.15 USDC** | 15 Credits | Multi-source synthesized AI executive research briefing |
| **📐 Arbitrage ROI Calc** | `GET /api/v1/agent/arbitrage-roi` | **FREE** | 0 Credits | Mathematical cost-benefit ROI calculator |
| **🎟️ Mint Credit Pass** | `POST /api/v1/pass/mint` | **1.0 / 5.0 USDC** | 100 / 600 | Zero-latency prepaid pass (20% bonus on 5 USDC) |

---

## 📦 Quick Installation

```bash
# Standard installation from PyPI
pip install x402-cleanweb-agent

# Or run instantly without installation via uvx
uvx x402-cleanweb-agent
```

---

## 🤖 Zero-Human Autonomous AI Agent Integration & Tools

```python
from agent_tools import X402AgentToolkit

# 1. Initialize toolkit (automatic 3 free discovery trials)
toolkit = X402AgentToolkit(
    private_key="0xYOUR_AGENT_PRIVATE_KEY", # Optional if using prepaid pass or free trial
    max_daily_budget_usdc=1.0               # Built-in Budget Guard protection
)

# 2. Check economic ROI before scraping
roi_report = toolkit.agent_client.get_arbitrage_roi()
print(roi_report["economic_arbitrage"])

# 3. Clean single webpage
web_data = toolkit.clean_web("https://news.ycombinator.com", density="compact")
print(web_data)

# 4. Extract structured JSON
json_data = toolkit.extract_json("https://news.ycombinator.com", "top 5 titles and links")
print(json_data)

# 5. Execute AI Deep Research
briefing = toolkit.deep_research("Autonomous AI Agent Economic Protocols")
print(briefing)
```

---

## 💻 1-Second Setup for Claude & Cursor (MCP)

Add to your `claude_desktop_config.json` or Cursor MCP settings:

```json
{
  "mcpServers": {
    "polygon-x402-cleanweb": {
      "command": "uvx",
      "args": ["x402-cleanweb-agent"]
    }
  }
}
```

---

## 📄 License & Attribution

Distributed under the **MIT License**. Hosted on **Google Cloud Run** and powered by **Polygon Mainnet (Chain ID 137)**.
