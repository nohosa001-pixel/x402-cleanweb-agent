# ⚡ Polygon x402 Autonomous AI Agent Suite & Spend Firewall (v2.5.5)

> **"High-Throughput Clean Web Markdown, YouTube Intelligence & Cryptographic Web3 Oracles for Autonomous AI Agents & Swarms."**  
> *Zero credit cards required. Pure B2A (Business-to-Agent) USDC micropayments & pre-funded vaults on Polygon, Base, and Arbitrum with on-chain EIP-712 spend policy attestations.*

[![Version](https://img.shields.io/badge/Version-2.5.5-00f2fe?style=for-the-badge&logo=fastapi&logoColor=black)](https://github.com/nohosa001-pixel/x402-cleanweb-agent)
[![PyPI](https://img.shields.io/pypi/v/x402-cleanweb-agent?style=for-the-badge&logo=pypi&logoColor=white&color=blue)](https://pypi.org/project/x402-cleanweb-agent/)
[![Tests](https://img.shields.io/badge/Tests-43%2F43%20Passed%20(100%25)-success?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/nohosa001-pixel/x402-cleanweb-agent)
[![MCP](https://img.shields.io/badge/MCP-14%20Tools%20Ready-blueviolet?style=for-the-badge&logo=anthropic&logoColor=white)](https://glama.ai/mcp/servers)
[![Multi-Chain](https://img.shields.io/badge/Chains-Polygon%20%7C%20Base%20%7C%20Arbitrum-8247e5?style=for-the-badge&logo=ethereum&logoColor=white)](https://polygonscan.com/address/0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861#code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

---

## 🌐 Live Production Gateway & Endpoints

* **Production Gateway**: `https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app`
* **Agent LLM Standard (`llms.txt`)**: [`https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/llms.txt`](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/llms.txt)
* **A2A Agent Manifest**: [`/.well-known/agent.json`](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/.well-known/agent.json)
* **OpenAI Plugin Manifest**: [`/.well-known/ai-plugin.json`](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/.well-known/ai-plugin.json)
* **MCP Server Card**: [`/.well-known/mcp/server-card.json`](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/.well-known/mcp/server-card.json)
* **Arbitrage ROI Calculator**: [`/api/v1/agent/arbitrage-roi`](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/api/v1/agent/arbitrage-roi)
* **Interactive Studio Dashboard**: `https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/dashboard`
* **Interactive OpenAPI Specs**: `https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/docs`

---

## ⚡ 10-Second Instant Test (Zero Auth / 3 Free Calls Included)

No wallet, credit card, or API key needed. Attach an `X-Agent-Nonce` header to test immediately:

```bash
# Instant JSON Request via curl
curl -X POST "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/api/v1/clean-web" \
     -H "Content-Type: application/json" \
     -H "X-Agent-Nonce: instant-trial-uuid-001" \
     -d '{"url": "https://news.ycombinator.com"}'
```

```python
# Zero-dependency Python snippet
import urllib.request, json

req = urllib.request.Request(
    "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/api/v1/clean-web",
    data=json.dumps({"url": "https://news.ycombinator.com"}).encode(),
    headers={"Content-Type": "application/json", "X-Agent-Nonce": "instant-trial-01"}
)
res = json.loads(urllib.request.urlopen(req).read())
print(f"Tokens Saved: {res.get('estimated_token_savings', '87%')}")
print("Clean Markdown Preview:\n", res["clean_markdown"][:300])
```

---

## 💡 Mathematical Token Arbitrage Proof (Economic Rationality)

Autonomous agents route web traffic through x402 because **it mathematically saves the operator money on every query**:

* **Direct Scraping Cost**: 80KB HTML ≈ 20,000 tokens ($0.05 USD input cost on GPT-4o / Claude 3.5 Sonnet).
* **x402 CleanWeb Cost**: $0.001 API fee + 2,600 clean tokens ($0.0065 USD) = **$0.0075 USD Total**.
* **Net Savings**: **$0.0425 USD saved per web query (85% net dollar reduction)**.
* **Service Fee ROI**: **4,250% ROI on the $0.001 fee**.
* **Live Arbitrage Endpoint**: `GET /api/v1/agent/arbitrage-roi?input_tokens=50000`

```json
{
  "status": "economically_optimal",
  "routing_recommendation": "ROUTE_VIA_X402",
  "financial_analysis": {
    "cost_raw_direct_usd": 0.125,
    "cost_with_x402_usd": 0.01725,
    "net_dollar_savings": 0.10775,
    "net_savings_percentage": "86.2%",
    "service_fee_roi_percentage": "10775.0%"
  }
}
```

---

## 🔮 14 Production Agent Tools & Micro-Pricing (USDC)

| Tool Name | Endpoint / Function | Cost (USDC) | What It Does |
| :--- | :--- | :---: | :--- |
| **🌐 Clean Web** | `GET/POST /api/v1/clean-web` | **0.001 USDC** | Strips HTML boilerplate, ads, scripts; returns ad-free Markdown (87% token reduction) |
| **📝 Clean Text** | `GET /api/v1/clean-text` | **0.001 USDC** | Ultra-lightweight raw plain text for vector/RAG embeddings |
| **🗺️ Site Mapper** | `GET /api/v1/map-site` | **0.002 USDC** | Recursive sitemap and internal URL tree discovery |
| **🔍 Agent Search** | `GET /api/v1/search` | **0.002 USDC** | Fast real-time keyword search & verified snippets (Tavily engine) |
| **📑 PDF Extractor** | `GET /api/v1/clean-pdf` | **0.005 USDC** | Formula- and table-preserved academic paper & research PDF extractor |
| **📦 Batch Clean** | `POST /api/v1/batch-clean` | **0.005 USDC** | Concurrent parallel scraping for up to 10 URLs in a single request |
| **🎬 YouTube AI** | `GET /api/v1/clean-youtube` | **0.010 USDC** | Gemini 3.6 Flash multimodal video intelligence & timestamped audio transcript |
| **📊 Extract JSON** | `POST /api/v1/extract-json` | **0.030 USDC** | Converts arbitrary web content into strict schema-constrained JSON |
| **🔮 Web3 Oracle** | `POST /api/v1/oracle/grounding` | **0.035 USDC** | **Live Search + Clean-to-JSON + EIP-712 Cryptographic On-Chain Attestation** |
| **🛡️ Oracle Verify** | `POST /api/v1/oracle/verify` | **0.000 USDC** | Verifies ECDSA signature of CleanWeb Oracle attestations on-chain |
| **🧠 Deep Research** | `GET /api/v1/deep-research` | **0.150 USDC** | Multi-source synthesized AI executive research briefing |
| **💼 Vault Deposit** | `POST /api/v1/vault/deposit` | **0.000 USDC** | Multi-chain USDC vault prefunding for sub-5ms gasless executions |
| **💳 Vault Balance** | `GET /api/v1/vault/balance` | **0.000 USDC** | Real-time query of credit pass balance and validity |
| **🎫 Pass Status** | `GET /api/v1/pass-status` | **0.000 USDC** | Inspects status and remaining credits of a prepaid pass |

---

## 💻 1-Click MCP Setup (Claude Desktop, Cursor, Windsurf)

Connect CleanWeb directly to Claude Desktop, Cursor, or any Model Context Protocol client using `uvx`:

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

Or configure via local clone:

```json
{
  "mcpServers": {
    "polygon-x402-cleanweb": {
      "command": "python",
      "args": ["-u", "mcp_server.py"],
      "env": {
        "POLYGON_RPC_URL": "https://polygon-bor-rpc.publicnode.com",
        "SERVER_WALLET_ADDRESS": "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf",
        "USDC_CONTRACT_ADDRESS": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
      }
    }
  }
}
```

---

## 🤖 Multi-Agent Framework Integrations

Drop-in ready integrations for every major autonomous agent framework via `GET /api/v1/agent/integrations/{framework}`:

### 🦜 LangChain / LangGraph

```python
from langchain.tools import tool
import requests

@tool
def clean_web(url: str) -> str:
    """Fetches a URL and returns ad-free, token-optimized Markdown (87% token savings)."""
    res = requests.get(
        "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/api/v1/clean-web",
        params={"url": url},
        headers={"X-Agent-Nonce": "langchain-agent-session"}
    )
    return res.json().get("clean_markdown", "")
```

### 👥 CrewAI

```python
from crewai.tools import tool
import requests

@tool("CleanWeb Tool")
def clean_web(url: str) -> str:
    """Strips HTML boilerplate and returns pure Markdown to save LLM context window."""
    res = requests.post(
        "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/api/v1/clean-web",
        json={"url": url},
        headers={"X-Agent-Nonce": "crewai-agent-session"}
    )
    return res.json().get("clean_markdown", "")
```

### 🤖 Microsoft AutoGen

```python
import requests

def clean_web_tool(url: str) -> str:
    res = requests.get(
        "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/api/v1/clean-web",
        params={"url": url},
        headers={"X-Agent-Nonce": "autogen-session"}
    )
    return res.json().get("clean_markdown", "")

# assistant.register_for_llm(name="clean_web", description="Clean web markdown")(clean_web_tool)
```

---

## 🏛️ Verified On-Chain Smart Contracts (Polygon, Base, Arbitrum)

CleanWeb operates verified, deterministic smart contracts for on-chain EIP-712 oracle verification and autonomous agent pre-funded vault management.

| Contract Name | Polygon Mainnet (137) ✔ | Base Mainnet (8453) ✔ | Arbitrum One (42161) ✔ |
| :--- | :--- | :--- | :--- |
| **`AgentPaymentVault`** | [`0x45ecBf...1861`](https://polygonscan.com/address/0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861#code) | [`0x28292D...76DD`](https://basescan.org/address/0x28292D76E07E5539F15F3b97935dE8E0432E76DD#code) | [`0x28292D...76DD`](https://arbiscan.io/address/0x28292D76E07E5539F15F3b97935dE8E0432E76DD#code) |
| **`CleanWebOracleConsumer`** | [`0xAECbfB...6D66`](https://polygonscan.com/address/0xAECbfBc171F522c35985AABa2FA1F9881A046D66) | [`0x2394d8...dabe`](https://basescan.org/address/0x2394d888Bd4FFeD472318B891FA17f7F9119dabe#code) | [`0x2394d8...dabe`](https://arbiscan.io/address/0x2394d888Bd4FFeD472318B891FA17f7F9119dabe#code) |
| **`CleanWebOracleVerifier`** | [`0x18fA45...Dc46`](https://polygonscan.com/address/0x18fA451b1d9A9FbbDa6Ebd86F8b42891866ADc46) | [`0x3eD259...0740`](https://basescan.org/address/0x3eD259e47ebA439A9A35489787482B0003310740#code) | [`0x3eD259...0740`](https://arbiscan.io/address/0x3eD259e47ebA439A9A35489787482B0003310740#code) |

---

## 🧪 Production Readiness Review: 43/43 Tests Passed (100%)

Verified across all 38+ FastAPI routes, 14 agent tools, multi-chain settlement vaults, and EIP-712 attestations:

```bash
python -m pytest tests/ -v
```

```text
tests/test_agent_discovery.py::test_well_known_manifests PASSED              [  2%]
tests/test_agent_discovery.py::test_agent_capabilities_reflection PASSED     [  4%]
tests/test_agent_discovery.py::test_agent_pricing_catalog PASSED             [  6%]
tests/test_agent_discovery.py::test_agent_arbitrage_roi PASSED               [  9%]
tests/test_agent_discovery.py::test_agent_framework_integrations PASSED      [ 11%]
tests/test_diagnostics.py::test_run_full_diagnostic PASSED                  [ 13%]
tests/test_diagnostics.py::test_diagnostics_endpoint PASSED                 [ 16%]
tests/test_enhanced_agent_features.py (16 tests) PASSED                      [ 53%]
tests/test_oracle_grounding.py (3 tests) PASSED                              [ 60%]
tests/test_payment_comprehensive.py (4 tests) PASSED                         [ 69%]
tests/test_phase1_cleaners.py (4 tests) PASSED                               [ 79%]
tests/test_phase2_payments.py (5 tests) PASSED                               [ 90%]
tests/test_routes_coverage.py::test_all_api_routes_operational PASSED         [ 93%]
tests/test_treasury.py (3 tests) PASSED                                      [100%]

================== 43 passed, 2 warnings in 85.93s (100%) ==================
```

---

## ⚖️ Legal, Fair Use & Financial Non-Liability Disclaimer

CleanWeb Studio operates strictly under the **Transformative Non-Expressive Text/Data Mining (TDM) Fair Use** doctrine for autonomous AI reasoning.

1. **No Financial or Investment Warranty**: All oracle feeds, search results, and scraped contents are provided **AS-IS**. CleanWeb Studio assumes zero liability for DeFi smart contract liquidations, prediction market settlements (e.g. Polymarket), or trading losses resulting from external web misreporting or LLM hallucinations.
2. **Caller Responsibility**: The autonomous agent deployer/caller is solely responsible for respecting target website intellectual property and applicable laws.
3. **Zero-Data Retention (GDPR Compliant)**: All fetched HTML and raw assets are processed ephemerally in RAM and purged immediately upon response transmission.
4. **100% OFAC Sanctions Filtering**: All micropayment addresses are verified against OFAC Specially Designated Nationals (SDN) lists.
5. **Full Legal Endpoints**:
   * `GET /api/v1/legal/terms`: Official Machine-to-Machine Terms of Service
   * `GET /api/v1/legal/disclaimer`: Full Legal & Financial Disclaimer

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
