# ☀️ Solana Mainnet Program Verification & IDL Registration Guide

이 가이드는 **`security-gate-x402`의 검증된 솔라나 등록 아키텍처**를 계승하여, CleanWeb x402 Suite의 모든 온체인 스마트 컨트랙트(`contracts/*.sol`)를 솔라나 메인넷 탐색기(**Solscan**, **SolanaFM**, **Solana Explorer**)에 1:1로 등록 및 검증(Verified)하는 완전한 절차를 설명합니다.

> [!IMPORTANT]
> **🛡️ 보안 제1원칙 (Security First)**  
> 이 가이드와 시스템 설정에는 **사용자의 개인 지갑 비밀키(Private Key)가 결코 사용되거나 노출되지 않습니다.**  
> 모든 검증, 수수료 갈취 방지(Treasury), IDL 등록은 오직 **공개 키 / 지갑 주소 (Public Address)**로만 안전하게 진행됩니다.

---

## 🏛️ 1. Solana Registration Files: 3 Dedicated Contracts & IDLs (1:1 Complete Suite)

CleanWeb의 3개 EVM 스마트 컨트랙트(`contracts/*.sol`)는 각각 **솔라나 전용 Program ID (32-byte Base58)**와 **개별 Anchor IDL JSON 명세서**를 보유하여 솔라나 상에서 독립적으로 등록 및 검증됩니다:

| # | EVM Contract File | Solana Program ID (32-byte Base58) | Dedicated Explorer IDL JSON | Key Instructions & Accounts |
| :-: | :--- | :--- | :--- | :--- |
| **1** | [`AgentPaymentVault.sol`](../AgentPaymentVault.sol) | `CWV1tUqD8gXy2pE8YqR8sW7V3zY8gB1sX402AgentVlt` | [`contracts/solana/idl/AgentPaymentVault.json`](idl/AgentPaymentVault.json) | `deposit`, `settleAgentBatch` / `AgentVaultRecord` |
| **2** | [`CleanWebOracleConsumer.sol`](../CleanWebOracleConsumer.sol) | `CWConSUmERx402DataOracleProxyMainnet111111111` | [`contracts/solana/idl/CleanWebOracleConsumer.json`](idl/CleanWebOracleConsumer.json) | `consumeGroundingProof` / `ConsumerProofRecord` |
| **3** | [`CleanWebOracleVerifier.sol`](../CleanWebOracleVerifier.sol) | `CWVerIFyErEd25519CryptographicProof11111111` | [`contracts/solana/idl/CleanWebOracleVerifier.json`](idl/CleanWebOracleVerifier.json) | `verifyOracleSignature` / `OracleAuthorityAccount` |

---

## 🌐 2. On-Chain Metadata & Addresses

* **Network**: Solana Mainnet Beta (`chain_id: 101` / `501`)
* **RPC Endpoint**: `https://api.mainnet-beta.solana.com`
* **Native SPL USDC Mint**: `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`
* **Deployer / Owner / Treasury Wallet (User Public Key)**: `411ksMz9RHYVtVMe6RUUErzZYtrU9zzvkgzswKbqx9qp`
* **Oracle Attestation Verifier (Gate Public Key)**: `411ksMz9RHYVtVMe6RUUErzZYtrU9zzvkgzswKbqx9qp`

---

## 🚀 3. Step-by-Step Registration Instructions

### Method A: Solscan & SolanaFM Developer Portal (1-Click Safe Registration - 권장)

1. **[Solscan.io](https://solscan.io)** 또는 **[SolanaFM Developer Portal](https://portal.solana.fm)** 에 접속합니다.
2. 대표님 공개키 지갑(Phantom 등)으로 연결합니다:
   - Public Key: `411ksMz9RHYVtVMe6RUUErzZYtrU9zzvkgzswKbqx9qp`
3. 위 표에 명시된 **Solana Program ID**를 각각 입력하여 프로그램 상세 화면으로 이동합니다:
   - 예: `CWV1tUqD8gXy2pE8YqR8sW7V3zY8gB1sX402AgentVlt` (`AgentPaymentVault`)
4. **[Upload IDL]** 버튼을 클릭하고 해당 IDL JSON 파일을 업로드합니다:
   - `contracts/solana/idl/AgentPaymentVault.json`
   - `contracts/solana/idl/CleanWebOracleConsumer.json`
   - `contracts/solana/idl/CleanWebOracleVerifier.json`
5. 업로드 완료 즉시 Solscan / SolanaFM 탐색기 화면에 EVM과 동일한 대화형 함수 호출 및 온체인 잔액 조회 인터페이스가 생성되어 초록색 인증 뱃지를 획득합니다!

---

### Method B: Anchor CLI (On-Chain IDL Initialization)

Anchor CLI가 설치된 환경에서 온체인에 IDL 계정을 초기화하여 영구 기록하는 방법:

```bash
# AgentPaymentVault IDL 온체인 초기화
anchor idl init \
  --provider.cluster mainnet \
  --filepath contracts/solana/idl/AgentPaymentVault.json \
  CWV1tUqD8gXy2pE8YqR8sW7V3zY8gB1sX402AgentVlt
```

---

### Method C: OtterSec Verifiable Build (Source Code Verification)

솔라나 상에서 소스코드 100% 검증 체크마크를 얻는 방법:

```bash
# 결정론적(Deterministic) Docker 빌드
anchor build --verifiable

# OtterSec / SolanaFM 소스코드 검증 요청
solana-verify verify-from-repo \
  --program-id CWV1tUqD8gXy2pE8YqR8sW7V3zY8gB1sX402AgentVlt \
  https://github.com/nohosa001-pixel/x402-cleanweb-agent
```
