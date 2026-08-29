"""
Unit and Integration Tests for x402 Payments, Multi-chain, Vault, and EIP-712 Signer.
"""

import time
import pytest
from fastapi.testclient import TestClient
from web3 import Web3

from app.main import app
from app.storage import storage_manager
from app.vault_manager import vault_manager
from app.onchain_signer import onchain_signer
from app.multi_chain import multi_chain_manager

client = TestClient(app)


def test_multi_chain_configs():
    for chain_id, name in [(137, "polygon"), (8453, "base"), (42161, "arbitrum")]:
        cfg = multi_chain_manager.get_chain_config(name)
        assert cfg.chain_id == chain_id
        assert Web3.is_address(cfg.usdc_address)


def test_onchain_eip712_attestation():
    url = "https://example.com/research-paper"
    text = "# Verified Research\nThis is a verified document."
    proof = onchain_signer.sign_cleanweb_attestation(target_url=url, content_text=text)
    
    assert proof.target_url == url
    assert proof.content_hash.startswith("0x")
    assert proof.oracle_signer == onchain_signer.signer_address
    assert proof.v in (27, 28)
    assert proof.abi_calldata.startswith("0x")


def test_vault_deposit_and_deduct():
    agent_addr = "0x1111111111111111111111111111111111111111"
    # Deposit
    acc = vault_manager.deposit(agent_addr, 5.0, chain="polygon")
    assert acc["balance_usdc"] >= 5.0
    
    # Deduct 0.001
    ok, rem_bal, updated = vault_manager.deduct(agent_addr, 0.001)
    assert ok is True
    assert round(rem_bal, 3) >= 4.999


def test_402_challenge_returned_when_unauthorized():
    # Exhaust free trial identifier
    ident = f"exhausted_{int(time.time())}"
    storage_manager.increment_trial_usage(ident)
    storage_manager.increment_trial_usage(ident)
    
    res = client.get("/api/v1/clean-web?url=https://example.com", headers={"X-Agent-Nonce": ident})
    assert res.status_code == 402
    data = res.json()
    assert data["error"] == "Payment Required"
    assert "challenge" in data
    assert "recipient_wallet" in data["challenge"]


def test_dev_bypass():
    res = client.get("/api/v1/clean-web?url=https://example.com", headers={"Authorization": "Bearer dev-bypass"})
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["payment_receipt"]["payment_method"] == "DEV_BYPASS"
