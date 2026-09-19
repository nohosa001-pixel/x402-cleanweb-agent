import time
from fastapi.testclient import TestClient
from app.main import app
from app.storage import storage_manager

client = TestClient(app)

def test_full_autonomous_agent_vault_lifecycle():
    # 1. 402 when quota exhausted (Verify strict human rejection headers & specs)
    exhausted_id = f"test_user_{int(time.time()*1000)}"
    storage_manager.increment_trial_usage(exhausted_id)
    storage_manager.increment_trial_usage(exhausted_id)
    
    r402 = client.get("/api/v1/clean-web?url=https://example.com", headers={"X-Agent-Nonce": exhausted_id})
    assert r402.status_code == 402
    data402 = r402.json()
    assert data402["status_code"] == 402
    assert data402["audience"] == "HUMANS_AND_AUTONOMOUS_AGENTS"
    assert "OPEN_TO_ALL" in data402.get("access_policy", "")
    assert r402.headers.get("X-Access-Policy") == "OPEN_TO_HUMANS_AND_AGENTS"
    assert "challenge" in data402
    
    # 2. Autonomous Agent Self-Funds Vault (2.0 USDC minimum)
    agent_wallet = f"0x{int(time.time()*1000):x}".ljust(42, "0")
    r_deposit = client.post("/api/v1/vault/deposit", json={
        "agent_address": agent_wallet,
        "amount_usdc": 5.0,
        "chain": "polygon",
        "tx_hash": ""
    })
    assert r_deposit.status_code == 200
    dep_data = r_deposit.json()
    assert dep_data["balance_usdc"] >= 5.0
    vault_key = dep_data["session_key"]
    assert "vault_key_" in vault_key
    
    # 3. Check vault-balance endpoint
    r_bal = client.get(f"/api/v1/vault/balance?identifier={vault_key}")
    assert r_bal.status_code == 200
    assert r_bal.json()["balance_usdc"] >= 5.0
    
    # 4. Autonomous Agent Executes Request with X-Vault-Key (Zero-Gas, Sub-1ms)
    r_paid = client.get(
        "/api/v1/clean-web?url=https://example.com",
        headers={"X-Vault-Key": vault_key}
    )
    assert r_paid.status_code == 200
    paid_data = r_paid.json()
    assert paid_data["status"] == "success"
    assert paid_data["payment_receipt"]["payment_method"] == "VAULT_BALANCE"
    assert paid_data["payment_receipt"]["remaining_vault_balance"] < 5.0
    assert paid_data["auth"]["mode"] == "VAULT_BALANCE"

def test_human_webhook_endpoints_blocked():
    # Verify legacy human payment webhook routes do not exist in pure B2A architecture
    r_ls = client.post("/api/v1/webhook/payment", json={"test": True})
    assert r_ls.status_code in (404, 405)


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
    
    # Markdown Renderer and CleanWeb Studio integration checks
    assert "marked.min.js" in html
    assert "headerVaultBalance" in html
    assert "btnCheckBalance" in html
    assert "currentOutputTab" in html
    assert "tabProofBtn" in html
    assert "tabJsonBtn" in html



