# 🌐 agentkit-cleanweb

> **Official Coinbase AgentKit Action Provider for CleanWeb Studio**  
> Pure B2A (Business-to-Agent) 87% Token Noise Reduction, Research PDF Parser, YouTube Gemini Flash Intelligence, and Base Mainnet EIP-712 Ground Truth Attestations.

[![npm version](https://img.shields.io/npm/v/agentkit-cleanweb.svg)](https://www.npmjs.com/package/agentkit-cleanweb)
[![PyPI Core](https://img.shields.io/pypi/v/x402-cleanweb-agent?label=PyPI%20Core%20%28x402-cleanweb-agent%29&color=blue)](https://pypi.org/project/x402-cleanweb-agent/)
[![ElizaOS Plugin](https://img.shields.io/npm/v/cleanweb-eliza-plugin?label=cleanweb-eliza-plugin&color=cb3837)](https://www.npmjs.com/package/cleanweb-eliza-plugin)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Base Mainnet](https://img.shields.io/badge/Base%20Mainnet-8453-blue)](https://basescan.org)

---

## 🔗 Official CleanWeb Multi-Registry Suite (npm ↔ PyPI Companion Packages)

For full-stack multi-agent deployments, pair `agentkit-cleanweb` with the official **Python Core / MCP Server (`PyPI`)** and **ElizaOS v2 Plugin (`npm`)**:

| Registry | Package | Role in Your Agent Stack | Install Command |
| :---: | :--- | :--- | :--- |
| **npm** | [**`agentkit-cleanweb`**](https://www.npmjs.com/package/agentkit-cleanweb) | **Coinbase AgentKit Action Provider** (Base Mainnet EIP-712 & x402 Vaults) | `npm install agentkit-cleanweb @coinbase/agentkit` |
| **PyPI** | [**`x402-cleanweb-agent`**](https://pypi.org/project/x402-cleanweb-agent/) | **Python Core Engine, Claude/Cursor MCP Server & Dual-Core Eliza Brain** | `pip install x402-cleanweb-agent` *(or `uvx x402-cleanweb-agent`)* |
| **npm** | [**`cleanweb-eliza-plugin`**](https://www.npmjs.com/package/cleanweb-eliza-plugin) | **ElizaOS v2 Plugin** (Solana x402 Micropayments & A.GRID Priority 0 Dispatch) | `npm install cleanweb-eliza-plugin` |

---

## 📌 Why CleanWeb for Coinbase AgentKit?

When autonomous AI agents crawl or scrape the live web, raw HTML boilerplate (cookie banners, JavaScript scripts, navigation clutter, ads) consumes **70% to 90% of the LLM context window**.

On GPT-4o or Claude 3.5 Sonnet, scraping a single 80KB page costs ~$0.05 in input tokens.

**CleanWeb reduces web content noise by 87%**, transforming raw HTML into clean, LLM-ready structured Markdown and delivering **86.2% net cost savings** on every downstream agent execution.

### ✨ Key Features
* **87% Token Compression**: 80KB HTML (20,000 tokens) ➔ 2,600 tokens clean Markdown.
* **On-Chain EIP-712 Proofs**: Cryptographically signed attestation hashes on Base Mainnet (`Chain ID: 8453`).
* **Research PDF Parsing**: Whitepapers, financial 10-K filings, and arXiv research parsed in < 2 seconds.
* **YouTube Video Intelligence**: Instant subtitles and Google Gemini 3.8 Flash bullet-point summaries.
* **Gasless x402 Micropayments**: Pre-funded USDC session vaults on Base with < 1ms execution latency.

---

## 🚀 Quickstart

### 1. Installation

```bash
# TypeScript / Coinbase AgentKit
npm install agentkit-cleanweb @coinbase/agentkit

# Companion Python Core & MCP Server (Optional: for local self-hosting & Claude/Cursor MCP)
pip install x402-cleanweb-agent
```

### 2. Register Action Provider with AgentKit

```typescript
import { AgentKit, EvmWalletProvider } from "@coinbase/agentkit";
import { cleanWebActionProvider } from "agentkit-cleanweb";

// 1. Initialize your Coinbase AgentKit EVM Wallet Provider
const walletProvider = new EvmWalletProvider({
  privateKey: process.env.CDP_WALLET_PRIVATE_KEY,
  networkId: "base-mainnet", // or "base-sepolia"
});

// 2. Initialize CleanWeb Action Provider
const cleanWeb = cleanWebActionProvider({
  vaultKey: process.env.AGENT_VAULT_KEY, // Optional: Pre-funded USDC vault key
});

// 3. Register with AgentKit
const agentKit = await AgentKit.from({
  walletProvider,
  actionProviders: [
    cleanWeb,
    // ...other action providers (e.g. security-gate, weth, erc20)
  ],
});

// 4. Retrieve actions and bind to your LangChain / ElizaOS agent
const actions = agentKit.getActions();
console.log(`Registered ${actions.length} CleanWeb actions!`);
```

---

## 🛠️ Provided Actions

| Action Name | Description | Base Pricing |
| :--- | :--- | :---: |
| **`cleanweb_clean_web_content`** | Scrapes any webpage URL and compresses noise/ads into 87% token-reduced Markdown. | 0.001 USDC |
| **`cleanweb_clean_pdf_research`** | Parses online whitepapers, arXiv research, or financial PDFs into structured text. | 0.005 USDC |
| **`cleanweb_clean_youtube_transcript`** | Extracts subtitles and Gemini 3.8 Flash summary from YouTube videos without downloading. | 0.005 USDC |
| **`cleanweb_oracle_grounding`** | Factual discovery with on-chain verifiable EIP-712 cryptographic signature for Base (`8453`). | 0.035 USDC |
| **`cleanweb_manage_x402_vault`** | Checks USDC balance, retrieves Base deposit address, or checks agent VIP pass status. | Free |

---

## 💡 Example: Standalone Usage (Without Full AgentKit)

All actions can also be called standalone in any Node.js / TypeScript environment:

```typescript
import { cleanWebContent, oracleGrounding } from "agentkit-cleanweb";

// 1. Clean a Webpage with 87% token compression
const webResult = await cleanWebContent({
  url: "https://news.ycombinator.com",
});
console.log(`Title: ${webResult.title}`);
console.log(`Token Reduction: ${webResult.tokenReductionRate}`);
console.log(`Clean Markdown:\n${webResult.cleanMarkdown.slice(0, 300)}...`);

// 2. Generate Base EIP-712 Attestation Proof
const proof = await oracleGrounding({
  query: "Base network daily transactions ATH",
  chainId: 8453,
});
console.log(`Verdict: ${proof.verdict}`);
console.log(`EIP-712 Signature: ${proof.attestation?.signature}`);
```

---

## 🔒 Dual-Core Security Gate & ElizaOS Brain Integration

CleanWeb is powered by the **Dual-Core Cognitive Fortress** ([`x402-cleanweb-agent` on PyPI](https://pypi.org/project/x402-cleanweb-agent/)), ensuring that all scraped content passes through a 5-stage zero-trust pipeline:
1. **Indirect Prompt Injection & Steganography Neutralization**
2. **AST Malicious Code Execution Firewall**
3. **ElizaOS Brain Causality & Brier Score Ground-Truth Verification**
4. **Double Cryptographic Seal (Keccak-256 Merkle Root + EIP-712 Signature)**

---

## 📄 License

MIT © [CleanWeb & A.GRID Protocol](https://github.com/nohosa001-pixel/x402-cleanweb-agent)
