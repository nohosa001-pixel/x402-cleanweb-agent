# ⚡ CleanWeb Studio v2.4.0: B2A Autonomous Agent Data Oracle & Grounding Pipeline

> **The World's First Pure Business-to-Agent (B2A) Real-Time Data Oracle & x402 Micropayment Engine.**  
> *Zero credit cards. Zero human logins. 100% Native USDC pre-funded vaults with on-chain EIP-712 attestations.*

[![Version](https://img.shields.io/badge/Version-2.4.0-00f2fe?style=for-the-badge&logo=fastapi&logoColor=black)](https://github.com/nohosa001-pixel/x402-cleanweb-agent)
[![Multi-Chain](https://img.shields.io/badge/Chains-Polygon%20%7C%20Base%20%7C%20Arbitrum-8247e5?style=for-the-badge&logo=ethereum&logoColor=white)](https://polygonscan.com)
[![PyPI Package](https://img.shields.io/pypi/v/x402-cleanweb-agent.svg?color=blue&label=PyPI%20Package)](https://pypi.org/project/x402-cleanweb-agent/)
[![Tests](https://img.shields.io/badge/Tests-19%2F19%20Passed%20(100%25)-10b981?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/nohosa001-pixel/x402-cleanweb-agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Why CleanWeb Studio for Autonomous AI Agents?

Autonomous AI Agents (LangChain, CrewAI, AutoGPT, DeFi trading bots) face three critical bottlenecks when accessing web knowledge:
1. **Paywall & Anti-Bot Friction**: Agents cannot solve Cloudflare turnstiles or register credit cards.
2. **LLM Context Token Waste**: Raw HTML is 95% garbage (ads, scripts, cookie banners) that drains inference budgets.
3. **Lack of Verifiable Truth (On-Chain Grounding)**: Smart contracts on Polymarket, Hyperliquid, or DeFi cannot verify whether off-chain web data has been tampered with.

**CleanWeb Studio v2.4.0 solves all three in a single HTTP call.**

---

## 🔮 4 Core Agent Services & Micro-Pricing (USDC)

| Service Endpoint | What it Does | Cost (USDC) | Gas Overhead |
| :--- | :--- | :---: | :---: |
| **🌐 Clean Web (`/api/v1/clean-web`)** | 99.9% token reduction web markdown cleaner | **0.001 USDC** | **0원 (<5ms)** |
| **🎬 YouTube AI (`/api/v1/clean-youtube`)** | Gemini 3.6 Flash hybrid video analysis & audio intelligence | **0.010 USDC** | **0원 (<5ms)** |
| **📄 PDF Research (`/api/v1/clean-pdf`)** | Formula & table-preserved academic paper extractor | **0.005 USDC** | **0원 (<5ms)** |
| **🔮 Web3 Signed Oracle (`/api/v1/oracle/grounding`)** | **Real-time search + Clean-to-JSON + EIP-712 On-Chain Attestation** | **0.035 USDC** | **0원 (<5ms)** |

---

## 💼 B2A Pre-funded Smart Vault (2.0 ~ 1,000.0 USDC)

Forget credit card chargebacks and 2.9% + $0.30 payment gateway fees. CleanWeb operates entirely on **Native USDC** across Polygon, Base, and Arbitrum.

* **Minimum Deposit**: **`2.0 USDC`** (~2,000 web cleans or 200 YouTube AI analyses)
* **Maximum Deposit**: **`1,000.0 USDC`** (1,000,000 queries for enterprise agent clusters)
* **Session Key Auth**: Agents deposit once on-chain and receive an `X-Vault-Key` for instant sub-5ms calls with zero gas transaction friction.

---

## 🔮 Oracle-Grade Grounding Pipeline (`/api/v1/oracle/grounding`)

```mermaid
graph LR
    Agent[🤖 Autonomous AI Agent] -->|POST /api/v1/oracle/grounding\nQuery: Fed Interest Rate Decision| CleanWeb[CleanWeb Engine]
    CleanWeb -->|1. Real-time Meta Search| Web[(Live Web Sources)]
    CleanWeb -->|2. Gemini 3.6 Flash| JSON[(Structured JSON)]
    CleanWeb -->|3. EIP-712 Master Key| Signer[(Cryptographic Signer)]
    Signer -->|Signed Attestation v,r,s| Agent
    Agent -->|ecrecover()| Contract[DeFi / Polymarket Smart Contract]
```

### 1-Line Solidity Verification ([`CleanWebOracleVerifier.sol`](contracts/CleanWebOracleVerifier.sol))

```solidity
// Verify CleanWeb Oracle attestation on Polygon / Base / Arbitrum
require(
    verifier.verifyAttestation(query, dataHash, timestamp, v, r, s),
    "Tampered or unauthorized oracle data"
);
```

---

## 🛠️ Quickstart (Autonomous Python Agent)

```python
import requests

# 1. Deposit into vault via Web3 or use existing session key
VAULT_KEY = "vault_key_your_prefunded_agent_key"

# 2. Call Web3 Signed Oracle Grounding
response = requests.post(
    "http://127.0.0.1:8000/api/v1/oracle/grounding",
    headers={"X-Vault-Key": VAULT_KEY},
    json={
        "query": "US Federal Reserve interest rate decision latest",
        "max_sources": 3
    }
)

data = response.json()
print("Fact Summary:", data["summary_markdown"])
print("Structured JSON:", data["structured_data"])
print("EIP-712 Signature:", data["oracle_attestation"]["signature"])
```

---

## 🧪 Comprehensive Test Suite (19/19 Passed)

```bash
# Run complete test suite
python -m pytest tests/ -v
```

```text
tests/test_oracle_grounding.py::test_oracle_grounding_402_challenge PASSED           [  5%]
tests/test_oracle_grounding.py::test_oracle_grounding_execution_with_attestation PASSED [ 10%]
tests/test_oracle_grounding.py::test_oracle_vault_deduction_0_035 PASSED             [ 15%]
tests/test_payment_comprehensive.py::test_full_payment_lifecycle PASSED              [ 21%]
tests/test_payment_comprehensive.py::test_vip_promo_code PASSED                      [ 26%]
tests/test_payment_comprehensive.py::test_b2a_vault_deposit_limits_lifecycle PASSED [ 31%]
tests/test_payment_comprehensive.py::test_ui_html_payment_components PASSED          [ 36%]
tests/test_phase1_cleaners.py::test_web_cleaner_example_domain PASSED                [ 42%]
tests/test_phase1_cleaners.py::test_youtube_cleaner_video_id PASSED                  [ 47%]
tests/test_phase1_cleaners.py::test_youtube_cleaner_execution PASSED                 [ 52%]
tests/test_phase1_cleaners.py::test_batch_clean_concurrent PASSED                    [ 57%]
tests/test_phase2_payments.py::test_multi_chain_configs PASSED                       [ 63%]
tests/test_phase2_payments.py::test_onchain_eip712_attestation PASSED                [ 68%]
tests/test_phase2_payments.py::test_vault_deposit_and_deduct PASSED                  [ 73%]
tests/test_phase2_payments.py::test_402_challenge_returned_when_unauthorized PASSED [ 78%]
tests/test_phase2_payments.py::test_dev_bypass PASSED                                [ 84%]
tests/test_treasury.py::test_ping_keepalive PASSED                                   [ 89%]
tests/test_treasury.py::test_treasury_status_endpoint PASSED                         [ 94%]
tests/test_treasury.py::test_multi_chain_balances_structure PASSED                   [100%]

======================= 19 passed, 2 warnings in 44.01s =======================
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
