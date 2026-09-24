"""
Comprehensive Integration & Verification Suite for Modernization Upgrades:
1. Remote MCP SSE Transport (/mcp-server/sse, /api/v1/mcp/sse-info)
2. Real-Time Chunk Streaming (/api/v1/clean-web/stream, /r/stream/{url})
3. RAG Dense Vector Embedding Pipeline (/api/v1/clean-embed)
4. Gasless EIP-2612 / EIP-3009 Permit Vault Deposit (/api/v1/vault/permit-deposit)
5. Cryptographic Merkle Tree Batch Anchoring & Ledger Proofs (/api/v1/treasury/merkle-root, /api/v1/treasury/merkle-proof/{tx})
"""

import os
import time
import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data

from app.main import app
from app.storage import storage_manager
from app.vault_manager import vault_manager
from app.merkle_engine import merkle_engine, compute_tx_leaf


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# 1. Remote MCP SSE Transport Tests
# =========================================================================
def test_mcp_sse_info_endpoint(client):
    """Verifies MCP SSE discovery endpoint returns protocol details."""
    res = client.get("/api/v1/mcp/sse-info")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert data["transport"] == "Server-Sent Events (SSE)"
    assert data["sse_endpoint"] == "/mcp-server/sse"
    assert data["messages_endpoint"] == "/mcp-server/messages"


def test_mcp_sse_mount_exists(client):
    """Verifies that /mcp-server/sse and /mcp-server/messages are mounted on FastAPI."""
    route_paths = [getattr(r, "path", None) for r in app.routes]
    assert "/mcp-server" in route_paths


# =========================================================================
# 2. Real-Time Chunk Streaming Tests
# =========================================================================
import uuid


def test_clean_web_stream_sse(client):
    """Verifies /api/v1/clean-web/stream returns SSE event stream with metadata, chunk, analytics, done."""
    headers = {"X-Agent-Nonce": f"test-stream-nonce-{uuid.uuid4().hex}"}
    url = "https://news.ycombinator.com"

    mock_clean_data = {
        "url": url,
        "title": "Hacker News",
        "markdown_content": "# Hacker News\n\nFirst paragraph content here.\n\nSecond paragraph content here.",
        "word_count": 12,
        "estimated_reading_time_sec": 3,
        "token_analytics": {
            "raw_html_estimated_tokens": 100,
            "clean_markdown_estimated_tokens": 20,
            "token_reduction_percent": 80.0,
            "saved_tokens": 80
        }
    }

    with patch("app.main.web_cleaner_engine.fetch_and_clean", return_value=mock_clean_data):
        res = client.get(f"/api/v1/clean-web/stream?url={url}", headers=headers)
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("content-type", "")
        content = res.text
        assert "event: metadata" in content
        assert "event: chunk" in content
        assert "event: analytics" in content
        assert "event: done" in content
        assert "[DONE]" in content


def test_agent_reader_stream_proxy(client):
    """Verifies /r/stream/{target_url} returns chunked markdown stream."""
    headers = {"X-Agent-Nonce": f"test-stream-proxy-{uuid.uuid4().hex}"}
    target_url = "https://example.com/test-stream"

    mock_clean_data = {
        "url": target_url,
        "title": "Example Stream",
        "markdown_content": "# Stream Header\n\nParagraph 1.\n\nParagraph 2.",
        "word_count": 6,
        "token_analytics": {"savings_percentage": "85%"}
    }

    with patch("app.main.web_cleaner_engine.fetch_and_clean", return_value=mock_clean_data):
        res = client.get(f"/r/stream/{target_url}", headers=headers)
        assert res.status_code == 200
        assert "text/markdown" in res.headers.get("content-type", "")
        assert "Stream Header" in res.text
        assert "Paragraph 1." in res.text


# =========================================================================
# 3. RAG Dense Vector Embedding Pipeline Tests
# =========================================================================
def test_clean_embed_endpoint(client):
    """Verifies /api/v1/clean-embed scrapes, chunks, and returns 768-dim vector embeddings."""
    headers = {"X-Agent-Nonce": f"test-embed-nonce-{uuid.uuid4().hex}"}
    body = {
        "url": "https://example.com/rag-doc",
        "chunk_size": 300,
        "chunk_overlap": 30,
        "density": "standard"
    }

    mock_clean_data = {
        "url": body["url"],
        "title": "RAG Document",
        "markdown_content": "# Section 1\n\nInformation retrieval is vital for AI agents.\n\n# Section 2\n\nDense vector representations enable semantic search.",
        "word_count": 18,
        "estimated_reading_time_sec": 5,
        "token_analytics": {
            "raw_html_estimated_tokens": 120,
            "clean_markdown_estimated_tokens": 30,
            "token_reduction_percent": 75.0,
            "saved_tokens": 90
        }
    }

    with patch("app.cleaners.embed_engine.web_cleaner_engine.fetch_and_clean", return_value=mock_clean_data):
        res = client.post("/api/v1/clean-embed", json=body, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["url"] == body["url"]
        assert data["dimension"] == 768
        assert data["total_chunks"] >= 1
        assert len(data["chunks"]) >= 1
        first_chunk = data["chunks"][0]
        assert "text" in first_chunk
        assert "embedding" in first_chunk
        assert len(first_chunk["embedding"]) == 768
        assert data["payment_receipt"] is not None


# =========================================================================
# 4. Gasless EIP-2612 / EIP-3009 Permit Vault Deposit Tests
# =========================================================================
def test_permit_vault_deposit_and_replay_protection(client):
    """
    Tests off-chain gasless permit deposit flow:
    Agent signs EIP-2612 typed message -> POST /api/v1/vault/permit-deposit -> vault credited -> replay blocked.
    """
    agent = Account.create()
    spender = "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf"
    token_contract = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"  # Polygon USDC
    amount_usdc = 5.0
    value_raw = int(round(amount_usdc * 1_000_000))
    deadline = int(time.time()) + 7200

    structured_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Permit": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
            ],
        },
        "primaryType": "Permit",
        "domain": {
            "name": "USD Coin",
            "version": "2",
            "chainId": 137,
            "verifyingContract": Web3.to_checksum_address(token_contract),
        },
        "message": {
            "owner": agent.address,
            "spender": Web3.to_checksum_address(spender),
            "value": value_raw,
            "nonce": 0,
            "deadline": deadline,
        },
    }

    encoded = encode_typed_data(full_message=structured_data)
    signed = agent.sign_message(encoded)

    permit_payload = {
        "owner": agent.address,
        "spender": spender,
        "value_usdc": amount_usdc,
        "deadline": deadline,
        "v": signed.v,
        "r": hex(signed.r),
        "s": hex(signed.s),
        "chain": "polygon",
        "nonce": 0
    }

    # 1. First deposit must succeed
    res = client.post("/api/v1/vault/permit-deposit", json=permit_payload)
    assert res.status_code == 200
    vault_info = res.json()
    assert vault_info["agent_address"].lower() == agent.address.lower()
    assert vault_info["balance_usdc"] >= 5.0
    assert "session_key" in vault_info
    assert vault_info["session_key"].startswith("vault_key_")

    # 2. Replay with identical signature must be rejected with HTTP 400
    res_replay = client.post("/api/v1/vault/permit-deposit", json=permit_payload)
    assert res_replay.status_code == 400
    assert "replay detected" in res_replay.json()["detail"].lower()


# =========================================================================
# 5. Cryptographic Merkle Root & Inclusion Proof Tests
# =========================================================================
def test_merkle_root_and_proof_lifecycle(client):
    """
    Tests ledger Merkle tree creation, root retrieval, and audit proof verification.
    """
    # 1. Seed a unique test transaction into SQLite storage
    test_tx_hash = f"0xtest_upgrade_merkle_tx_{int(time.time())}"
    agent_addr = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    storage_manager.record_used_tx(
        tx_hash=test_tx_hash,
        chain="polygon",
        payer=agent_addr,
        amount_usdc=2.50
    )

    # 2. Retrieve global Merkle Root
    root_res = client.get("/api/v1/treasury/merkle-root")
    assert root_res.status_code == 200
    root_data = root_res.json()
    assert root_data["status"] == "success"
    assert root_data["merkle_root"].startswith("0x")
    assert root_data["total_leaves"] >= 1
    assert root_data["anchored_tx_count"] >= 1

    # 3. Retrieve Merkle Proof for the seeded transaction
    proof_res = client.get(f"/api/v1/treasury/merkle-proof/{test_tx_hash}")
    assert proof_res.status_code == 200
    proof_data = proof_res.json()
    assert proof_data["status"] == "success"
    assert proof_data["tx_hash"] == test_tx_hash.lower()
    assert proof_data["leaf"].startswith("0x")
    assert proof_data["merkle_root"] == root_data["merkle_root"]
    assert proof_data["verified"] is True

    # 4. Independent local verification using MerkleTreeEngine
    leaf = proof_data["leaf"]
    proof_items = proof_data["proof"]
    merkle_root = proof_data["merkle_root"]
    assert merkle_engine.verify_proof(leaf, proof_items, merkle_root) is True
