# 🌐 cleanweb-eliza-plugin

> **Official CleanWeb Studio & A.GRID Intelligence Plugin for ElizaOS (v2)**  
> *87% LLM Token Reduction, Fresh Ground-Truth Discovery, Dual-Core Security Gate Attestations, and Solana/Multi-Chain x402 Autonomous Micropayments*

[![npm version](https://img.shields.io/npm/v/cleanweb-eliza-plugin.svg)](https://www.npmjs.com/package/cleanweb-eliza-plugin)
[![PyPI Core](https://img.shields.io/pypi/v/x402-cleanweb-agent?label=PyPI%20Core%20%28x402-cleanweb-agent%29&color=blue)](https://pypi.org/project/x402-cleanweb-agent/)
[![Coinbase AgentKit](https://img.shields.io/npm/v/agentkit-cleanweb?label=agentkit-cleanweb&color=cb3837)](https://www.npmjs.com/package/agentkit-cleanweb)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

## 🔗 Official CleanWeb Multi-Registry Suite (npm ↔ PyPI Companion Packages)

`cleanweb-eliza-plugin` is part of the multi-registry CleanWeb Autonomous Intelligence Suite. Combine the **ElizaOS Plugin (`npm`)** with the **Python Core / MCP Server (`PyPI`)** and **Coinbase AgentKit Provider (`npm`)**:

| Registry | Package | Role in Your Agent Stack | Install Command |
| :---: | :--- | :--- | :--- |
| **npm** | [**`cleanweb-eliza-plugin`**](https://www.npmjs.com/package/cleanweb-eliza-plugin) | **ElizaOS v2 Plugin** (Solana x402 Micropayments & A.GRID Priority 0 Dispatch) | `npm install cleanweb-eliza-plugin` |
| **PyPI** | [**`x402-cleanweb-agent`**](https://pypi.org/project/x402-cleanweb-agent/) | **Python Core Engine, Claude/Cursor MCP Server & Dual-Core Eliza Brain** | `pip install x402-cleanweb-agent` *(or `uvx x402-cleanweb-agent`)* |
| **npm** | [**`agentkit-cleanweb`**](https://www.npmjs.com/package/agentkit-cleanweb) | **Coinbase AgentKit Action Provider** (Base Mainnet EIP-712 & x402 Vaults) | `npm install agentkit-cleanweb @coinbase/agentkit` |

---

## ⚡ Key Capabilities
- 🚀 **87% Token Compression**: Strips ads, navigation, scripts, and HTML boilerplate—saving 85%+ in LLM input token costs on every web query.
- ☀️ **Solana & Multi-Chain x402 Micropayments**: Instant `$0.001 USDC` settlement on Solana (`0.4s` finality), Base, Polygon, and Arbitrum.
- 🛡️ **Zero-Injection Cleansing (Security Gate)**: Neutralizes hidden CSS, Unicode steganography, and indirect prompt injection before LLM ingestion.
- 🧠 **ElizaOS Brain Causality & Priority 0 Dispatch**: Evaluates signal actionability (`Brier Score < 0.038`), predicts 0.5–4h market lead times, and dispatches Priority 0 alerts to A.GRID HQ.
- 🔐 **Double Cryptographic Seal**: Every extracted payload is verifiable via Keccak-256 Merkle Root + EIP-712 Oracle Signature.

---

## 📦 Installation

```bash
# 1. Install the ElizaOS v2 Plugin (TypeScript / Node.js)
npm install cleanweb-eliza-plugin

# 2. (Recommended) Install the Companion Python Core & MCP Server
pip install x402-cleanweb-agent
```

---

## 💻 Quick Start (ElizaOS Character Configuration)

```typescript
import { cleanWebPlugin } from "cleanweb-eliza-plugin";

export default {
  name: "AutonomousAlphaAgent",
  plugins: [cleanWebPlugin],
  settings: {
    secrets: {
      CLEANWEB_VAULT_KEY: process.env.CLEANWEB_VAULT_KEY,
    },
  },
};
```

---

## 🖥️ Companion MCP Server Setup (Claude Desktop, Cursor, Windsurf)

Pair your ElizaOS agent with the Python MCP Server from [`x402-cleanweb-agent` (PyPI)](https://pypi.org/project/x402-cleanweb-agent/):

```json
{
  "mcpServers": {
    "x402-cleanweb": {
      "command": "uvx",
      "args": ["x402-cleanweb-agent"]
    }
  }
}
```

---

## 📄 License

MIT © [CleanWeb & A.GRID Protocol](https://github.com/nohosa001-pixel/x402-cleanweb-agent)
