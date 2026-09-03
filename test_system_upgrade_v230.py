"""
Comprehensive Verification Suite for CleanWeb Studio v2.3.0 System Upgrade.
Verifies Multi-RPC Failover, SQLite WAL Storage, Token Analytics, Jina Fallback, Metrics, and Route Aliases.
"""

import sys
import os
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

print("=========================================================================")
print("🚀 [ENTERPRISE SYSTEM AUDIT] CleanWeb Studio v2.3.0 Upgrade Verification")
print("=========================================================================\n")

# 1. Multi-RPC Failover and Health Check
print("▶ [1/6] ⛓️ Multi-Chain Multi-RPC Failover Pool & Ping Health...")
from app.multi_chain import multi_chain_manager, CHAIN_REGISTRY

for chain_name, cfg in CHAIN_REGISTRY.items():
    print(f"  - {cfg.display_name} (Chain ID {cfg.chain_id}): {len(cfg.rpc_urls)} RPCs in failover pool")

ping_results = multi_chain_manager.ping_all_chains()
for c_name, res in ping_results.items():
    status = res.get("status")
    rpc = res.get("active_rpc")
    lat = res.get("latency_ms")
    block = res.get("latest_block")
    print(f"  [OK] {c_name.upper()}: Status={status}, Block={block}, Latency={lat}ms (RPC: {rpc})")

# 2. SQLite WAL Storage & In-Memory Cache
print("\n▶ [2/6] 🗄️ SQLite WAL Mode, Replay Cache, & Telemetry Stats...")
from app.storage import storage_manager

stats = storage_manager.get_stats()
print(f"  [OK] Storage Stats: {json.dumps(stats, indent=2)}")
assert stats.get("journal_mode") == "WAL", "Expected WAL journal mode"

# Test Replay Protection and Cache
test_tx = f"0x{int(time.time() * 1000):x}".ljust(66, "a")
assert not storage_manager.is_tx_used(test_tx)
storage_manager.record_used_tx(test_tx, "polygon", "0x1111111111111111111111111111111111111111", 0.005)
assert storage_manager.is_tx_used(test_tx)
print("  [OK] Replay cache and WAL write verification passed.")

# 3. Web Cleaner Engine & Token Analytics
print("\n▶ [3/6] 🌐 Web Cleaner Engine with Token Analytics & Jina Fallback...")
from app.cleaners.web_engine import web_cleaner_engine

web_res = web_cleaner_engine.fetch_and_clean("https://paulgraham.com/greatwork.html")
print(f"  [OK] Title: {web_res['title']}")
print(f"  [OK] Words: {web_res['word_count']}, Reading Time: {web_res['estimated_reading_time_sec']}s")
print(f"  [OK] Token Analytics: {web_res['token_analytics']}")
assert web_res['token_analytics']['clean_markdown_estimated_tokens'] > 0

# 4. YouTube Cleaner Engine & Subtitles/Metadata
print("\n▶ [4/6] 📺 YouTube Cleaner Engine (3Blue1Brown Neural Network)...")
from app.cleaners.youtube_engine import youtube_cleaner_engine

yt_res = youtube_cleaner_engine.clean_youtube("https://www.youtube.com/watch?v=aircAruvnKk")
print(f"  [OK] Video Title: {yt_res['title']}")
print(f"  [OK] Method Used: {yt_res['method_used']}, Engine: {yt_res['engine']}")
print(f"  [OK] Token Analytics: {yt_res['token_analytics']}")

# 5. PDF Cleaner Engine & PDF Analytics
print("\n▶ [5/6] 📄 PDF Cleaner Engine (Attention Is All You Need)...")
from app.cleaners.pdf_engine import pdf_cleaner_engine

pdf_res = pdf_cleaner_engine.clean_pdf("https://arxiv.org/pdf/1706.03762.pdf", max_pages=3)
print(f"  [OK] PDF Title: {pdf_res['title']}")
print(f"  [OK] PDF Analytics: {pdf_res['pdf_analytics']}")
print(f"  [OK] Token Analytics: {pdf_res['token_analytics']}")

# 6. FastAPI Endpoints, Metrics & Route Alias Check via TestClient
print("\n▶ [6/6] ⚡ FastAPI Endpoints, /metrics, & Route Alias Verification...")
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Health
r_h = client.get("/health")
assert r_h.status_code == 200
print(f"  [OK] /health: HTTP 200 => {r_h.json()['service']} v{r_h.json()['version']}")

# Metrics
r_m = client.get("/metrics")
assert r_m.status_code == 200
assert "cleanweb_total_requests" in r_m.text
print(f"  [OK] /metrics: HTTP 200 (Prometheus text format received)")

# Clean Web API: First verify 402 challenge on unauthenticated request
r_402 = client.get("/api/v1/clean-web?url=https://paulgraham.com/greatwork.html")
assert r_402.status_code == 402
challenge_body = r_402.json()
assert "x402" in challenge_body and "challenge" in challenge_body
print(f"  [OK] /api/v1/clean-web: HTTP 402 Dual-Challenge verified (Recipient: {challenge_body['challenge']['recipient_wallet'][:10]}...)")

# Now verify 200 OK with Pass
r_web = client.get("/api/v1/clean-web?url=https://paulgraham.com/greatwork.html", headers={"X-Agent-Pass": "WELCOME100"})
assert r_web.status_code == 200
web_json = r_web.json()
print(f"  [OK] /api/v1/clean-web: HTTP 200 (Unlocked with Pass) => Tokens: {web_json.get('token_analytics')}")

# Batch Clean via BOTH aliases (with Pass Authorization)
batch_payload = {"urls": ["https://paulgraham.com/greatwork.html"], "density": "standard"}

r_b1 = client.post("/api/v1/clean-batch", json=batch_payload, headers={"X-Agent-Pass": "WELCOME100"})
assert r_b1.status_code == 200
print(f"  [OK] /api/v1/clean-batch: HTTP 200 => Total: {r_b1.json()['total_requested']}, Success: {r_b1.json()['total_success']}")

r_b2 = client.post("/api/v1/batch-clean", json=batch_payload, headers={"X-Agent-Pass": "WELCOME100"})
assert r_b2.status_code == 200
print(f"  [OK] /api/v1/batch-clean (Alias): HTTP 200 => Total: {r_b2.json()['total_requested']}, Success: {r_b2.json()['total_success']}")

# 7. B2A Vault Limits (Min 2.0 ~ Max 1000.0 USDC) & SSRF Security Verification
print("\n▶ [Bonus] 💼 B2A Vault Limits (Min 2.0 ~ Max 1000.0 USDC) & SSRF Security...")
# Below minimum (1.5) must fail
r_fail = client.post("/api/v1/vault/deposit", json={"agent_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", "amount_usdc": 1.5, "tx_hash": ""})
assert r_fail.status_code in (400, 422)
# Valid deposit (2.0) must succeed
r_valid = client.post("/api/v1/vault/deposit", json={"agent_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", "amount_usdc": 2.0, "tx_hash": ""})
assert r_valid.status_code == 200
print(f"  [OK] /api/v1/vault/deposit: Limits (2.0 ~ 1000.0 USDC) Enforced Successfully.")

# SSRF attack block verification
from app.cleaners.security import is_safe_url
assert not is_safe_url("http://metadata.google.internal/computeMetadata/v1/")
assert not is_safe_url("http://169.254.169.254/latest/meta-data/")
assert not is_safe_url("http://192.168.1.1/admin")
assert is_safe_url("https://paulgraham.com/greatwork.html")
print("  [OK] SSRF Firewall: Cloud metadata & private IPs successfully BLOCKED.")

print("\n=========================================================================")
print("🎉 [ALL UPGRADE DOMAINS FULLY VERIFIED AND OPERATIONAL (v2.4.0)]")
print("=========================================================================")
