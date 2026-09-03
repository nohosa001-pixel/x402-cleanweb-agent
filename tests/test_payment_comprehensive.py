import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage import storage_manager

client = TestClient(app)

def test_full_payment_lifecycle():
    # 1. 402 when quota exhausted
    exhausted_id = f"test_user_{int(time.time()*1000)}"
    storage_manager.increment_trial_usage(exhausted_id)
    storage_manager.increment_trial_usage(exhausted_id)
    
    r402 = client.get("/api/v1/clean-web?url=https://example.com", headers={"X-Agent-Nonce": exhausted_id})
    assert r402.status_code == 402
    assert r402.json()["status_code"] == 402
    assert "challenge" in r402.json()
    
    # 2. Webhook order_created generates pass with 100 credits
    wh_payload = {
        "meta": {"event_name": "order_created"},
        "data": {
            "id": "order_test_lifecycle_100",
            "attributes": {
                "user_email": "buyer@cleanweb.ai",
                "total_formatted": "$1.00",
                "first_order_item": {"variant_name": "100_passes"}
            }
        }
    }
    r_wh = client.post("/api/v1/webhook/lemonsqueezy", json=wh_payload)
    assert r_wh.status_code == 200
    wh_data = r_wh.json()
    assert wh_data["status"] == "success"
    pass_token = wh_data["pass_token"]
    assert wh_data["credits"] == 100
    
    # 3. Check pass-status endpoint
    r_stat = client.get(f"/api/v1/pass-status?agent_wallet={pass_token}")
    assert r_stat.status_code == 200
    stat_data = r_stat.json()
    assert stat_data["has_active_pass"] is True
    assert stat_data["remaining_credits"] == 100
    
    # 4. Use pass in X-Agent-Pass header
    r_paid = client.get(
        "/api/v1/clean-web?url=https://example.com",
        headers={"X-Agent-Pass": pass_token}
    )
    assert r_paid.status_code == 200
    paid_data = r_paid.json()
    assert paid_data["status"] == "success"
    assert paid_data["auth"]["remaining_credits"] == 99
    assert paid_data["auth"]["credits_deducted"] == 1
    assert paid_data["payment_receipt"]["remaining_credits"] == 99

def test_vip_promo_code():
    r_promo = client.get(
        "/api/v1/clean-web?url=https://example.com",
        headers={"X-Agent-Pass": "WELCOME100"}
    )
    assert r_promo.status_code == 200
    pdata = r_promo.json()
    assert pdata["status"] == "success"
    assert pdata["auth"]["mode"] == "VIP_PROMO"
    assert pdata["auth"]["remaining_credits"] > 0

def test_b2a_vault_deposit_limits_lifecycle():
    vault_agent = f"0x{int(time.time()*1000):x}".ljust(42, "0")

    # 1. Below Minimum (< 2.0 USDC) must fail
    r_low = client.post("/api/v1/vault/deposit", json={
        "agent_address": vault_agent,
        "amount_usdc": 1.5,
        "chain": "polygon",
        "tx_hash": ""
    })
    assert r_low.status_code in (400, 422)

    # 2. Above Maximum (> 1000.0 USDC) must fail
    r_high = client.post("/api/v1/vault/deposit", json={
        "agent_address": vault_agent,
        "amount_usdc": 1000.5,
        "chain": "polygon",
        "tx_hash": ""
    })
    assert r_high.status_code in (400, 422)

    # 3. Exactly Minimum (2.0 USDC) must succeed
    r_min = client.post("/api/v1/vault/deposit", json={
        "agent_address": vault_agent,
        "amount_usdc": 2.0,
        "chain": "polygon",
        "tx_hash": ""
    })
    assert r_min.status_code == 200
    min_data = r_min.json()
    assert min_data["balance_usdc"] >= 2.0
    assert "vault_key_" in min_data["session_key"]

    # 4. Large Deposit up to Max Cap (1000.0 USDC) must succeed
    agent_enterprise = f"0x{int(time.time()*1000)+1:x}".ljust(42, "0")
    r_max = client.post("/api/v1/vault/deposit", json={
        "agent_address": agent_enterprise,
        "amount_usdc": 1000.0,
        "chain": "base",
        "tx_hash": ""
    })
    assert r_max.status_code == 200
    assert r_max.json()["balance_usdc"] >= 1000.0

def test_ui_html_payment_components():
    r_html = client.get("/dashboard")
    assert r_html.status_code == 200
    html = r_html.text
    
    # Markdown Renderer and B2A Agent Vault integration checks
    assert "marked.min.js" in html
    assert "depositVaultUSDC" in html
    assert "customVaultAmtInput" in html
    
    # UI Modals, Toolbar, & Paywall components
    assert "paymentModal" in html
    assert "openPaymentModal" in html
    assert "saveAndActivatePass" in html
    assert "payCryptoUSDC" in html
    assert "console-toolbar" in html
    assert "tab-pricing" in html
    assert "tab-oracle" in html
    assert "runOracleGrounding" in html


