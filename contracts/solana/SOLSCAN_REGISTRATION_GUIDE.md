# ☀️ Solscan (솔스캔) & Solana 온체인 볼트 프로그램 등록 가이드

> **대상 스마트 프로그램**: `agent_payment_vault` (Anchor v0.29 / Rust)  
> **EVM 대응 원본**: [`contracts/AgentPaymentVault.sol`](../AgentPaymentVault.sol)  
> **공식 Anchor IDL 명세**: [`contracts/solana/target/idl/agent_payment_vault.json`](./target/idl/agent_payment_vault.json)

---

## 1. 개요: EVM vs Solana Solscan의 등록 메커니즘 차이

| 구분 | Polygonscan / Basescan (EVM) | Solscan / Solana Explorer (Solana) |
| :--- | :--- | :--- |
| **스마트 컨트랙트 형식** | Solidity (`AgentPaymentVault.sol`) | Rust / BPF 바이트코드 (`agent_payment_vault.so`) |
| **소스 검증(Verification) 방식** | `.sol` 코드 업로드 및 컴파일러 매칭 | **Anchor IDL (JSON)** 온체인 초기화 또는 Solscan IDL 업로드 |
| **실행 엔진** | EVM (Ethereum Virtual Machine) | SVM (Sealevel Virtual Machine) |
| **결제 방식** | ERC-20 `transferFrom` | **SPL Token Transfer (Native USDC)** |

---

## 2. Solscan에 Anchor IDL 등록하는 방법 (Step-by-Step)

배포된 프로그램 주소(또는 로컬/데브넷/메인넷 프로그램)의 Solscan 탐색기 화면에 **`deposit`**, **`settleAgent`**, **`updateTreasury`** 함수와 **`VaultConfig`**, **`AgentVaultRecord`** 상태가 GUI로 완전히 나타나도록 등록하는 절차입니다.

### 방법 A. Solscan 웹 GUI에서 직접 IDL 업로드 (가장 간편)

1. **Solscan** ([https://solscan.io](https://solscan.io)) 접속.
2. 배포된 프로그램 계정 주소 페이지로 이동.  
   *(예: `https://solscan.io/account/<PROGRAM_ID>`)*
3. **[Program]** 또는 **[Anchor IDL]** 탭 클릭.
4. **[Upload IDL]** 버튼 클릭.
5. 로컬의 IDL 파일 선택:
   ```
   contracts/solana/target/idl/agent_payment_vault.json
   ```
6. 업로드 완료 즉시 Solscan 화면에 `AgentPaymentVault.sol`과 동일한 함수 호출 및 온체인 잔액 열람 인터페이스가 자동 생성됩니다.

---

### 방법 B. Anchor CLI를 통한 온체인 IDL 배포 (완전 탈중앙화)

Anchor CLI가 설치된 환경에서 다음 명령어로 솔라나 온체인에 IDL을 영구 기록하면, Solscan 및 모든 익스플로러가 자동으로 소스코드를 파싱합니다:

```bash
# 1. Rust 프로그램 빌드 (BFP/ELF 바이너리 및 IDL 생성)
anchor build

# 2. 솔라나 메인넷 배포
anchor deploy --provider.cluster mainnet

# 3. 온체인 IDL 초기화 (Solscan 자동 연동)
anchor idl init --filepath target/idl/agent_payment_vault.json <PROGRAM_ID> --provider.cluster mainnet
```

---

## 3. 프로그램 내 함수 및 계정 명세

### 지원 Instructions
1. **`initialize(treasury_wallet)`**:  
   - 글로벌 금고 PDA(`vault_config`) 및 SPL USDC 보관 계정(`vault_tokens`) 생성.
2. **`deposit(amount)`**:  
   - AI 에이전트가 본인의 지갑에서 Vault PDA로 Native SPL USDC를 선입금하고 온체인 예치금 잔액 증가.
3. **`settle_agent(amount)`**:  
   - 에이전트가 소비한 API 금액만큼 Vault 잔액에서 차감 후 대표님의 Treasury Wallet(`411ks...`)으로 정산 이체.
4. **`update_treasury(new_treasury)`**:  
   - 대표님 수신 지갑 주소 변경 (오너 전용).

### 온체인 계정 상태 (Accounts)
- **`VaultConfig`**: 총 정산액, 오너, 수신 지갑, USDC 토큰 민트 주소 보관
- **`AgentVaultRecord`**: 에이전트별 예치금 잔액(`balance`), 누적 입금액, 누적 소비액 보관
