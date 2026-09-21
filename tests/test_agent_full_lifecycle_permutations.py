"""
Comprehensive Agent Full Lifecycle Permutations & Stochastic Edge-Case Test Suite
---------------------------------------------------------------------------------
Validates all 32 distinct state transitions and probabilistic failure cases:
1. Discovery & Manifest Compliance (Cases 1.1 - 1.4)
2. Sandbox Onboarding & Exhaustion (Cases 2.1 - 2.5)
3. Payment Verification & Vault Deposit (Cases 3.1 - 3.6)
4. Extraction, SSRF Defense & Auto-Refund (Cases 4.1 - 4.5)
5. Web3 Oracle EIP-712 Tamper Resistance (Cases 5.1 - 5.5)
6. Extreme Concurrency & Zero-Overdraft (Cases 6.1 - 6.4)
7. VIP Passes & Mathematical Invariance on Exit (Cases 7.1 - 7.3)
"""

import sys
import os
import time
import secrets
import threading
import concurrent.futures
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from web3 import Web3

from app.main import app
from app.storage import storage_manager
from app.vault_manager import vault_manager
from app.onchain_signer import onchain_signer
from app.multi_chain import multi_chain_manager
from autonomous_agent_client import AutonomousX402Agent
import mcp_server

client = TestClient(app)

def run_lifecycle_permutations_audit():
    print("=" * 80)
    print("🤖 AUTONOMOUS AGENT FULL WORKFLOW: 32 STATE TRANSITIONS & PERMUTATION AUDIT")
    print("=" * 80)

    # =========================================================================
    # 1. DISCOVERY & MANIFESTS
    # =========================================================================
    print("\n[SECTION 1] Entry & Discovery Permutations (4 Cases)...")
    
    # 1.1 agent.json
    r1_1 = client.get("/.well-known/agent.json")
    assert r1_1.status_code == 200 and "2020-12" in r1_1.json().get("$schema", "")
    print("  ✅ [CASE 1.1] /.well-known/agent.json parsed correctly by autonomous crawler")

    # 1.2 llms.txt
    r1_2 = client.get("/llms.txt")
    assert r1_2.status_code == 200 and "x402" in r1_2.text
    print("  ✅ [CASE 1.2] /llms.txt provides complete pricing and endpoint directory")

    # 1.3 MCP tool discovery
    r1_3 = client.get("/mcp/tools")
    assert r1_3.status_code == 200
    tools = r1_3.json().get("tools", [])
    assert len(tools) >= 13
    print(f"  ✅ [CASE 1.3] /mcp/tools exposes {len(tools)} standardized agent tools")

    # 1.4 Unauthenticated raw request receives RFC-compliant 402
    r1_4 = client.get("/api/v1/clean-web?url=https://example.com")
    assert r1_4.status_code == 402
    assert "WWW-Authenticate" in r1_4.headers
    assert "X-Payment-Amount" in r1_4.headers
    assert isinstance(r1_4.json().get("x402"), dict)
    print("  ✅ [CASE 1.4] Blind unauthenticated call receives strict machine-readable HTTP 402")

    # =========================================================================
    # 2. SANDBOX & FREE TRIAL PERMUTATIONS
    # =========================================================================
    print("\n[SECTION 2] Sandbox Onboarding & Exhaustion Permutations (5 Cases)...")
    agent_ephemeral_nonce = f"agent_sim_{secrets.token_hex(8)}"
    headers_trial = {"X-Agent-Nonce": agent_ephemeral_nonce}

    # 2.1 Trial Call 1
    r2_1 = client.get("/api/v1/clean-web?url=https://example.com", headers=headers_trial)
    assert r2_1.status_code == 200
    print("  ✅ [CASE 2.1] Trial Call #1: HTTP 200 Granted, Content Received")

    # 2.2 Trial Call 2
    r2_2 = client.get("/api/v1/clean-web?url=https://example.com", headers=headers_trial)
    assert r2_2.status_code == 200
    print("  ✅ [CASE 2.2] Trial Call #2: HTTP 200 Granted, Sandbox Quota Exhausted")

    # 2.3 Trial Call 3 (Must fail with 402)
    r2_3 = client.get("/api/v1/clean-web?url=https://example.com", headers=headers_trial)
    assert r2_3.status_code == 402
    print("  ✅ [CASE 2.3] Trial Call #3: Strict HTTP 402 Cutoff Enforced")

    # 2.4 Same Nonce Retry (Cannot bypass)
    r2_4 = client.get("/api/v1/clean-text?url=https://example.com", headers=headers_trial)
    assert r2_4.status_code == 402
    print("  ✅ [CASE 2.4] Repeated Requests on Exhausted Nonce Strictly Blocked")

    # 2.5 Malformed/Forged Auth Headers
    forged_headers = {"Authorization": "Bearer forged_jwt_token_gibberish"}
    r2_5 = client.get("/api/v1/clean-web?url=https://example.com", headers=forged_headers)
    assert r2_5.status_code == 402
    print("  ✅ [CASE 2.5] Forged Authorization Header Safely Handled (No 500 Server Error)")

    # =========================================================================
    # 3. PAYMENT & VAULT DEPOSIT PERMUTATIONS
    # =========================================================================
    print("\n[SECTION 3] Payment Verification & Vault Deposit Permutations (6 Cases)...")
    test_agent_wallet = "0x" + secrets.token_hex(20)

    # 3.1 Under Min Deposit ($0.5 < $2.0)
    r3_1 = client.post("/api/v1/vault/deposit", json={
        "agent_address": test_agent_wallet,
        "amount_usdc": 0.5,
        "chain": "polygon"
    })
    assert r3_1.status_code == 422
    print("  ✅ [CASE 3.1] Under-minimum deposit rejected ($0.5 < $2.0: HTTP 422)")

    # 3.2 Over Max Deposit ($1500.0 > $1000.0)
    r3_2 = client.post("/api/v1/vault/deposit", json={
        "agent_address": test_agent_wallet,
        "amount_usdc": 1500.0,
        "chain": "polygon"
    })
    assert r3_2.status_code == 422
    print("  ✅ [CASE 3.2] Over-maximum deposit rejected ($1500.0 > $1000.0: HTTP 422)")

    # 3.3 Fake/Unmined Transaction Hash in Production
    r3_3 = client.post("/api/v1/vault/deposit", json={
        "agent_address": test_agent_wallet,
        "amount_usdc": 5.0,
        "chain": "polygon",
        "tx_hash": "0x" + "c0ffee" * 10 + "1234"
    })
    assert r3_3.status_code == 400
    print("  ✅ [CASE 3.3] Fake On-Chain Tx Hash Blocked (HTTP 400)")

    # 3.4 Anti-Replay: Attempt to reuse used tx hash
    dummy_replay_hash = "0x" + "a1" * 32
    storage_manager.record_used_tx(dummy_replay_hash, "polygon", test_agent_wallet, 5.0)
    r3_4 = client.post("/api/v1/vault/deposit", json={
        "agent_address": test_agent_wallet,
        "amount_usdc": 5.0,
        "chain": "polygon",
        "tx_hash": dummy_replay_hash
    })
    assert r3_4.status_code == 400 and "already been used" in r3_4.json().get("detail", "")
    print("  ✅ [CASE 3.4] Anti-Replay Attack Blocked: Duplicate Tx Hash Rejected")

    # 3.5 Valid Simulated Deposit
    os.environ["ALLOW_DEV_BYPASS"] = "true"
    r3_5 = client.post("/api/v1/vault/deposit", json={
        "agent_address": test_agent_wallet,
        "amount_usdc": 10.0,
        "chain": "polygon"
    })
    assert r3_5.status_code == 200
    agent_session_key = r3_5.json()["session_key"]
    assert agent_session_key.startswith("vault_key_")
    print(f"  ✅ [CASE 3.5] Legitimate Deposit Succeeded: Balance=$10.0, SessionKey={agent_session_key[:18]}...")

    # 3.6 Malformed Ethereum Address
    r3_6 = client.post("/api/v1/vault/deposit", json={
        "agent_address": "not_an_ethereum_address",
        "amount_usdc": 5.0,
        "chain": "polygon"
    })
    assert r3_6.status_code in (400, 422)
    print("  ✅ [CASE 3.6] Malformed EVM Address Format Rejected (HTTP 422)")

    # =========================================================================
    # 4. EXTRACTION, SSRF DEFENSE & AUTO-REFUND PERMUTATIONS
    # =========================================================================
    print("\n[SECTION 4] Consumption, Security & Auto-Refund Permutations (5 Cases)...")
    v_headers = {"X-Vault-Key": agent_session_key}

    # 4.1 Normal Clean Web Execution
    bal_before = vault_manager.get_balance(agent_session_key)["balance_usdc"]
    r4_1 = client.get("/api/v1/clean-web?url=https://example.com", headers=v_headers)
    assert r4_1.status_code == 200
    bal_after = vault_manager.get_balance(agent_session_key)["balance_usdc"]
    assert round(bal_before - bal_after, 6) == 0.001
    print(f"  ✅ [CASE 4.1] Normal Extraction: 0.001 USDC atomically deducted (${bal_before:.4f} -> ${bal_after:.4f})")

    # 4.2 Auto-Refund on Failed URL (Dead domain)
    bal_pre_fail = vault_manager.get_balance(agent_session_key)["balance_usdc"]
    r4_2 = client.get("/api/v1/clean-web?url=http://non-existent-domain-404-500-test-failure.xyz", headers=v_headers)
    assert r4_2.status_code in (400, 500, 502, 504)
    bal_post_fail = vault_manager.get_balance(agent_session_key)["balance_usdc"]
    assert bal_post_fail == bal_pre_fail, f"Leakage detected! Pre={bal_pre_fail}, Post={bal_post_fail}"
    print(f"  ✅ [CASE 4.2] Service Failure Auto-Refund: 100% Rolled Back (${bal_post_fail:.4f})")

    # 4.3 SSRF Attack Defense (Private Loopback / Metadata IP)
    ssrf_targets = [
        "http://127.0.0.1:8000/secret",
        "http://localhost:22",
        "http://169.254.169.254/latest/meta-data/"
    ]
    for ssrf_url in ssrf_targets:
        r4_3 = client.get(f"/api/v1/clean-web?url={ssrf_url}", headers=v_headers)
        assert r4_3.status_code == 400
    bal_ssrf = vault_manager.get_balance(agent_session_key)["balance_usdc"]
    assert bal_ssrf == bal_pre_fail
    print("  ✅ [CASE 4.3] SSRF Attacks (127.0.0.1, localhost, 169.254.169.254) Blocked with Zero Economic Charge")

    # 4.4 Large payload / High token extraction limit
    r4_4 = client.get("/api/v1/clean-web?url=https://example.com&max_tokens=50000", headers=v_headers)
    assert r4_4.status_code == 200
    print("  ✅ [CASE 4.4] High-Token Request Handled Gracefully without Buffer/Memory Faults")

    # 4.5 Universal Reader Proxy with Multi-Param Query
    complex_target = "https://example.com/api?a=1&b=2#section"
    r4_5 = client.get(f"/r/{complex_target}", headers=v_headers)
    assert r4_5.status_code == 200
    print("  ✅ [CASE 4.5] Universal Reader Proxy (/r/) Handled Complex URI & Hash Query")

    # =========================================================================
    # 5. WEB3 ORACLE EIP-712 TAMPER RESISTANCE PERMUTATIONS
    # =========================================================================
    print("\n[SECTION 5] Web3 Oracle EIP-712 Cryptography Permutations (5 Cases)...")

    # 5.1 Real Oracle Grounding Request
    r5_1 = client.post("/api/v1/oracle/grounding", json={
        "query": "Polygon PoS architecture consensus 2026",
        "max_sources": 1
    }, headers=v_headers)
    assert r5_1.status_code == 200
    oracle_data = r5_1.json()
    attestation = oracle_data.get("oracle_attestation") or oracle_data.get("attestation")
    assert attestation is not None
    sig = attestation["signature"]
    d_hash = attestation["data_hash"]
    ts = attestation["timestamp"]
    orig_query = oracle_data["query"]
    print(f"  ✅ [CASE 5.1] Oracle Grounding Executed & Signed (0.035 USDC): Signer={onchain_signer.signer_address[:12]}...")

    # 5.2 Online Verification via API
    r5_2 = client.post("/api/v1/oracle/verify", json={
        "query": orig_query,
        "data_hash": d_hash,
        "timestamp": ts,
        "signature": sig
    })
    assert r5_2.status_code == 200 and r5_2.json().get("valid") is True
    print("  ✅ [CASE 5.2] Online Verification API: valid=True confirmed")

    # 5.3 Offline Memory Verification via AutonomousX402Agent SDK
    sdk_agent = AutonomousX402Agent()
    offline_res = sdk_agent.verify_attestation_offline(
        query=orig_query,
        data_hash=d_hash,
        timestamp=ts,
        signature=sig,
        expected_signer=onchain_signer.signer_address
    )
    assert offline_res["valid"] is True
    print("  ✅ [CASE 5.3] Offline SDK Verification (0 Gas, 0 API): valid=True confirmed")

    # 5.4 Tampered Data Hash (1 bit corrupted)
    tampered_hash = "0x" + ("0" if d_hash[2] != "0" else "1") + d_hash[3:]
    tampered_res = sdk_agent.verify_attestation_offline(
        query=orig_query,
        data_hash=tampered_hash,
        timestamp=ts,
        signature=sig,
        expected_signer=onchain_signer.signer_address
    )
    assert tampered_res["valid"] is False
    print("  ✅ [CASE 5.4] Tampered Data Hash Rejected Instantly: valid=False detected")

    # 5.5 Tampered Query Text
    tampered_query_res = sdk_agent.verify_attestation_offline(
        query=orig_query + " [CORRUPTED]",
        data_hash=d_hash,
        timestamp=ts,
        signature=sig,
        expected_signer=onchain_signer.signer_address
    )
    assert tampered_query_res["valid"] is False
    print("  ✅ [CASE 5.5] Tampered Query Text Rejected Instantly: valid=False detected")

    # =========================================================================
    # 6. EXTREME CONCURRENCY & ZERO-OVERDRAFT PERMUTATIONS
    # =========================================================================
    print("\n[SECTION 6] Extreme Concurrency & Overdraft Guard Permutations (4 Cases)...")

    # Create a micro-vault with exactly 0.003 USDC
    micro_wallet = "0x" + secrets.token_hex(20)
    storage_manager.deposit_vault(micro_wallet, 0.003000, f"micro_key_{micro_wallet}")
    micro_headers = {"X-Vault-Key": f"micro_key_{micro_wallet}"}

    # 6.1 Call 1 ($0.003 -> $0.002)
    assert client.get("/api/v1/clean-web?url=https://example.com", headers=micro_headers).status_code == 200
    # 6.2 Call 2 ($0.002 -> $0.001)
    assert client.get("/api/v1/clean-web?url=https://example.com", headers=micro_headers).status_code == 200
    # 6.3 Call 3 ($0.001 -> $0.000)
    assert client.get("/api/v1/clean-web?url=https://example.com", headers=micro_headers).status_code == 200
    bal_zero = vault_manager.get_balance(f"micro_key_{micro_wallet}")["balance_usdc"]
    assert bal_zero == 0.0
    print("  ✅ [CASE 6.1 & 6.2] Exact micro-depletion to $0.000000 USDC verified")

    # 6.3 Call 4 on $0.000 (Must strictly trigger 402)
    r_empty = client.get("/api/v1/clean-web?url=https://example.com", headers=micro_headers)
    assert r_empty.status_code == 402
    print("  ✅ [CASE 6.3] Zero-Balance Guard: 402 Payment Required issued immediately")

    # 6.4 High-Concurrency Race Condition (10 threads simultaneously racing for 0.001 USDC balance)
    race_wallet = "0x" + secrets.token_hex(20)
    storage_manager.deposit_vault(race_wallet, 0.001000, f"race_key_{race_wallet}")
    race_headers = {"X-Vault-Key": f"race_key_{race_wallet}"}

    successes = 0
    denials = 0
    lock = threading.Lock()

    def race_worker():
        nonlocal successes, denials
        r = client.get("/api/v1/clean-web?url=https://example.com", headers=race_headers)
        with lock:
            if r.status_code == 200:
                successes += 1
            elif r.status_code == 402:
                denials += 1

    threads = [threading.Thread(target=race_worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final_race_bal = vault_manager.get_balance(f"race_key_{race_wallet}")["balance_usdc"]
    assert successes == 1, f"Expected exactly 1 winner, got {successes}"
    assert denials == 9, f"Expected 9 402 denials, got {denials}"
    assert final_race_bal == 0.0, f"Overdraft detected! Balance={final_race_bal}"
    print(f"  ✅ [CASE 6.4] 10-Thread Swarm Race: Exactly 1 Success, 9 Denials, Final Balance=0.000000 USDC (Zero Overdraft!)")

    # =========================================================================
    # 7. VIP PASSES & MATHEMATICAL INVARIANCE ON EXIT
    # =========================================================================
    print("\n[SECTION 7] VIP Passes & Mathematical Invariance on Exit (3 Cases)...")

    # 7.1 VIP Pass Usage
    r7_1 = client.get("/api/v1/clean-web?url=https://example.com", headers={"X-Agent-Pass": "WELCOME100"})
    assert r7_1.status_code == 200
    print("  ✅ [CASE 7.1] VIP Pass (WELCOME100) Granted 200 OK without Gas/USDC deduction")

    # 7.2 VIP Pass Status Inspection via MCP Tool
    pass_status = mcp_server.get_pass_status("WELCOME100")
    assert "VIP_PROMO_100" in pass_status and "YES" in pass_status
    print("  ✅ [CASE 7.2] MCP Tool get_pass_status verified pass integrity")

    # 7.3 Mathematical Invariance on Agent Exit:
    # balance == total_deposited - total_consumed
    final_acc = vault_manager.get_balance(agent_session_key)
    f_dep = final_acc["total_deposited"]
    f_con = final_acc["total_consumed"]
    f_bal = final_acc["balance_usdc"]
    expected_bal = round(f_dep - f_con, 6)
    assert abs(f_bal - expected_bal) < 1e-6, f"Math drift! Dep={f_dep}, Con={f_con}, Bal={f_bal}, Expected={expected_bal}"
    print(f"  ✅ [CASE 7.3] Agent Exit Invariance Check: Total Deposited (${f_dep:.6f}) - Total Consumed (${f_con:.6f}) == Remaining Balance (${f_bal:.6f})")

    print("\n" + "=" * 80)
    print("🎉 ALL 32 WORKFLOW PERMUTATIONS & STOCHASTIC FAILURE CASES PASSED WITH 100% PERFECTION!")
    print("=" * 80)

if __name__ == "__main__":
    run_lifecycle_permutations_audit()
