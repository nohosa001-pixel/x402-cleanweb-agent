"""Integration test suite verifying agrid-ops-agent as central A.GRID Clearing & Treasury Hub."""
import os
import sys

# Windows console UTF-8 support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure agrid-ops-agent path is in sys.path
OPS_PATH = os.path.abspath(os.path.join("..", "agrid-ops-agent"))
sys.path.insert(0, OPS_PATH)

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_agrid_service_registry():
    res = client.get("/api/v1/grid/registry")
    assert res.status_code == 200
    data = res.json()
    assert data["hq_service"] == "agrid-ops-agent"
    assert data["total_services_count"] >= 4
    service_ids = [s["service_id"] for s in data["active_services"]]
    assert "cleanweb-studio" in service_ids
    assert "eudr-compliance" in service_ids
    assert "security-gate" in service_ids
    assert "minerals-oracle" in service_ids
    print("[PASS] A.GRID Universal Service Registry verified!")

def test_agrid_clearing_and_accounting_journal():
    payload = {
        "event_id": "evt_integration_001",
        "source_service": "cleanweb-studio",
        "caller_agent_id": "0x71C9482938472938472938472938472938472938",
        "operation": "/api/v1/clean-web",
        "amount_usdc": 0.001,
        "chain": "polygon"
    }
    res = client.post("/api/v1/grid/clearing/event", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "CLEARED"
    assert data["amount_usdc"] == 0.001
    assert "journal_entries" in data
    assert len(data["journal_entries"]) > 0
    print(f"[PASS] A.GRID Central Clearing: {data['summary']}")
    for j in data["journal_entries"]:
        print(f"       -> [계정] {j['account_title']} | 차변: {j['debit']:,} | 대변: {j['credit']:,} | {j['description']}")

def test_agrid_a2a_delegation_clearing():
    # Scenario: EUDR delegates PDF clean to CleanWeb (0.005 USDC)
    payload = {
        "event_id": "evt_a2a_002",
        "source_service": "eudr-compliance",
        "caller_agent_id": "eudr_agent_core",
        "operation": "/api/v1/clean-pdf",
        "amount_usdc": 0.005,
        "chain": "base",
        "is_a2a_delegation": True,
        "target_service": "cleanweb-studio"
    }
    res = client.post("/api/v1/grid/clearing/event", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "CLEARED"
    titles = [j["account_title"] for j in data["journal_entries"]]
    assert any("외주용역비" in t for t in titles)
    print(f"[PASS] A2A Delegation Clearing verified: {data['summary']}")

def test_agrid_treasury_summary():
    res = client.get("/api/v1/grid/treasury/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_treasury_usdc"] > 0
    assert "polygon" in data["chain_balances_usdc"]
    assert "base" in data["chain_balances_usdc"]
    assert "arbitrum" in data["chain_balances_usdc"]
    print(f"[PASS] Corporate Treasury Summary: Total ${data['total_treasury_usdc']:,.2f} USDC (₩{data['total_treasury_krw']:,})")

def test_agrid_legal_notarization():
    payload = {
        "document_title": "EUDR Supply Chain Deforestation Statement",
        "document_text": "Supplier warrants that all products are sourced from plots free from deforestation after Dec 31, 2020. No toxic IP forfeiture is imposed.",
        "service_id": "eudr-compliance",
        "requester_agent_id": "0xAgentTrader007"
    }
    res = client.post("/api/v1/grid/legal/notarize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "legal_verdict" in data
    print(f"[PASS] Legal Notarization Verdict: {data['legal_verdict']} (Risk Score: {data['risk_score']})")

if __name__ == "__main__":
    print("=== RUNNING A.GRID CENTRAL HUB INTEGRATION TESTS ===")
    test_agrid_service_registry()
    test_agrid_clearing_and_accounting_journal()
    test_agrid_a2a_delegation_clearing()
    test_agrid_treasury_summary()
    test_agrid_legal_notarization()
    print("\nALL 5 CENTRAL HUB INTEGRATION TESTS PASSED 100%!")
