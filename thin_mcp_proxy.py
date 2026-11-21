"""
x402-cleanweb-agent v3.0.0 Cloud-Native Thin MCP & REST Proxy
=============================================================
Forwards local stdio MCP tool invocations and thin-client SDK requests directly
to the managed x402 CleanWeb Cloud Run Gateway over HTTPS JSON-RPC 2.0.

Ensures:
- Zero local scraping/parsing dependencies (no bs4, pypdf, yt-dlp, fastapi required on client)
- 100% server-side Indirect Prompt Injection & Hidden White-Text PDF sanitization
- Deterministic x402 USDC / Pre-Funded Vault enforcement on every call
- End-to-end X-Request-ID traceability & X-Idempotency-Key retry deduplication
"""

from __future__ import annotations

import hashlib
import os
import secrets
import time
from typing import Any, Dict, Optional

import requests

DEFAULT_GATEWAY_URL = os.getenv(
    "X402_GATEWAY_URL",
    "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app",
)

# Process-local session nonce for the 3-query evaluation trial when no Vault key is configured
_CLIENT_SESSION_NONCE = f"thin_v3_{secrets.token_hex(6)}"


def is_thin_client_mode() -> bool:
    """
    Returns True when running in v3.0.0 Thin Client mode:
    - Explicitly enabled via X402_THIN_CLIENT_MODE=1/true, OR
    - When server-side `app.cleaners` package is absent (e.g. v3.0.0 PyPI thin wheel).
    """
    flag = os.getenv("X402_THIN_CLIENT_MODE", "").strip().lower()
    if flag in ("1", "true", "yes"):
        return True
    if flag in ("0", "false", "no"):
        return False
    try:
        import app.cleaners.web_engine  # noqa: F401
        return False
    except ImportError:
        return True


def build_thin_gateway_headers(
    tool_name: str,
    arguments: Dict[str, Any],
    auth_token_or_tx: Optional[str] = None,
    request_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> Dict[str, str]:
    """Constructs standard x402 + traceability + idempotency headers for the remote gateway."""
    token = (
        auth_token_or_tx
        or arguments.get("auth_token_or_tx")
        or os.getenv("AGENT_VAULT_KEY")
        or os.getenv("X402_AUTH_TOKEN")
    )
    req_id = (
        request_id
        or arguments.get("request_id")
        or f"thin_{secrets.token_hex(8)}"
    )
    target_ref = str(arguments.get("url") or arguments.get("query") or arguments.get("urls") or tool_name)
    digest = hashlib.sha256(f"{tool_name}|{target_ref}".encode("utf-8")).hexdigest()[:12]
    idem_key = (
        idempotency_key
        or arguments.get("idempotency_key")
        or f"thin_{req_id}_{digest}"
    )

    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "x402-cleanweb-thin-client/3.0.0",
        "X-Agent-Nonce": _CLIENT_SESSION_NONCE,
        "X-Request-ID": str(req_id),
        "X-Idempotency-Key": str(idem_key),
    }

    if isinstance(token, str) and token.strip():
        tok = token.strip()
        if tok.startswith("vault_key_") or tok.startswith("sk_") or (tok.startswith("0x") and len(tok) == 42):
            headers["X-Vault-Key"] = tok
            headers["X-Agent-Pass"] = tok
        elif tok.startswith("pass_"):
            headers["X-Agent-Pass"] = tok
        elif tok.startswith("0x") and len(tok) == 66:
            headers["X-Payment-Tx"] = tok
        else:
            headers["X-Vault-Key"] = tok

    return headers


def forward_mcp_tool_to_gateway(
    tool_name: str,
    arguments: Dict[str, Any],
    gateway_url: Optional[str] = None,
    timeout: int = 35,
) -> str:
    """
    Forwards an MCP tool call to the remote Cloud Run Gateway's `POST /api/v1/mcp` JSON-RPC endpoint.
    """
    base = (gateway_url or os.getenv("X402_GATEWAY_URL") or DEFAULT_GATEWAY_URL).rstrip("/")
    endpoint = f"{base}/api/v1/mcp"

    clean_args = {
        k: v
        for k, v in arguments.items()
        if v is not None and not hasattr(v, "default")
    }
    headers = build_thin_gateway_headers(tool_name, clean_args)
    payload = {
        "jsonrpc": "2.0",
        "id": headers["X-Request-ID"],
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": clean_args,
        },
    }

    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            body = resp.json()
            result = body.get("result") or {}
            contents = result.get("content") or []
            if contents and isinstance(contents, list):
                texts = [c.get("text", "") for c in contents if isinstance(c, dict) and c.get("text")]
                if texts:
                    return "\n".join(texts)
            if "error" in body:
                err = body["error"]
                return f"❌ [GATEWAY MCP ERROR]: {err.get('message', err)}"
            return str(result)
        return f"❌ [GATEWAY HTTP {resp.status_code}]: {resp.text[:500]}"
    except Exception as exc:
        return f"❌ [THIN CLIENT GATEWAY ERROR]: Failed to reach {endpoint}: {exc}"
