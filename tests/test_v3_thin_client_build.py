import pathlib
import tomllib

import mcp_server
import thin_mcp_proxy


def test_thin_gateway_headers_mapping():
    h_vault = thin_mcp_proxy.build_thin_gateway_headers(
        "clean_web_content",
        {"url": "https://example.com"},
        auth_token_or_tx="vault_key_test_123",
        request_id="req-v3-001",
    )
    assert h_vault["X-Vault-Key"] == "vault_key_test_123"
    assert h_vault["X-Request-ID"] == "req-v3-001"
    assert h_vault["X-Idempotency-Key"].startswith("thin_req-v3-001_")

    h_tx = thin_mcp_proxy.build_thin_gateway_headers(
        "clean_pdf_research",
        {"url": "https://example.com/a.pdf"},
        auth_token_or_tx="0x" + ("a" * 64),
        idempotency_key="custom-idem-99",
    )
    assert h_tx["X-Payment-Tx"] == "0x" + ("a" * 64)
    assert h_tx["X-Idempotency-Key"] == "custom-idem-99"


def test_mcp_server_thin_client_mode_forwards_to_remote_gateway(monkeypatch):
    monkeypatch.setenv("X402_THIN_CLIENT_MODE", "1")
    monkeypatch.setenv("X402_GATEWAY_URL", "https://gateway.cleanweb.test")

    # Ensure server-side app/ engines are absent/unused in Thin Client mode
    monkeypatch.setattr(mcp_server, "web_cleaner_engine", None)
    monkeypatch.setattr(mcp_server, "pdf_cleaner_engine", None)

    captured = []

    class FakeResp:
        status_code = 200

        def json(self):
            return {
                "jsonrpc": "2.0",
                "id": "req-1",
                "result": {
                    "content": [{"type": "text", "text": "✅ [REMOTE GATEWAY CLEAN SUCCESS]\n# Remote Title"}]
                },
            }

    def fake_post(url, json=None, headers=None, timeout=None):
        captured.append((url, json, headers))
        return FakeResp()

    monkeypatch.setattr(thin_mcp_proxy.requests, "post", fake_post)

    out_web = mcp_server.clean_web_content(
        url="https://news.ycombinator.com",
        auth_token_or_tx="vault_key_thin_01",
        request_id="lc-run-555",
        idempotency_key="lc-idem-555",
    )
    assert "REMOTE GATEWAY CLEAN SUCCESS" in out_web
    assert len(captured) == 1
    url, payload, headers = captured[0]
    assert url == "https://gateway.cleanweb.test/api/v1/mcp"
    assert payload["method"] == "tools/call"
    assert payload["params"]["name"] == "clean_web_content"
    assert headers["X-Vault-Key"] == "vault_key_thin_01"
    assert headers["X-Request-ID"] == "lc-run-555"
    assert headers["X-Idempotency-Key"] == "lc-idem-555"

    out_pdf = mcp_server.clean_pdf_research(
        url="https://arxiv.org/pdf/1706.03762.pdf",
        max_pages=5,
        auth_token_or_tx="vault_key_thin_01",
    )
    assert "REMOTE GATEWAY CLEAN SUCCESS" in out_pdf
    assert len(captured) == 2
    assert captured[1][1]["params"]["name"] == "clean_pdf_research"

    # Verify non-web/pdf MCP tools also forward cleanly via _thin_aware_mcp_tool when server objects are None
    monkeypatch.setattr(mcp_server, "storage_manager", None)
    monkeypatch.setattr(mcp_server, "multi_chain_manager", None)
    out_search = mcp_server.search_web_quick(query="x402 micropayments", auth_token_or_tx="vault_key_thin_01")
    assert "REMOTE GATEWAY CLEAN SUCCESS" in out_search
    assert len(captured) == 3
    assert captured[2][1]["params"]["name"] == "search_web_quick"
    assert captured[2][1]["params"]["arguments"]["query"] == "x402 micropayments"


def test_pyproject_v3_manifest_excludes_server_core_and_heavy_deps():
    root = pathlib.Path(__file__).resolve().parent.parent
    v3_toml = root / "pyproject.toml"
    assert v3_toml.exists()

    data = tomllib.loads(v3_toml.read_text(encoding="utf-8"))
    assert tuple(int(p) for p in data["project"]["version"].split(".")[:3]) >= (3, 0, 0)

    setuptools_cfg = data["tool"]["setuptools"]
    assert setuptools_cfg["packages"] == []
    assert "thin_mcp_proxy" in setuptools_cfg["py-modules"]
    assert "main" not in setuptools_cfg["py-modules"]

    deps_joined = " ".join(data["project"]["dependencies"]).lower()
    for heavy_server_dep in ("fastapi", "uvicorn", "beautifulsoup4", "pypdf", "yt-dlp", "youtube-transcript-api"):
        assert heavy_server_dep not in deps_joined


def test_day6_core_separation_rehearsal_without_app_package(monkeypatch):
    """Day 6 Rehearsal: Verifies that every v3.0.0 py-module exists and auto-detects Thin Mode when app/ is absent."""
    import sys

    root = pathlib.Path(__file__).resolve().parent.parent
    v3_toml = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    py_modules = v3_toml["tool"]["setuptools"]["py-modules"]

    for mod_name in py_modules:
        mod_file = root / f"{mod_name}.py"
        assert mod_file.exists(), f"Missing v3.0.0 Thin Client module: {mod_file}"

    # Simulate app.cleaners.web_engine being absent (as in the installed v3.0.0 PyPI wheel)
    monkeypatch.delenv("X402_THIN_CLIENT_MODE", raising=False)
    monkeypatch.setitem(sys.modules, "app.cleaners.web_engine", None)
    assert thin_mcp_proxy.is_thin_client_mode() is True
