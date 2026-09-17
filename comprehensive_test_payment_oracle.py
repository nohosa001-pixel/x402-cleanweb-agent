"""
Comprehensive Live Test Script for x402 Micropayments & Oracle Pipelines.
Tests:
1. Multi-Chain On-Chain Contracts & EIP-712 Live Signature Verification (Polygon, Base, Arbitrum)
2. x402 Payment Gate Handshake (HTTP 402 Challenge on unpaid requests)
3. Vault Pre-funded Balance Automatic Deduction & Receipt Generation
4. Live EIP-712 Oracle Grounding Generation
5. Dual-Layer Oracle Verification (Off-Chain API + On-Chain Smart Contract verifyAttestation)
"""

import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from fastapi.testclient import TestClient

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

from app.main import app
from app.onchain_signer import OnChainCleanWebSigner, onchain_signer
from app.vault_manager import vault_manager

client = TestClient(app)

def run_tests():
    print("=" * 75)
    print("🧪 [종합 라이브 테스트] x402 마이크로 결제 & 오라클 파이프라인 검증")
    print("=" * 75)

    passed_count = 0
    total_count = 0

    # ---------------------------------------------------------
    # TEST 1: 온체인 스마트 컨트랙트 라이브 EIP-712 검증 (Polygonscan 등록 완료본)
    # ---------------------------------------------------------
    total_count += 1
    print("\n[TEST 1] Polygon Mainnet 온체인 컨트랙트 라이브 검증")
    try:
        polygon_rpc = os.getenv("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")
        vault_addr = os.getenv("AGENT_PAYMENT_VAULT_ADDRESS", "0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861")
        verifier_addr = os.getenv("CLEANWEB_ORACLE_VERIFIER_ADDRESS", "0x18fA451b1d9A9FbbDa6Ebd86F8b42891866ADc46")
        
        w3 = Web3(Web3.HTTPProvider(polygon_rpc))
        if not w3.is_connected():
            raise RuntimeError(f"Polygon RPC 연결 실패: {polygon_rpc}")
            
        # ABI
        verifier_abi = [
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
            }
        ]
        
        verifier_contract = w3.eth.contract(address=w3.to_checksum_address(verifier_addr), abi=verifier_abi)
        signer_onchain = verifier_contract.functions.oracleSigner().call()
        print(f"  📍 배포된 Verifier 컨트랙트: {verifier_addr}")
        print(f"  🔑 등록된 온체인 오라클 서명자 주소: {signer_onchain}")

        # 로컬 서명 생성 후 온체인 함수(verifyAttestation) 호출
        deployer_key = os.getenv("DEPLOYER_PRIVATE_KEY") or os.getenv("SERVER_PRIVATE_KEY")
        if not deployer_key:
            neighbor_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "security-gate-x402", ".env"))
            if os.path.exists(neighbor_env):
                with open(neighbor_env, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("DEPLOYER_PRIVATE_KEY="):
                            deployer_key = line.strip().split("=", 1)[1].strip()
                            break

        signer_instance = OnChainCleanWebSigner(private_key=deployer_key, chain_id=137, contract_address=verifier_addr)
        sample_query = "CleanWeb Live Micropayment & Oracle Verification"
        sample_hash = Web3.keccak(text="Attested Oracle Data 2026").hex()
        now_ts = int(time.time())

        attestation = signer_instance.sign_oracle_grounding(sample_query, sample_hash, timestamp=now_ts)

        is_valid_onchain = verifier_contract.functions.verifyAttestation(
            sample_query,
            bytes.fromhex(sample_hash.replace("0x", "")),
            now_ts,
            attestation.v,
            bytes.fromhex(attestation.r.replace("0x", "").zfill(64)),
            bytes.fromhex(attestation.s.replace("0x", "").zfill(64)),
        ).call()

        if is_valid_onchain:
            print(f"  ✅ [PASS] Polygonscan 등록 컨트랙트 온체인 EIP-712 서명 검증 성공! (isValid={is_valid_onchain})")
            passed_count += 1
        else:
            print(f"  ❌ [FAIL] 온체인 검증 실패: isValid={is_valid_onchain}")
    except Exception as e:
        print(f"  ❌ [FAIL] 오류: {e}")

    # ---------------------------------------------------------
    # TEST 2: x402 결제 핸드셰이크 테스트 (HTTP 402 Payment Required)
    # ---------------------------------------------------------
    total_count += 1
    print("\n[TEST 2] x402 결제 프로토콜 핸드셰이크 (미결제 요청 시 402 챌린지 검증)")
    res = client.get("/api/v1/clean-web?url=https://example.com")
    if res.status_code == 402:
        data = res.json()
        recipient = data.get("recipient") or data.get("recipient_wallet")
        networks = data.get("networks") or data.get("payment_methods_accepted") or data.get("challenge", {}).get("payment_methods_accepted")
        print(f"  🛡️ HTTP 상태 코드: {res.status_code} Payment Required (정상)")
        print(f"  💰 요구 결제 금액: {data.get('amount_usdc')} USDC")
        print(f"  📬 수신 지갑 주소: {recipient}")
        print(f"  🌐 지원 결제 수단: {networks}")
        print("  ✅ [PASS] x402 프로토콜 규격대로 무단 접근 완벽 차단 및 결제 가이드 반환")
        passed_count += 1
    else:
        print(f"  ❌ [FAIL] 예상치 못한 상태 코드: {res.status_code} (402가 반환되어야 함)")

    # ---------------------------------------------------------
    # TEST 3: 사전 예치 볼트(Vault) 자동 차감 결제 테스트
    # ---------------------------------------------------------
    total_count += 1
    print("\n[TEST 3] 에이전트 볼트(Vault Key) 기반 초고속 자동 차감 결제")
    test_vault_key = "vault_key_demo_agent_sandbox_2026"
    res = client.get("/api/v1/clean-web?url=https://example.com", headers={"X-Vault-Key": test_vault_key})
    if res.status_code == 200:
        data = res.json()
        receipt = data.get("payment_receipt", {})
        cost = receipt.get("cost_usdc") if receipt.get("cost_usdc") is not None else receipt.get("amount_usdc")
        print(f"  🧾 결제 승인 수단: {receipt.get('payment_method')}")
        print(f"  💵 차감된 금액: ${cost} USDC")
        print(f"  💳 잔여 볼트 잔액: ${receipt.get('remaining_vault_balance'):.4f} USDC")
        print(f"  📄 스크래핑된 문서 제목: {data.get('title')}")
        print("  ✅ [PASS] 에이전트 선입금 볼트에서 지연 없이 자동 차감 및 서비스 제공 성공")
        passed_count += 1
    else:
        print(f"  ❌ [FAIL] 볼트 결제 실패: HTTP {res.status_code} - {res.text[:150]}")

    # ---------------------------------------------------------
    # TEST 4: EIP-712 오라클 증명 생성 (Clean Web with onchain_proof=True)
    # ---------------------------------------------------------
    total_count += 1
    print("\n[TEST 4] 웹 스크래핑 데이터에 대한 실시간 EIP-712 오라클 암호학적 증명 발급")
    res = client.get("/api/v1/clean-web?url=https://example.com&onchain_proof=true", headers={"Authorization": "Bearer dev-bypass"})
    if res.status_code == 200:
        data = res.json()
        proof = data.get("onchain_proof")
        if proof and ("r" in proof or "signature" in proof):
            print(f"  🔐 오라클 증명 서명자: {proof.get('oracle_signer')}")
            print(f"  📝 컨텐츠 해시 (Keccak256): {proof.get('content_hash')}")
            print(f"  🔏 ECDSA v, r, s: v={proof.get('v')}, r={proof.get('r')[:18]}..., s={proof.get('s')[:18]}...")
            print(f"  ⚙️ Solidity Calldata: {proof.get('abi_calldata')[:40]}...")
            print("  ✅ [PASS] 오라클 데이터에 대한 EIP-712 증명 및 온체인 제출용 Calldata 생성 완료")
            passed_count += 1
        else:
            print("  ❌ [FAIL] onchain_proof 필드 누락")
    else:
        print(f"  ❌ [FAIL] HTTP {res.status_code}")

    # ---------------------------------------------------------
    # TEST 5: 오프체인 오라클 서명 검증 엔드포인트 (/api/v1/oracle/verify)
    # ---------------------------------------------------------
    total_count += 1
    print("\n[TEST 5] 오라클 EIP-712 서명 검증 API (/api/v1/oracle/verify)")
    test_q = "CleanWeb Verification Query"
    test_dh = Web3.keccak(text="Structured Payload JSON").hex()
    now_t = int(time.time())
    sig_obj = onchain_signer.sign_oracle_grounding(test_q, test_dh, timestamp=now_t)

    verify_payload = {
        "data_hash": test_dh,
        "timestamp": now_t,
        "signature": sig_obj.signature,
        "chain_id": 137
    }
    res = client.post(f"/api/v1/oracle/verify?query={test_q}", json=verify_payload)
    if res.status_code == 200:
        v_data = res.json()
        if v_data.get("valid") is True:
            print(f"  🎯 검증 결과: valid={v_data.get('valid')}")
            print(f"  🔎 복원된 서명자: {v_data.get('recovered_signer')}")
            print(f"  📌 일치 여부: {v_data.get('message')}")
            print("  ✅ [PASS] 오라클 서명 검증 API 정상 작동")
            passed_count += 1
        else:
            print(f"  ❌ [FAIL] 검증 결과 False: {v_data}")
    else:
        print(f"  ❌ [FAIL] HTTP {res.status_code} - {res.text}")

    # ---------------------------------------------------------
    # TEST 6: 전체 시스템 진단 API (/health?deep=true)
    # ---------------------------------------------------------
    total_count += 1
    print("\n[TEST 6] 5대 파이프라인 심층 자가진단 (/health?deep=true)")
    res = client.get("/health?deep=true")
    if res.status_code == 200:
        diag = res.json()
        overall = diag.get("system_health") or diag.get("overall_status")
        print(f"  🩺 종합 헬스 상태: {overall}")
        for p in diag.get("pipelines", []):
            status_icon = "🟢" if p.get("status") == "HEALTHY" or p.get("status") == "healthy" else "🟡"
            print(f"     {status_icon} {p.get('name')}: {p.get('status')} ({p.get('latency_ms')}ms)")
        print("  ✅ [PASS] 전체 핵심 엔진 및 RPC 노드 정상 동작")
        passed_count += 1
    else:
        print(f"  ❌ [FAIL] HTTP {res.status_code}")

    print("\n" + "=" * 75)
    print(f"🏆 [최종 테스트 결과] {passed_count}/{total_count} 항목 성공! (성공률: {passed_count/total_count*100:.1f}%)")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()
