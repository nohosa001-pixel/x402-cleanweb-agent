# ☀️ CleanWeb x402 — Solana Autonomous Agent & ElizaOS Ecosystem Suite

> **"Zero-Human Machine-to-Machine (B2A) Economy on Solana Mainnet-Beta"**  
> Solana 기반 자율 AI 에이전트(SendAI Solana Agent Kit, ElizaOS, Anchor Swarms)가 중앙 통제 없이 87% 압축된 클린 웹 마크다운과 암호학적 오라클 데이터를 직접 소비하고 결제할 수 있는 공식 연동 스택입니다.

---

## 🏛️ Solana Mainnet-Beta 스마트 컨트랙트 주소록

| 컨트랙트 명칭 | Solana Program ID (32-byte Base58) | Solscan 상태 | 역할 |
| :--- | :--- | :---: | :--- |
| **AgentPaymentVault** | `7oZ16YaazQzN6z5uA1nAZWD9oGUDXyvHwXGJLFYyWi3y` | 🟢 **Mainnet Live** | 에이전트 사전 예치금 볼트 & 가스비 제로 실시간 차감 |
| **CleanWebOracleConsumer** | `21ZR1QCyAbNrRLs1iWEkdbNsfCFdJcy6ip9R2JxDbkTL` | 🟢 **Mainnet Live** | 온체인 오라클 그라운딩 데이터 소비 컨트랙트 |
| **CleanWebOracleVerifier** | `9nVrymJgNWCXkuGKn8CCQnSK6aDazFR7z3WL82jZiopC` | 🟢 **Mainnet Live** | Ed25519 암호학적 디지털 서명 검증 라이브러리 |
| **Official Treasury Wallet** | `411ksMz9RHYVtVMe6RUUErzZYtrU9zzvkgzswKbqx9qp` | 🟢 **Mainnet Live** | CleanWeb 공식 SPL USDC 수신 지갑 |
| **Native SPL USDC Mint** | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` | 🟢 **Official Circle** | Solana 공식 SPL USDC 토큰 |

---

## 🚀 1. 빠른 사용법 (Python: Solana Agent Kit 연동)

```python
from integrations.solana.x402_solana_agent import X402SolanaAgentTool

# 에이전트 세션 초기화 (지갑/카드 없이 즉시 5회 무료 샌드박스 제공)
agent_tool = X402SolanaAgentTool(agent_nonce="solana_agent_alpha_01")

# 87% 토큰 절감 클린 마크다운 스크래핑
result = agent_tool.scrape_clean_markdown("https://news.ycombinator.com")

print("Status:", result["status"])
print("Markdown Preview:\n", result["markdown"][:300])
```

---

## 🤖 2. ElizaOS 플러그인 액션 (`CLEANWEB_SCRAPE`)

ElizaOS 에이전트가 트윗 분석, 웹 조사, 온체인 알파 발굴 시 LLM 컨텍스트 비용을 86% 이상 절감하도록 액션으로 제공됩니다:

```typescript
import { Action, IAgentRuntime, Memory } from "@elizaos/core";

export const cleanWebScrapeAction: Action = {
    name: "CLEANWEB_SCRAPE",
    similes: ["SCRAPE_WEB", "EXTRACT_CLEAN_MARKDOWN", "SOLANA_ORACLE_BROWSE"],
    description: "Scrapes target web page and returns 87% token-compressed markdown with x402 Solana micropayments.",
    validate: async (runtime: IAgentRuntime, message: Memory) => true,
    handler: async (runtime: IAgentRuntime, message: Memory) => {
        const url = message.content.text;
        const res = await fetch(`https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/r/${encodeURIComponent(url)}`, {
            headers: {
                "User-Agent": "ElizaOS/x402-CleanWeb",
                "X-Agent-Nonce": runtime.agentId
            }
        });
        const markdown = await res.text();
        return { text: markdown };
    }
};
```

---

## 🌐 3. Solscan 1-Click IDL 등록 (바탕화면 원클릭 패키지)

대표님의 Phantom 지갑(`411ksMz...`)으로 Solscan에 Anchor IDL을 등록하면, 전 세계 솔라나 사용자들이 Solscan 화면에서 직접 컨트랙트 함수를 호출할 수 있게 됩니다.

1. **바탕화면 열기**: `CleanWeb_Solana_Registration_Package` 폴더 확인
2. **Solscan 접속**: [https://solscan.io](https://solscan.io)
3. **지갑 연결**: 팬텀(Phantom) 지갑 (`411ksMz9RHYVtVMe6RUUErzZYtrU9zzvkgzswKbqx9qp`)
4. **Program 검색 및 IDL 업로드**:
   - `7oZ16Yaaz...` 검색 -> **[Upload IDL]** 클릭 -> `AgentPaymentVault.json` 업로드
   - `21ZR1QC...` 검색 -> **[Upload IDL]** 클릭 -> `CleanWebOracleConsumer.json` 업로드
   - `9nVrymJ...` 검색 -> **[Upload IDL]** 클릭 -> `CleanWebOracleVerifier.json` 업로드
