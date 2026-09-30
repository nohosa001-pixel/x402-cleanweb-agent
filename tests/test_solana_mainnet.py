"""
Test Suite for Solana Mainnet-Beta Integration in CleanWeb Studio.
Verifies Solana RPC connectivity, SPL USDC balance queries, multi-chain treasury aggregation,
HTTP 402 challenge/response with Solana support, and transfer verification logic.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.multi_chain import multi_chain_manager, SupportedChain, CHAIN_REGISTRY
from app.x402_verifier import x402_verifier
from app.schemas import PricingTier
from app.vault_manager import vault_manager, safe_agent_address

client = TestClient(app)


def test_solana_chain_registry_configuration():
    """Validates that Solana Mainnet-Beta is properly registered in CHAIN_REGISTRY."""
    assert SupportedChain.SOLANA.value in CHAIN_REGISTRY
    cfg = CHAIN_REGISTRY["solana"]
    assert cfg.chain_name == "solana"
    assert cfg.chain_id == 101
    assert cfg.display_name == "Solana Mainnet-Beta"
    assert cfg.usdc_address == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    assert cfg.decimals == 6
    assert len(cfg.rpc_urls) >= 1
    assert "https://solscan.io" in cfg.explorer_url


def test_get_chain_config_for_solana():
    """Validates chain configuration resolution by aliases: 'solana', 'sol', and '101'."""
    cfg1 = multi_chain_manager.get_chain_config("solana")
    cfg2 = multi_chain_manager.get_chain_config("sol")
    cfg3 = multi_chain_manager.get_chain_config(101)
    cfg4 = multi_chain_manager.get_chain_config("101")

    assert cfg1.chain_name == "solana"
    assert cfg2.chain_name == "solana"
    assert cfg3.chain_name == "solana"
    assert cfg4.chain_name == "solana"


def test_live_solana_rpc_ping():
    """Tests live ping to Solana Mainnet RPC node failover pool."""
    res = multi_chain_manager.ping_solana()
    assert res["chain_id"] == 101
    assert res["display_name"] == "Solana Mainnet-Beta"
    # Either healthy with latest slot or gracefully handles degraded network
    if res["status"] == "healthy":
        assert res["latest_block"] > 0
        assert res["latency_ms"] > 0
        assert "active_rpc" in res


def test_live_solana_balances_query():
    """Tests live query of SOL and SPL USDC balances for Solana treasury."""
    res = multi_chain_manager.get_chain_balances("solana")
    assert res["chain"] == "solana"
    assert res["chain_id"] == 101
    assert res["native_symbol"] == "SOL"
    assert isinstance(res["usdc_balance"], (int, float))
    assert isinstance(res["native_balance"], (int, float))
    assert res["usdc_balance"] >= 0.0


def test_multi_chain_treasury_summary_includes_solana():
    """Validates that get_multi_chain_treasury_summary aggregates all 4 chains including Solana."""
    summary = multi_chain_manager.get_multi_chain_treasury_summary()
    assert "networks" in summary
    networks = summary["networks"]

    assert "polygon" in networks
    assert "base" in networks
    assert "arbitrum" in networks
    assert "solana" in networks

    assert "solana_treasury_wallet" in summary
    assert summary["solana_treasury_wallet"] == multi_chain_manager.solana_recipient
    assert summary["total_usdc_accumulated"] >= 0.0


def test_treasury_status_api_endpoint():
    """Tests that GET /api/v1/treasury/status returns all 4 supported networks."""
    resp = client.get("/api/v1/treasury/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    supported_nets = data.get("supported_networks", [])
    assert any("Solana" in net for net in supported_nets)
    assert any("Polygon" in net for net in supported_nets)
    assert any("Base" in net for net in supported_nets)
    assert any("Arbitrum" in net for net in supported_nets)

    balances = data.get("onchain_balances", {}).get("networks", {})
    assert "solana" in balances


def test_x402_challenge_contains_solana():
    """Verifies that the HTTP 402 challenge includes Solana payment options."""
    challenge = x402_verifier.build_402_challenge(tier=PricingTier.LIGHT)
    ch_dict = challenge.model_dump()

    # Check payment methods
    assert "USDC_ONCHAIN_SOLANA" in ch_dict["payment_methods_accepted"]

    # Check networks
    sol_net = next((n for n in ch_dict["networks"] if n["chain"] == "solana"), None)
    assert sol_net is not None
    assert sol_net["chain_id"] == 101
    assert sol_net["token"] == "USDC"
    assert sol_net["address"] == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    assert sol_net["recipient"] == multi_chain_manager.solana_recipient


def test_x402_response_contains_solana_accepts_and_prebuilt():
    """Verifies that the 402 JSON response includes Solana under accepts and prebuilt_transactions."""
    resp = x402_verifier.build_402_response(tier=PricingTier.LIGHT)
    assert resp.status_code == 402
    
    import json
    body = json.loads(resp.body.decode("utf-8"))

    # Check WWW-Authenticate header
    www_auth = resp.headers.get("www-authenticate", "")
    assert "Solana" in www_auth

    # Check X-Payment-Networks header
    net_hdr = resp.headers.get("x-payment-networks", "")
    assert "Solana(SPL)" in net_hdr

    # Check accepts
    accepts = body.get("accepts", [])
    sol_accept = next((a for a in accepts if a.get("network") == "solana"), None)
    assert sol_accept is not None
    assert sol_accept["chain_id"] == 101
    assert sol_accept["payTo"] == multi_chain_manager.solana_recipient

    # Check prebuilt_transactions
    prebuilt = body.get("prebuilt_transactions", {})
    assert "solana" in prebuilt
    assert prebuilt["solana"]["mint"] == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def test_safe_agent_address():
    """Tests safe_agent_address helper for EVM checksum and Solana Base58 addresses."""
    # EVM address (lowercase -> checksum)
    evm_addr = "0xa185b43fdd19619f99952aaed6eabf1029bf36a1"
    assert safe_agent_address(evm_addr) == "0xA185B43fDD19619f99952AAed6eabf1029bF36a1"

    # Solana Base58 address (should remain unchanged)
    sol_addr = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
    assert safe_agent_address(sol_addr) == sol_addr


def test_verify_solana_usdc_transfer_mock_success():
    """Tests verify_solana_usdc_transfer with mocked RPC getTransaction response."""
    fake_sig = "5Ver7GJq9Er4d7uCpxvJcWnS2zR9Yy38vKj451881972AbCdEfGhIjKlMnOpQrStUvWxYz1234567890abcdef"
    mock_recipient = multi_chain_manager.solana_recipient

    mock_tx_data = {
        "slot": 451881980,
        "meta": {
            "err": None,
            "preTokenBalances": [
                {
                    "accountIndex": 1,
                    "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    "owner": mock_recipient,
                    "uiTokenAmount": {"uiAmount": 10.0}
                }
            ],
            "postTokenBalances": [
                {
                    "accountIndex": 1,
                    "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    "owner": mock_recipient,
                    "uiTokenAmount": {"uiAmount": 10.05}  # 0.05 USDC transferred
                }
            ],
            "innerInstructions": []
        },
        "transaction": {
            "message": {
                "accountKeys": [
                    {"pubkey": "SenderWallet11111111111111111111111111111111"}
                ],
                "instructions": []
            }
        }
    }

    with patch.object(multi_chain_manager, "_solana_rpc_call", return_value=mock_tx_data):
        is_valid, msg, details = multi_chain_manager.verify_solana_usdc_transfer(
            tx_signature=fake_sig,
            expected_recipient=mock_recipient,
            min_amount_usdc=0.01
        )

        assert is_valid is True
        assert "successfully" in msg
        assert details["chain"] == "solana"
        assert details["chain_id"] == 101
        assert details["amount_usdc"] == 0.05
        assert details["recipient"] == mock_recipient
        assert details["payer"] == "SenderWallet11111111111111111111111111111111"
        assert details["block_number"] == 451881980


def test_solana_dedicated_idls_verification():
    """Learned from security-gate-x402: Verify that all 3 EVM contracts have dedicated Solana Anchor IDLs."""
    import os, json
    from pathlib import Path
    
    base_dir = Path(__file__).parent.parent
    idl_dir = base_dir / "contracts" / "solana" / "idl"
    assert idl_dir.exists(), "contracts/solana/idl directory must exist"

    expected_files = [
        "AgentPaymentVault.json",
        "CleanWebOracleConsumer.json",
        "CleanWebOracleVerifier.json"
    ]

    for fname in expected_files:
        fpath = idl_dir / fname
        assert fpath.exists(), f"Missing IDL file: {fname}"
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("version") == "0.1.0"
        assert "name" in data
        assert "metadata" in data and "address" in data["metadata"]
        assert len(data.get("instructions", [])) >= 1

