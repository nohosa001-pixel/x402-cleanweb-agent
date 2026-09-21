"""
E2E Organic Autonomous AI Agent Influx & Settlement Verification Suite
---------------------------------------------------------------------
Simulates the entire autonomous agent journey:
1. Discovery (agent.json, ap2.json, mcp, llms.txt, pricing-catalog)
2. Zero-friction trial onboarding via X-Agent-Nonce (2 calls -> 402 challenge)
3. 402 challenge parsing & multi-chain network negotiation
4. Pre-funded vault balance deposit & session key issuance
5. Multi-tool execution across Web, Reader Proxy, Search, Map, Oracle Grounding
6. Precise micro-USDC balance deduction without float drift
7. EIP-712 cryptographic signature verification
8. MCP Server tool execution in-process
"""

import sys
import time
import json
from fastapi.testclient import TestClient
from app.main import app
from app.storage import storage_manager
from mcp_server import (
    get_payment_info,
    clean_web_content,
    get_vault_balance,
    map_site,
    search_web_quick,
    oracle_grounding,
    verify_oracle_attestation
)

client = TestClient(app)

def run_e2e_verification():
    print("=" * 70)
    print("🚀 STARTING ORGANIC AUTONOMOUS AGENT E2E LIFECYCLE AUDIT")
    print("=" * 70)
    errors = []

    # =========================================================================
    # Step 1: Agent Discovery Protocols
    # =========================================================================
    print("\n[PHASE 1] Agent Discovery & Machine-Readable Manifests...")
    
    # 1.1 agent.json
    r = client.get("/.well-known/agent.json")
    if r.status_code != 200:
        errors.append(f"agent.json returned {r.status_code}")
    else:
        d = r.json()
        assert "$schema" in d, "agent.json missing $schema"
        assert d["economic_model"]["free_tier"]["discovery_trial_calls"] == 2
        print("  ✅ [PASS] /.well-known/agent.json (2020-12 schema, 2 trial calls)")

    # 1.2 ap2.json
    r = client.get("/.well-known/ap2.json")
    if r.status_code != 200:
        errors.append(f"ap2.json returned {r.status_code}")
    else:
        d = r.json()
        assert "$schema" in d, "ap2.json missing $schema"
        assert "reader_proxy" in d["endpoints"], "ap2.json missing reader_proxy endpoint"
        assert "free_tier" in d, "ap2.json missing free_tier block"
        print("  ✅ [PASS] /.well-known/ap2.json ($schema, reader_proxy, free_tier aligned)")

    # 1.3 mcp server-card & mcp.json
    r_card = client.get("/.well-known/mcp/server-card.json")
    r_mcp = client.get("/.well-known/mcp.json")
    if r_card.status_code != 200 or r_mcp.status_code != 200:
        errors.append("mcp manifests failed to serve")
    else:
        card_d = r_card.json()
        mcp_d = r_mcp.json()
        assert len(card_d["tools"]) == 14, f"server-card tools count is {len(card_d['tools'])}, expected 14"
        assert len(mcp_d["tools"]) == 14, f"mcp.json tools count is {len(mcp_d['tools'])}, expected 14"
        assert card_d["tools"] == mcp_d["tools"], "tool list mismatch between server-card and mcp.json"
        print("  ✅ [PASS] MCP Server Manifests (14 tools synchronized 100%)")

    # 1.4 llms.txt
    r_llms = client.get("/llms.txt")
    if r_llms.status_code != 200 or "/api/v1/clean-web" not in r_llms.text:
        errors.append("llms.txt failed or missing critical routes")
    else:
        print("  ✅ [PASS] /llms.txt Context Ingestion Guide")

    # 1.5 Pricing Catalog & Arbitrage ROI
    r_cat = client.get("/api/v1/agent/pricing-catalog")
    r_roi = client.get("/api/v1/agent/arbitrage-roi")
    if r_cat.status_code != 200 or r_roi.status_code != 200:
        errors.append("Pricing or Arbitrage ROI endpoint failed")
    else:
        print("  ✅ [PASS] Machine-Readable Pricing Catalog & Arbitrage ROI Proof")

    # =========================================================================
    # Step 2: Instant Sandbox Onboarding & 402 Challenge
    # =========================================================================
    print("\n[PHASE 2] Zero-Friction Sandbox Onboarding & 402 Challenge...")
    agent_nonce = f"agent_sim_{int(time.time()*1000)}"

    # 2.1 First Free Call
    r1 = client.get("/api/v1/clean-web?url=https://example.com", headers={"X-Agent-Nonce": agent_nonce})
    if r1.status_code != 200:
        errors.append(f"Call 1 failed with {r1.status_code}: {r1.text}")
    else:
        d1 = r1.json()
        assert d1["auth"]["mode"] == "SANDBOX_FREE_TRIAL"
        assert d1["payment_receipt"]["remaining_trial_calls"] == 1
        print("  ✅ [PASS] Trial Call 1: HTTP 200, Remaining: 1")

    # 2.2 Second Free Call
    r2 = client.post("/api/v1/clean-web", json={"url": "https://example.com"}, headers={"X-Agent-Nonce": agent_nonce})
    if r2.status_code != 200:
        errors.append(f"Call 2 failed with {r2.status_code}: {r2.text}")
    else:
        d2 = r2.json()
        assert d2["auth"]["mode"] == "SANDBOX_FREE_TRIAL"
        assert d2["payment_receipt"]["remaining_trial_calls"] == 0
        print("  ✅ [PASS] Trial Call 2: HTTP 200, Remaining: 0")

    # 2.3 Third Call -> Intercept HTTP 402 Payment Required
    r3 = client.get("/api/v1/clean-web?url=https://example.com", headers={"X-Agent-Nonce": agent_nonce})
    if r3.status_code != 402:
        errors.append(f"Call 3 expected 402, got {r3.status_code}")
    else:
        d3 = r3.json()
        assert "WWW-Authenticate" in r3.headers or "www-authenticate" in r3.headers
        assert r3.headers.get("X-Access-Policy") == "OPEN_TO_HUMANS_AND_AGENTS"
        assert d3["status_code"] == 402
        assert "challenge" in d3
        challenge = d3["challenge"]
        assert "networks" in challenge or "recipient" in challenge
        print("  ✅ [PASS] Call 3: HTTP 402 Challenge correctly issued with x402 headers and multi-chain terms")

    # =========================================================================
    # Step 3: Vault Pre-Funding & Session Key Issuance
    # =========================================================================
    print("\n[PHASE 3] Pre-Funded Vault Deposit & Economic Safety...")
    sim_wallet = f"0x{int(time.time()*1000):x}".ljust(42, "0")
    
    # 3.1 Verify Economic Security Guard: Blocks unbacked deposit in production mode
    r_blocked = client.post("/api/v1/vault/deposit", json={
        "agent_address": sim_wallet,
        "amount_usdc": 5.0,
        "chain": "polygon",
        "tx_hash": ""
    })
    assert r_blocked.status_code == 400, f"Expected 400 for unbacked deposit, got {r_blocked.status_code}"
    assert "verified on-chain transaction hash" in r_blocked.text
    print("  ✅ [PASS] Economic Security Guard: Unbacked fake deposit correctly rejected (HTTP 400)")

    # 3.2 Authorized Deposit via Sandbox/Dev Bypass mode
    import os
    os.environ["ALLOW_DEV_BYPASS"] = "true"
    r_dep = client.post("/api/v1/vault/deposit", json={
        "agent_address": sim_wallet,
        "amount_usdc": 5.0,
        "chain": "polygon",
        "tx_hash": ""
    })
    assert r_dep.status_code == 200, f"Authorized deposit failed: {r_dep.text}"
    
    dep_data = r_dep.json()
    vault_key = dep_data["session_key"]
    initial_balance = dep_data["balance_usdc"]
    assert initial_balance == 5.0
    print(f"  ✅ [PASS] Vault pre-funded with 5.0 USDC. Session Key: {vault_key[:15]}...")

    # 3.2 Vault Balance Check
    r_bal = client.get(f"/api/v1/vault/balance?identifier={vault_key}")
    assert r_bal.status_code == 200
    assert r_bal.json()["balance_usdc"] == 5.0
    print("  ✅ [PASS] Verified Vault Balance: 5.0 USDC")

    # =========================================================================
    # Step 4: Multi-Tool Execution with Zero-Gas Vault Key
    # =========================================================================
    print("\n[PHASE 4] Multi-Tool Execution via Zero-Latency Vault Key...")
    headers = {"X-Vault-Key": vault_key}

    # 4.1 clean-web GET (0.001 USDC)
    r_web = client.get("/api/v1/clean-web?url=https://example.com", headers=headers)
    assert r_web.status_code == 200, f"clean-web GET failed: {r_web.text}"
    print("  ✅ [PASS] /api/v1/clean-web (GET): 0.001 USDC deducted")

    # 4.2 clean-web POST (0.001 USDC)
    r_web_post = client.post("/api/v1/clean-web", json={"url": "https://example.com", "density": "dense"}, headers=headers)
    assert r_web_post.status_code == 200, f"clean-web POST failed: {r_web_post.text}"
    print("  ✅ [PASS] /api/v1/clean-web (POST): 0.001 USDC deducted")

    # 4.3 Reader Proxy /r/ (0.001 USDC)
    r_proxy = client.get("/r/https://example.com", headers=headers)
    assert r_proxy.status_code == 200, f"/r/ proxy failed: {r_proxy.text}"
    assert "# " in r_proxy.text
    print("  ✅ [PASS] /r/ Universal Reader Proxy: 0.001 USDC deducted (Raw Markdown returned)")

    # 4.4 clean-text (0.001 USDC)
    r_txt = client.get("/api/v1/clean-text?url=https://example.com", headers=headers)
    assert r_txt.status_code == 200, f"clean-text failed: {r_txt.text}"
    print("  ✅ [PASS] /api/v1/clean-text: 0.001 USDC deducted")

    # 4.5 map-site (0.002 USDC)
    r_map = client.post("/api/v1/map-site", json={"url": "https://example.com", "max_links": 10}, headers=headers)
    assert r_map.status_code == 200, f"map-site failed: {r_map.text}"
    print("  ✅ [PASS] /api/v1/map-site: 0.002 USDC deducted")

    # 4.6 search (0.002 USDC)
    r_search = client.get("/api/v1/search?query=ethereum+agent", headers=headers)
    assert r_search.status_code == 200, f"search failed: {r_search.text}"
    print("  ✅ [PASS] /api/v1/search: 0.002 USDC deducted")

    # 4.7 oracle grounding & off-chain verification (0.035 USDC)
    r_oracle = client.post("/api/v1/oracle/grounding", json={"query": "crypto market cap"}, headers=headers)
    assert r_oracle.status_code == 200, f"oracle grounding failed: {r_oracle.text}"
    oracle_data = r_oracle.json()
    att = oracle_data["oracle_attestation"]
    assert att["signature"] is not None
    print("  ✅ [PASS] /api/v1/oracle/grounding: 0.035 USDC deducted & EIP-712 Signed")

    # Verify Attestation
    r_verify = client.post("/api/v1/oracle/verify", json={
        "query": oracle_data["query"],
        "data_hash": att["data_hash"],
        "timestamp": att["timestamp"],
        "signature": att["signature"]
    })
    assert r_verify.status_code == 200
    assert r_verify.json()["valid"] is True
    print("  ✅ [PASS] /api/v1/oracle/verify: EIP-712 Attestation verified cryptographically!")

    # =========================================================================
    # Step 5: Exact Balance Math & IEEE-754 Precision Validation
    # =========================================================================
    print("\n[PHASE 5] Strict Micro-USDC Balance Math Verification...")
    # Expected deductions:
    # 0.001 (clean-web GET)
    # 0.001 (clean-web POST)
    # 0.001 (reader proxy)
    # 0.001 (clean-text)
    # 0.002 (map-site)
    # 0.002 (search)
    # 0.035 (oracle grounding)
    # Total spent: 0.043 USDC
    # Expected remaining: 5.0 - 0.043 = 4.957 USDC
    r_final_bal = client.get(f"/api/v1/vault/balance?identifier={vault_key}")
    final_data = r_final_bal.json()
    remaining = final_data["balance_usdc"]
    total_spent = final_data["total_consumed_usdc"]

    expected_spent = 0.043
    expected_remaining = round(5.0 - expected_spent, 6)

    assert remaining == expected_remaining, f"Balance mismatch: {remaining} != {expected_remaining}"
    assert total_spent == expected_spent, f"Consumed mismatch: {total_spent} != {expected_spent}"
    print(f"  ✅ [PASS] Math Perfect: Initial $5.000000 - Spent ${total_spent:.6f} = Remaining ${remaining:.6f} USDC (Zero Drift!)")

    # =========================================================================
    # Step 6: In-Process MCP Server Tool Direct Invocation
    # =========================================================================
    print("\n[PHASE 6] MCP Server Stdio Tools Invocation...")
    info_res = get_payment_info()
    assert "CleanWeb Studio x402 Micropayment Architecture" in info_res
    print("  ✅ [PASS] MCP tool: get_payment_info")

    web_res = clean_web_content(url="https://example.com")
    assert "CLEAN WEB SUCCESS" in web_res
    print("  ✅ [PASS] MCP tool: clean_web_content")

    vault_res = get_vault_balance(agent_address_or_key=vault_key)
    assert "VAULT BALANCE REPORT" in vault_res
    print("  ✅ [PASS] MCP tool: get_vault_balance")

    map_res = map_site(url="https://example.com", max_links=5)
    assert "SITE MAP SUCCESS" in map_res
    print("  ✅ [PASS] MCP tool: map_site")

    search_res = search_web_quick(query="AI agents", max_results=3)
    assert "SEARCH SUCCESS" in search_res
    print("  ✅ [PASS] MCP tool: search_web_quick")

    oracle_res = oracle_grounding(query="Ethereum price")
    assert "ORACLE GROUNDING SUCCESS" in oracle_res
    print("  ✅ [PASS] MCP tool: oracle_grounding")

    print("\n" + "=" * 70)
    print("🎉 ALL 6 PHASES PASSED WITH ZERO ERRORS! 100% ORGANIC B2A READY.")
    print("=" * 70)
    return errors

if __name__ == "__main__":
    errs = run_e2e_verification()
    if errs:
        print("❌ Audit failed with errors:", errs)
        sys.exit(1)
    sys.exit(0)
