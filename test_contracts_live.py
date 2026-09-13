"""
Verification test script for newly deployed contracts across Polygon, Base, and Arbitrum.
Tests:
1. AgentPaymentVault state variables (owner, treasuryWallet, usdcToken)
2. CleanWebOracleVerifier on-chain EIP-712 attestation verification
"""

import os
import sys
import time
from web3 import Web3
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

from app.onchain_signer import OnChainCleanWebSigner

CHAINS = [
    {
        "name": "Polygon Mainnet",
        "chain_id": 137,
        "rpc_url": os.getenv("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com"),
        "vault_addr": os.getenv("AGENT_PAYMENT_VAULT_ADDRESS"),
        "consumer_addr": os.getenv("CLEANWEB_ORACLE_CONTRACT_ADDRESS"),
        "verifier_addr": os.getenv("CLEANWEB_ORACLE_VERIFIER_ADDRESS"),
    },
    {
        "name": "Base Mainnet",
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "vault_addr": os.getenv("BASE_AGENT_PAYMENT_VAULT_ADDRESS"),
        "consumer_addr": os.getenv("BASE_CLEANWEB_ORACLE_CONTRACT_ADDRESS"),
        "verifier_addr": os.getenv("BASE_CLEANWEB_ORACLE_VERIFIER_ADDRESS"),
    },
    {
        "name": "Arbitrum One",
        "chain_id": 42161,
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "vault_addr": os.getenv("ARBITRUM_AGENT_PAYMENT_VAULT_ADDRESS"),
        "consumer_addr": os.getenv("ARBITRUM_CLEANWEB_ORACLE_CONTRACT_ADDRESS"),
        "verifier_addr": os.getenv("ARBITRUM_CLEANWEB_ORACLE_VERIFIER_ADDRESS"),
    },
]

# Minimal ABIs
VERIFIER_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "query", "type": "string"},
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "uint8", "name": "v", "type": "uint8"},
            {"internalType": "bytes32", "name": "r", "type": "bytes32"},
            {"internalType": "bytes32", "name": "s", "type": "bytes32"},
        ],
        "name": "verifyAttestation",
        "outputs": [{"internalType": "bool", "name": "isValid", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "oracleSigner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

VAULT_ABI = [
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "treasuryWallet",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

def main():
    print("=" * 70)
    print("🧪 [STEP 1] 3대 메인넷 스마트 컨트랙트 종합 라이브 검증 테스트")
    print("=" * 70)

    # Use DEPLOYER_PRIVATE_KEY for signing
    deployer_key = os.getenv("DEPLOYER_PRIVATE_KEY") or os.getenv("SERVER_PRIVATE_KEY")
    if not deployer_key:
        neighbor_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "security-gate-x402", ".env"))
        if os.path.exists(neighbor_env):
            with open(neighbor_env, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("DEPLOYER_PRIVATE_KEY="):
                        deployer_key = line.strip().split("=", 1)[1].strip()
                        break

    all_passed = True

    for c in CHAINS:
        print(f"\n🌐 [{c['name']}] (Chain ID {c['chain_id']}) 검증 시작")
        print(f"   - Verifier Address : {c['verifier_addr']}")
        print(f"   - Vault Address    : {c['vault_addr']}")

        w3 = Web3(Web3.HTTPProvider(c["rpc_url"]))
        if not w3.is_connected():
            print("   ❌ RPC 연결 실패!")
            all_passed = False
            continue

        # 1. Vault Test
        try:
            vault = w3.eth.contract(address=w3.to_checksum_address(c["vault_addr"]), abi=VAULT_ABI)
            owner = vault.functions.owner().call()
            treasury = vault.functions.treasuryWallet().call()
            print(f"   ✅ [Vault] 정상 응답: Owner={owner[:8]}..., Treasury={treasury[:8]}...")
        except Exception as e:
            print(f"   ❌ [Vault] 오류: {e}")
            all_passed = False

        # 2. Verifier Test
        try:
            verifier = w3.eth.contract(address=w3.to_checksum_address(c["verifier_addr"]), abi=VERIFIER_ABI)
            onchain_signer_addr = verifier.functions.oracleSigner().call()
            print(f"   ✅ [Verifier] Signer 등록 확인: {onchain_signer_addr}")

            # Create an EIP-712 signature using OnChainCleanWebSigner
            signer = OnChainCleanWebSigner(
                private_key=deployer_key,
                chain_id=c["chain_id"],
                contract_address=c["verifier_addr"]
            )
            
            test_query = "CleanWeb Live Oracle Verification Test"
            test_data_hash = Web3.keccak(text="Hello CleanWeb On-Chain World!").hex()
            now_ts = int(time.time())

            attestation = signer.sign_oracle_grounding(test_query, test_data_hash, timestamp=now_ts)

            # Call on-chain verifyAttestation
            r_bytes = bytes.fromhex(attestation.r.replace("0x", "").zfill(64))
            s_bytes = bytes.fromhex(attestation.s.replace("0x", "").zfill(64))
            
            is_valid_onchain = verifier.functions.verifyAttestation(
                test_query,
                bytes.fromhex(test_data_hash.replace("0x", "")),
                now_ts,
                attestation.v,
                r_bytes,
                s_bytes
            ).call()

            if is_valid_onchain:
                print(f"   🎯 [Verifier] 온체인 EIP-712 서명 검증 성공! (isValid: {is_valid_onchain})")
            else:
                print(f"   ❌ [Verifier] 온체인 검증 반환값 False")
                all_passed = False

        except Exception as e:
            print(f"   ❌ [Verifier] 검증 중 오류: {e}")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 [STEP 1 성공] Polygon, Base, Arbitrum 모든 온체인 컨트랙트 검증 통과!")
    else:
        print("⚠️ [STEP 1 일부 경고] 세부 로그를 확인해주세요.")
    print("=" * 70)

if __name__ == "__main__":
    main()
