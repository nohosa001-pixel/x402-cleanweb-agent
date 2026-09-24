import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_all_api_routes_operational():
    """Google SRE Production Readiness: Verifies that all registered FastAPI routes respond without 500 errors."""
    routes = []
    for r in app.routes:
        if hasattr(r, "path") and hasattr(r, "methods"):
            # Exclude infinite streaming SSE transport routes mounted by MCP
            if r.path.startswith("/mcp-server"):
                continue
            for m in r.methods:
                if m not in ("HEAD", "OPTIONS"):
                    routes.append((m, r.path))

    assert len(routes) >= 35, f"Expected at least 35 routes, got {len(routes)}"

    sample_payloads = {
        "/api/v1/clean-web": {"params": {"url": "https://example.com"}},
        "/api/v1/clean-text": {"params": {"url": "https://example.com"}},
        "/api/v1/clean-youtube": {"params": {"url": "https://www.youtube.com/watch?v=aircAruvnKk"}},
        "/api/v1/clean-pdf": {"params": {"url": "https://raw.githubusercontent.com/mozilla/pdf.js/master/examples/learning/helloworld.pdf"}},
        "/api/v1/clean-batch": {"json": {"urls": ["https://example.com"], "density": "standard"}},
        "/api/v1/batch-clean": {"json": {"urls": ["https://example.com"], "density": "standard"}},
        "/api/v1/map-site": {"params": {"url": "https://example.com"}},
        "/api/v1/search": {"params": {"query": "AI Agents 2026"}},
        "/api/v1/extract-json": {"json": {"url": "https://example.com", "schema_description": "title and description"}},
        "/api/v1/oracle/grounding": {"json": {"query": "Federal Reserve Rate Decision", "max_sources": 1}},
        "/api/v1/oracle/verify": {"json": {"data_hash": "0x482fe666766eeff1aaac00ae74a1b9b7382679e766bd65d3d59018097a7b28ce", "timestamp": 1789639556, "signature": "0x111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111b"}},
        "/api/v1/deep-research": {"params": {"query": "Autonomous Agent Economics", "max_sources": 1}},
        "/api/v1/vault/deposit": {"json": {"agent_address": "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf", "amount_usdc": 2.0, "chain": "polygon", "tx_hash": ""}},
        "/api/v1/vault/balance": {"params": {"identifier": "vault_key_demo_agent_sandbox_2026"}},
        "/api/v1/pass-status": {"params": {"agent_wallet": "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf"}},
        "/api/v1/security/inspect": {"json": {"text": "Hello world inspection", "is_code": False}},
        "/api/v1/legal/terms": {},
        "/api/v1/legal/disclaimer": {},
        "/api/v1/chains": {},
        "/api/v1/pricing": {},
        "/metrics": {},
        "/health": {},
        "/dashboard": {},
        "/.well-known/ap2": {},
        "/.well-known/ap2.json": {},
        "/.well-known/agent.json": {},
        "/.well-known/ai-plugin.json": {},
        "/.well-known/mcp/server-card.json": {},
        "/.well-known/mcp.json": {},
        "/mcp/tools": {},
        "/mcp_tool_spec.json": {},
        "/glama.json": {},
        "/api/v1/agent/capabilities": {},
        "/api/v1/agent/pricing-catalog": {},
        "/api/v1/agent/arbitrage-roi": {"params": {"input_tokens": 50000}},
        "/api/v1/agent/integrations/{framework}": {},
        "/api/v1/clean-web/stream": {"params": {"url": "https://example.com"}},
        "/r/stream/{target_url:path}": {"path_override": "/r/stream/https://example.com"},
        "/r/{target_url:path}": {"path_override": "/r/https://example.com"},
        "/api/v1/clean-embed": {"json": {"url": "https://example.com"}},
        "/api/v1/vault/permit-deposit": {"json": {"owner": "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf", "value_usdc": 2.0, "deadline": 9999999999, "v": 27, "r": "0x1111111111111111111111111111111111111111111111111111111111111111", "s": "0x2222222222222222222222222222222222222222222222222222222222222222"}},
        "/api/v1/treasury/merkle-root": {},
        "/api/v1/treasury/merkle-proof/{tx_hash}": {"path_override": "/api/v1/treasury/merkle-proof/0x0000000000000000000000000000000000000000000000000000000000000000"},
        "/api/v1/mcp/sse-info": {},
    }

    failures = []
    for method, path in routes:
        req_path = path.replace("{framework}", "langchain")
        kwargs = sample_payloads.get(path, sample_payloads.get(req_path, {})).copy()
        if "path_override" in kwargs:
            req_path = kwargs.pop("path_override")
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = "Bearer dev-bypass"

        if method == "GET":
            res = client.get(req_path, headers=headers, **kwargs)
        elif method == "POST":
            res = client.post(req_path, headers=headers, **kwargs)
        else:
            continue

        if res.status_code >= 500:
            failures.append((method, req_path, res.status_code, res.text[:120]))

    assert len(failures) == 0, f"Routes returning 500 server errors: {failures}"
