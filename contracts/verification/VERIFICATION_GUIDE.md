# Smart Contract Verification & Public Explorer Guide

This guide provides everything required to verify and publicly display **`AgentPaymentVault.sol`**, **`CleanWebOracleConsumer.sol`**, and **`CleanWebOracleVerifier.sol`** on block explorers (**Polygonscan**, **BaseScan**, **Arbiscan**).

---

## 1. Quick Verification Parameters

| Parameter | Recommended Value |
| :--- | :--- |
| **Solidity Compiler Version** | `v0.8.20+commit.a1b79de6` |
| **Open Source License Type** | `MIT License (MIT)` |
| **Optimization** | `No` (or `Yes` with `200` runs if compiled with optimizer) |
| **EVM Version** | `default` (or `paris` / `shanghai`) |

---

## 2. Polygon Mainnet (Chain ID: 137)

### Contract A: `AgentPaymentVault.sol`

* **Status**: 🟢 **Verified on Polygonscan** (Exact Bytecode & ABI Match)
* **Contract Address**: [`0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861`](https://polygonscan.com/address/0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861#code)
* **Direct Verification URL**: [https://polygonscan.com/verifyContract?a=0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861](https://polygonscan.com/verifyContract?a=0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861)
* **Source File**: [`contracts/verification/AgentPaymentVault.flattened.sol`](AgentPaymentVault.flattened.sol)
* **Constructor Arguments**:
  * `_usdcToken` (Polygon Native USDC): `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359`
  * `_treasuryWallet` (Server Treasury): `0x255F9991233f86B29dB847c8d5b8CB9915e80dCf`
* **ABI-Encoded Constructor Arguments (HEX)**:
```text
0000000000000000000000003c499c542cef5e3811e1192ce70d8cc03d5c3359000000000000000000000000255f9991233f86b29db847c8d5b8cb9915e80dcf
```

---

### Contract B: `CleanWebOracleConsumer.sol`

* **Status**: 🟢 **Verified on Polygonscan** (Exact Bytecode & ABI Match)
* **Contract Address**: [`0xAECbfBc171F522c35985AABa2FA1F9881A046D66`](https://polygonscan.com/address/0xAECbfBc171F522c35985AABa2FA1F9881A046D66#code)
* **Direct Verification URL**: [https://polygonscan.com/verifyContract?a=0xAECbfBc171F522c35985AABa2FA1F9881A046D66](https://polygonscan.com/verifyContract?a=0xAECbfBc171F522c35985AABa2FA1F9881A046D66)
* **Source File**: [`contracts/verification/CleanWebOracleConsumer.flattened.sol`](CleanWebOracleConsumer.flattened.sol)
* **Constructor Arguments**:
  * `_oracleSigner` (Server Treasury/Signer): `0x255F9991233f86B29dB847c8d5b8CB9915e80dCf`
* **ABI-Encoded Constructor Arguments (HEX)**:
```text
000000000000000000000000255f9991233f86b29db847c8d5b8cb9915e80dcf
```

---

### Contract C: `CleanWebOracleVerifier.sol`

* **Status**: 🟢 **Verified on Polygonscan** (Exact Bytecode & ABI Match)
* **Contract Address**: [`0x18fA451b1d9A9FbbDa6Ebd86F8b42891866ADc46`](https://polygonscan.com/address/0x18fA451b1d9A9FbbDa6Ebd86F8b42891866ADc46#code)
* **Direct Verification URL**: [https://polygonscan.com/verifyContract?a=0x18fA451b1d9A9FbbDa6Ebd86F8b42891866ADc46](https://polygonscan.com/verifyContract?a=0x18fA451b1d9A9FbbDa6Ebd86F8b42891866ADc46)
* **Source File**: [`contracts/verification/CleanWebOracleVerifier.flattened.sol`](CleanWebOracleVerifier.flattened.sol)
* **Constructor Arguments**:
  * `_oracleSigner` (Server Treasury/Signer): `0x255F9991233f86B29dB847c8d5b8CB9915e80dCf`
* **ABI-Encoded Constructor Arguments (HEX)**:
```text
000000000000000000000000255f9991233f86b29db847c8d5b8cb9915e80dcf
```

---

## 3. Base (Chain ID: 8453) Multi-Chain Parameters (✔ Verified on BaseScan)

* **Native USDC Address**: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
* **Direct Verify URLs**:
  * AgentPaymentVault: [https://basescan.org/verifyContract?a=0x28292D76E07E5539F15F3b97935dE8E0432E76DD](https://basescan.org/verifyContract?a=0x28292D76E07E5539F15F3b97935dE8E0432E76DD)
  * CleanWebOracleConsumer: [https://basescan.org/verifyContract?a=0x2394d888Bd4FFeD472318B891FA17f7F9119dabe](https://basescan.org/verifyContract?a=0x2394d888Bd4FFeD472318B891FA17f7F9119dabe)
  * CleanWebOracleVerifier: [https://basescan.org/verifyContract?a=0x3eD259e47ebA439A9A35489787482B0003310740](https://basescan.org/verifyContract?a=0x3eD259e47ebA439A9A35489787482B0003310740)
* **AgentPaymentVault Constructor HEX**:
```text
000000000000000000000000833589fcd6edb6e08f4c7c32d4f71b54bda02913000000000000000000000000255f9991233f86b29db847c8d5b8cb9915e80dcf
```
* **Consumer / Verifier Constructor HEX**:
```text
000000000000000000000000255f9991233f86b29db847c8d5b8cb9915e80dcf
```

---

## 4. Arbitrum One (Chain ID: 42161) Multi-Chain Parameters (✔ Verified on Arbiscan)

* **Native USDC Address**: `0xaf88d065e77c8cC2239327C5EDb3A432268e5831`
* **Direct Verify URLs**:
  * AgentPaymentVault: [https://arbiscan.io/verifyContract?a=0x28292D76E07E5539F15F3b97935dE8E0432E76DD](https://arbiscan.io/verifyContract?a=0x28292D76E07E5539F15F3b97935dE8E0432E76DD)
  * CleanWebOracleConsumer: [https://arbiscan.io/verifyContract?a=0x2394d888Bd4FFeD472318B891FA17f7F9119dabe](https://arbiscan.io/verifyContract?a=0x2394d888Bd4FFeD472318B891FA17f7F9119dabe)
  * CleanWebOracleVerifier: [https://arbiscan.io/verifyContract?a=0x3eD259e47ebA439A9A35489787482B0003310740](https://arbiscan.io/verifyContract?a=0x3eD259e47ebA439A9A35489787482B0003310740)
* **AgentPaymentVault Constructor HEX**:
```text
000000000000000000000000af88d065e77c8cc2239327c5edb3a432268e5831000000000000000000000000255f9991233f86b29db847c8d5b8cb9915e80dcf
```
* **Consumer / Verifier Constructor HEX**:
```text
000000000000000000000000255f9991233f86b29db847c8d5b8cb9915e80dcf
```

---

## 5. Automated CLI Verification Helper

Run the verification helper anytime to view direct links and constructor payloads:

```bash
# Polygon Mainnet
python scripts/verify_contracts.py --chain polygon

# All Chains (Polygon, Base, Arbitrum)
python scripts/verify_contracts.py --chain all
```
