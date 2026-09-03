"""
Tests for Treasury Status API, Multi-Chain Balance Aggregator, and Ping Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.multi_chain import multi_chain_manager

client = TestClient(app)


def test_ping_keepalive():
    resp = client.get("/api/v1/ping")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ping"] == "pong"
    assert "timestamp" in data


def test_treasury_status_endpoint():
    resp = client.get("/api/v1/treasury/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "treasury_wallet" in data
    assert "total_usdc_onchain" in data
    assert "onchain_balances" in data
    assert "db_stats" in data
    assert len(data["supported_networks"]) == 3


def test_multi_chain_balances_structure():
    summary = multi_chain_manager.get_multi_chain_treasury_summary()
    assert "treasury_wallet" in summary
    assert "total_usdc_accumulated" in summary
    assert "networks" in summary
    assert "polygon" in summary["networks"]
    assert "base" in summary["networks"]
    assert "arbitrum" in summary["networks"]
