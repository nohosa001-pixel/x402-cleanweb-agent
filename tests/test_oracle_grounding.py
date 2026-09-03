"""
Unit tests for the Oracle-Grade Agent Grounding Pipeline.
Tests 402 challenge, real-time search & clean-to-json synthesis,
EIP-712 cryptographic oracle attestation, off-chain verification, and vault deduction.
"""

import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage import storage_manager
from app.vault_manager import vault_manager
from app.onchain_signer import onchain_signer

client = TestClient(app)


def test_oracle_grounding_402_challenge():
    """Verify that unauthorized requests receive HTTP 402 with 0.035 USDC challenge."""
    exhausted_id = f"oracle_user_{int(time.time()*1000)}"
    storage_manager.increment_trial_usage(exhausted_id)
    storage_manager.increment_trial_usage(exhausted_id)

    resp = client.post(
        "/api/v1/oracle/grounding",
        json={"query": "US Federal Reserve interest rate decision latest"},
        headers={"X-Agent-Nonce": exhausted_id},
    )
    assert resp.status_code == 402
    body = resp.json()
    assert body["status_code"] == 402
    assert "challenge" in body
    assert float(body["challenge"]["amount_usdc"]) == 0.035



def test_oracle_grounding_execution_with_attestation():
    """Verify the end-to-end execution of search + clean-to-JSON + EIP-712 signature."""
    query_str = "Bitcoin halving schedule and block reward history"
    target_schema = {
        "asset": "str",
        "current_reward": "float",
        "next_halving_year": "int",
        "key_takeaway": "str"
    }

    resp = client.post(
        "/api/v1/oracle/grounding",
        json={
            "query": query_str,
            "target_schema": target_schema,
            "max_sources": 2
        },
        headers={"X-Agent-Pass": "WELCOME100"}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert data["query"] == query_str
    assert isinstance(data["structured_data"], dict)
    assert len(data["summary_markdown"]) > 20
    assert len(data["source_urls"]) > 0

    # Verify Oracle Attestation payload
    att = data["oracle_attestation"]
    assert att["query"] == query_str
    assert att["data_hash"].startswith("0x")
    assert att["oracle_signer"].startswith("0x")
    assert att["v"] in (27, 28)
    assert att["r"].startswith("0x")
    assert att["s"].startswith("0x")
    assert att["signature"].startswith("0x")

    # Step 2: Verify the signature with /api/v1/oracle/verify
    v_resp = client.post(
        f"/api/v1/oracle/verify?query={query_str}",
        json={
            "data_hash": att["data_hash"],
            "timestamp": att["timestamp"],
            "signature": att["signature"],
            "oracle_signer": att["oracle_signer"],
        }
    )
    assert v_resp.status_code == 200
    v_data = v_resp.json()
    assert v_data["valid"] is True
    assert v_data["recovered_signer"].lower() == onchain_signer.signer_address.lower()


def test_oracle_vault_deduction_0_035():
    """Verify that a pre-funded agent vault is charged exactly 0.035 USDC per oracle query."""
    test_agent = f"0x{int(time.time()*1000):x}".ljust(42, "0")

    # 1. Deposit 2.0 USDC (Minimum)
    r_dep = client.post("/api/v1/vault/deposit", json={
        "agent_address": test_agent,
        "amount_usdc": 2.0,
        "chain": "polygon",
        "tx_hash": ""
    })
    assert r_dep.status_code == 200
    session_key = r_dep.json()["session_key"]
    initial_balance = r_dep.json()["balance_usdc"]

    # 2. Call Oracle Grounding using X-Vault-Key
    r_call = client.post(
        "/api/v1/oracle/grounding",
        json={"query": "Ethereum Pectra upgrade timeline", "max_sources": 1},
        headers={"X-Vault-Key": session_key}
    )
    assert r_call.status_code == 200
    call_data = r_call.json()
    assert call_data["payment_receipt"]["cost_usdc"] == 0.035

    # 3. Check Vault Balance
    r_bal = client.get(f"/api/v1/vault/balance?identifier={session_key}")
    assert r_bal.status_code == 200
    new_bal = r_bal.json()["balance_usdc"]
    assert round(initial_balance - new_bal, 3) == 0.035
