# ⚡ CleanWeb Studio & Spend Firewall (v2.5.3)

> **"Clean, Ad-Free Web Content & Verified On-Chain Data Oracle for Humans & Autonomous Agents."**  
> *Zero credit cards required. Transparent pay-as-you-go Native USDC micropayments & pre-funded vaults with on-chain Polygon EIP-712 spend policy attestations.*

[![Version](https://img.shields.io/badge/Version-2.5.3-00f2fe?style=for-the-badge&logo=fastapi&logoColor=black)](https://github.com/nohosa001-pixel/x402-cleanweb-agent)
[![Multi-Chain](https://img.shields.io/badge/Chains-Polygon%20(Verified)%20%7C%20Base%20%7C%20Arbitrum-8247e5?style=for-the-badge&logo=ethereum&logoColor=white)](https://polygonscan.com/address/0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861#code)
[![Access](https://img.shields.io/badge/Access-Humans%20%26%20AI%20Agents-10b981?style=for-the-badge&logo=probot&logoColor=white)](http://localhost:8080/dashboard)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Why CleanWeb Studio?

Whether you are a **human researcher** who wants ad-free, high-density web reading, or an **autonomous AI agent** (LangChain, CrewAI, AutoGPT, trading bots) building RAG knowledge:
1. **Paywall & Anti-Bot Friction**: No need for recurring monthly credit card subscriptions. Pay only for what you consume via pre-funded Native USDC.
2. **Context Token & Attention Waste**: Raw HTML is 95% garbage (ads, trackers, cookie modals) that clutters your screen or exhausts LLM context windows.
3. **Verifiable Truth (On-Chain Grounding)**: Every extraction can be cryptographically anchored with an on-chain EIP-712 digital signature verifiable on Polygon.

---

## 🖥️ Interactive Web Studio Dashboard

Access the live human-friendly web interface at:
* **Web Dashboard**: `http://localhost:8080/dashboard`
* **Interactive API Docs**: `http://localhost:8080/docs`
* **Health & Diagnostics**: `http://localhost:8080/health?deep=true`

---

## 🔮 Core Agent Services & Micro-Pricing (USDC)

| Service Endpoint | What it Does | Cost (USDC) | Gas Overhead |
| :--- | :--- | :---: | :---: |
| **🌐 Clean Web (`/api/v1/clean-web`)** | 99.9% token reduction web markdown cleaner | **0.001 USDC** | **0원 (<5ms)** |
| **📝 Pure Text (`/api/v1/clean-text`)** | Ultra-lightweight raw plain text for vector/RAG embeddings | **0.001 USDC** | **0원 (<5ms)** |
| **🗺️ Site Mapper (`/api/v1/map-site`)** | Domain sitemap & internal URL tree discovery (Firecrawl /map) | **0.002 USDC** | **0원 (<5ms)** |
| **🔍 Agent Search (`/api/v1/search`)** | Fast real-time keyword search & verified snippets (Tavily) | **0.002 USDC** | **0원 (<5ms)** |
| **📄 PDF Research (`/api/v1/clean-pdf`)** | Formula & table-preserved academic paper extractor | **0.005 USDC** | **0원 (<5ms)** |
| **🎬 YouTube AI (`/api/v1/clean-youtube`)** | Gemini 3.6 Flash hybrid video analysis & audio intelligence | **0.010 USDC** | **0원 (<5ms)** |
| **📊 Extract JSON (`/api/v1/extract-json`)** | Webpage to schema-constrained JSON structured extractor | **0.030 USDC** | **0원 (<5ms)** |
| **🔮 Web3 Signed Oracle (`/api/v1/oracle/grounding`)** | **Real-time search + Clean-to-JSON + EIP-712 On-Chain Attestation** | **0.035 USDC** | **0원 (<5ms)** |
| **🧠 Deep Research (`/api/v1/deep-research`)** | Multi-source synthesized AI executive research briefing | **0.150 USDC** | **0원 (<5ms)** |

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

## 🏛️ Official On-Chain Smart Contracts (Polygon, Base, Arbitrum)

CleanWeb Studio v2.5.3 deploys verified, deterministic smart contracts for on-chain EIP-712 oracle verification and autonomous agent pre-funded vault management.

| Contract Name | Polygon Mainnet (137) | Base Mainnet (8453) | Arbitrum One (42161) |
| :--- | :--- | :--- | :--- |
| **`AgentPaymentVault`** | [`0x45ecBf...1861`](https://polygonscan.com/address/0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861) | [`0x28292D...76DD`](https://basescan.org/address/0x28292D76E07E5539F15F3b97935dE8E0432E76DD) | [`0x28292D...76DD`](https://arbiscan.io/address/0x28292D76E07E5539F15F3b97935dE8E0432E76DD) |
| **`CleanWebOracleConsumer`** | [`0xAECbfB...6D66`](https://polygonscan.com/address/0xAECbfBc171F522c35985AABa2FA1F9881A046D66) | [`0x2394d8...dabe`](https://basescan.org/address/0x2394d888Bd4FFeD472318B891FA17f7F9119dabe) | [`0x2394d8...dabe`](https://arbiscan.io/address/0x2394d888Bd4FFeD472318B891FA17f7F9119dabe) |
| **`CleanWebOracleVerifier`** | [`0x18fA45...Dc46`](https://polygonscan.com/address/0x18fA451b1d9A9FbbDa6Ebd86F8b42891866ADc46) | [`0x3eD259...0740`](https://basescan.org/address/0x3eD259e47ebA439A9A35489787482B0003310740) | [`0x3eD259...0740`](https://arbiscan.io/address/0x3eD259e47ebA439A9A35489787482B0003310740) |

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

## ⚖️ Legal, Fair Use & Financial Non-Liability Disclaimer

CleanWeb Studio operates strictly under the **Transformative Non-Expressive Text/Data Mining (TDM) Fair Use** doctrine for autonomous AI reasoning.

1. **No Financial or Investment Warranty**: All oracle feeds, search results, and scraped contents are provided **AS-IS**. CleanWeb Studio assumes zero liability for DeFi smart contract liquidations, prediction market settlements (e.g. Polymarket), or trading losses resulting from external web misreporting or LLM hallucinations.
2. **Caller Responsibility**: The autonomous agent deployer/caller is solely responsible for respecting target website intellectual property and applicable laws.
3. **Zero-Data Retention (GDPR Compliant)**: All fetched HTML and raw assets are processed ephemerally in RAM and purged immediately upon response transmission.
4. **100% OFAC Sanctions Filtering**: All micropayment addresses are verified against OFAC Specially Designated Nationals (SDN) lists.
5. **Full Legal Endpoints**:
   - `GET /api/v1/legal/terms`: Official Machine-to-Machine Terms of Service
   - `GET /api/v1/legal/disclaimer`: Full Legal & Financial Disclaimer

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
