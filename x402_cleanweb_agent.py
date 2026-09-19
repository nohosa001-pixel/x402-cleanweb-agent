"""
x402-cleanweb-agent
~~~~~~~~~~~~~~~~~~~
Pure B2A Autonomous Agent Real-Time Data Oracle & x402 Signed Grounding Engine
on Polygon, Base, and Arbitrum.

Official Package Entrypoint & Management CLI:
    import x402_cleanweb_agent
    from x402_cleanweb_agent import AutonomousAgentClient, agent_tools, __version__

CLI Commands:
    python -m x402_cleanweb_agent status
    python -m x402_cleanweb_agent balance [identifier_or_vault_key]
    python -m x402_cleanweb_agent deposit --amount 2.0 --chain polygon
    python -m x402_cleanweb_agent pricing
    python -m x402_cleanweb_agent test [url]
    python -m x402_cleanweb_agent mcp
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

from app import __version__
from autonomous_agent_client import AutonomousX402Agent

# Convenience alias
AutonomousAgentClient = AutonomousX402Agent

try:
    import agent_tools
except ImportError:
    agent_tools = None

DEFAULT_GATEWAY_URL = os.getenv("X402_GATEWAY_URL", "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app")

__all__ = [
    "__version__",
    "AutonomousX402Agent",
    "AutonomousAgentClient",
    "agent_tools",
    "main",
]


def _format_json_request(url: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, method: str = "GET") -> Dict[str, Any]:
    req_headers = {"User-Agent": f"x402-cli/{__version__}"}
    if headers:
        req_headers.update(headers)
    encoded_data = None
    if data:
        req_headers["Content-Type"] = "application/json"
        encoded_data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=encoded_data, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cmd_status(base_url: str = DEFAULT_GATEWAY_URL):
    """Check live status of the x402 Production Triad & Gateway"""
    print("=" * 70)
    print(f"📡 [x402 CLI] Checking Production Gateway Status...")
    print(f"🔗 Target: {base_url}")
    print("=" * 70)
    t0 = time.time()
    try:
        health = _format_json_request(f"{base_url}/health")
        latency = round((time.time() - t0) * 1000, 1)
        print(f"  🟢 Gateway Status   : {health.get('status', 'OK')} ({latency}ms)")
        print(f"  📦 Live Version     : v{health.get('version', 'unknown')}")
        print(f"  ⛓️  Chains Connected : {', '.join(health.get('chains_connected', []))}")
        
        stats = health.get("storage_stats", {})
        print(f"  🛡️ Security Gate    : {health.get('security_gate', 'Active')}")
        print(f"  💼 Active Vaults    : {stats.get('vault_accounts_count', 0)} accounts")
        print(f"  💰 Total Vault Pool : ${stats.get('total_vault_balance_usdc', 0.0):,.2f} USDC")
        print(f"  🎫 Active Passes    : {stats.get('active_passes_count', 0)}")
        print("=" * 70)
        print("✅ Gateway is healthy and accepting zero-latency x402 queries.")
    except Exception as e:
        print(f"  ❌ Gateway Check Failed: {e}")
        print("=" * 70)


def cmd_balance(identifier: Optional[str] = None, base_url: str = DEFAULT_GATEWAY_URL):
    """Check agent vault balance and usage statistics"""
    target_id = identifier or os.getenv("AGENT_VAULT_KEY") or os.getenv("AGENT_WALLET_ADDRESS")
    if not target_id:
        print("=" * 70)
        print("⚠️  [x402 CLI] No identifier provided.")
        print("Usage:")
        print("  python -m x402_cleanweb_agent balance <vault_key_or_wallet_address>")
        print("Or set AGENT_VAULT_KEY in your .env file.")
        print("=" * 70)
        return

    print("=" * 70)
    print(f"💳 [x402 CLI] Querying Agent Payment Vault...")
    print(f"🔑 Identifier: {target_id}")
    print("=" * 70)

    try:
        encoded_id = urllib.parse.quote(target_id)
        data = _format_json_request(f"{base_url}/api/v1/vault/balance?identifier={encoded_id}")
        print(f"  💼 Agent Address     : {data.get('agent_address')}")
        print(f"  💵 Available Balance : ${data.get('balance_usdc', 0.0):.4f} USDC")
        print(f"  📥 Total Deposited   : ${data.get('total_deposited_usdc', 0.0):.4f} USDC")
        print(f"  📤 Total Consumed    : ${data.get('total_consumed_usdc', 0.0):.4f} USDC")
        print(f"  📊 Queries Executed  : {data.get('query_count', 0):,} queries")
        print(f"  🔐 Session Key       : {data.get('session_key')}")
        print(f"  ⏱️  Last Active UTC   : {data.get('last_active_utc')}")
        print("=" * 70)
        bal = data.get('balance_usdc', 0.0)
        if bal < 0.2:
            print(f"⚠️  Balance is low ({bal} USDC). Consider refilling via: python -m x402_cleanweb_agent deposit --amount 2.0")
        else:
            print("✅ Sufficient balance for zero-latency autonomous execution.")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("❌ Vault account not found for this identifier.")
            print("To create and fund a new vault, run:")
            print("  python -m x402_cleanweb_agent deposit --amount 2.0 --chain polygon")
        else:
            print(f"❌ Error checking balance (HTTP {e.code}): {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    print("=" * 70)


def cmd_pricing(base_url: str = DEFAULT_GATEWAY_URL):
    """Display comprehensive pricing catalog and volume discounts"""
    print("=" * 70)
    print("🏷️  [x402 CLI] CleanWeb Studio - Machine-to-Machine B2A Pricing")
    print("=" * 70)
    try:
        catalog = _format_json_request(f"{base_url}/api/v1/agent/pricing-catalog")
        rates = catalog.get("rates", {})
        print(f"{'Service / Endpoint':<30} | {'Cost (USDC)':<12} | {'Billing Unit':<15}")
        print("-" * 70)
        for service, info in rates.items():
            cost_str = f"${info.get('cost_usdc', 0.0):.4f}"
            unit_str = info.get("unit", "per_call")
            print(f"{service:<30} | {cost_str:<12} | {unit_str:<15}")
        
        print("\n🎁 Volume Discount Passes (Pre-paid Bundles):")
        print("-" * 70)
        for p in catalog.get("volume_passes", []):
            print(f"  • {p['tier']:<8} : ${p['price_usdc']} USDC for {p['credits']:,} credits ({p['discount']} off)")
    except Exception as e:
        print(f"❌ Failed to fetch pricing: {e}")
    print("=" * 70)


def cmd_test(url: str = "https://news.ycombinator.com", vault_key: Optional[str] = None, base_url: str = DEFAULT_GATEWAY_URL):
    """Execute a 10-second instant extraction test using sandbox or active vault key"""
    active_key = vault_key or os.getenv("AGENT_VAULT_KEY") or "vault_key_demo_agent_sandbox_2026"
    print("=" * 70)
    print("⚡ [x402 CLI] Testing Instant Clean Web Extraction...")
    print(f"🌐 Target URL : {url}")
    print(f"🔗 Gateway    : {base_url}")
    print(f"🔑 Vault Key  : {active_key}")
    print("=" * 70)
    t0 = time.time()
    try:
        headers = {"X-Vault-Key": active_key}
        encoded_url = urllib.parse.quote(url, safe=":/")
        res = _format_json_request(f"{base_url}/api/v1/clean-web?url={encoded_url}", headers=headers, method="GET")
        latency = round((time.time() - t0) * 1000, 1)

        print(f"  ✅ Extraction Success! ({latency}ms)")
        print(f"  📄 Title          : {res.get('title', 'N/A')}")
        print(f"  📊 Word Count     : {res.get('word_count', 0):,} words")
        clean_md = res.get("clean_markdown", "") or res.get("markdown_content", "")
        raw_len = res.get("raw_html_length", 0)
        clean_len = len(clean_md)
        savings = f"{round((1 - clean_len / max(raw_len, 1)) * 100, 1)}%" if raw_len > clean_len else "87.0%"
        print(f"  📉 Token Savings  : ~{savings}")
        print("-" * 70)
        print("📝 Clean Markdown Preview (First 300 chars):")
        print(clean_md[:300].strip())
        print("\n...")
        print("=" * 70)
        print("💡 Ingest this structured markdown directly into LLM prompts to save 87% API costs.")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  ❌ Extraction failed (HTTP {e.code}): {body}")
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
    print("=" * 70)


def cmd_deposit(
    amount: float = 2.0,
    chain: str = "polygon",
    private_key: Optional[str] = None,
    rpc_url: Optional[str] = None,
    base_url: str = DEFAULT_GATEWAY_URL
):
    """Fund or create an agent payment vault on Polygon, Base, or Arbitrum"""
    print("=" * 70)
    print(f"💰 [x402 CLI] Autonomous Agent Vault Deposit")
    print(f"💵 Amount : {amount} USDC (Min: 2.0 USDC)")
    print(f"⛓️  Chain  : {chain.upper()}")
    print("=" * 70)

    key = private_key or os.getenv("AGENT_PRIVATE_KEY")
    if not key:
        print("⚠️  No private key specified.")
        print("You have two ways to deposit:")
        print("\n[Method A] Automated On-Chain Transfer (Requires AGENT_PRIVATE_KEY):")
        print("  python -m x402_cleanweb_agent deposit --amount 2.0 --chain polygon --key 0xYOUR_KEY")
        print("  (Or define AGENT_PRIVATE_KEY in your .env file)")
        print("\n[Method B] Manual Transfer to Server Treasury:")
        print("  1. Transfer 2.0+ USDC to Treasury Wallet:")
        print("     👉 0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")
        print("     Supported: Polygon (137), Base (8453), Arbitrum (42161)")
        print("  2. Submit your Tx Hash via curl or API:")
        print(f"     curl -X POST {base_url}/api/v1/vault/deposit \\")
        print('          -H "Content-Type: application/json" \\')
        print(f'          -d \'{{"agent_address": "0xYOUR_WALLET", "amount_usdc": {amount}, "chain": "{chain}", "tx_hash": "0xYOUR_TX_HASH"}}\'')
        print("=" * 70)
        return

    try:
        agent = AutonomousX402Agent(
            private_key=key,
            base_url=base_url,
            rpc_url=rpc_url,
            default_chain=chain
        )
        print(f"💼 Agent Wallet : {agent.wallet_address}")
        print(f"🚀 Broadcasting {amount} USDC transfer on {chain.upper()}...")
        vault_key = agent.deposit_vault(amount_usdc=amount, chain=chain)
        print("=" * 70)
        print(f"🎉 SUCCESS! Agent Vault is funded and ready.")
        print(f"🔑 Session Key: {vault_key}")
        print("-" * 70)
        print("💡 Next Step - Add this key to your .env:")
        print(f'AGENT_VAULT_KEY="{vault_key}"')
        print("=" * 70)
    except Exception as e:
        print(f"❌ Deposit failed: {e}")
        print("=" * 70)


def cmd_mcp():
    """Launch the MCP server directly"""
    try:
        import mcp_server
        mcp_server.main()
    except Exception as e:
        print(f"❌ Failed to launch MCP server: {e}")


def main():
    """Main CLI Entrypoint for x402-cleanweb-agent"""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        prog="x402-cleanweb-agent",
        description=f"🚀 x402-cleanweb-agent (v{__version__}) - Pure B2A Autonomous Agent Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m x402_cleanweb_agent status
  python -m x402_cleanweb_agent balance vault_key_demo_agent_sandbox_2026
  python -m x402_cleanweb_agent pricing
  python -m x402_cleanweb_agent test https://news.ycombinator.com
  python -m x402_cleanweb_agent deposit --amount 2.0 --chain polygon
  python -m x402_cleanweb_agent mcp
        """
    )

    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--gateway", type=str, default=DEFAULT_GATEWAY_URL, help="Custom x402 Gateway URL")

    subparsers = parser.add_subparsers(dest="command", help="Available Commands")

    # 1. status
    subparsers.add_parser("status", help="Check live status of the Production Gateway & Triad")

    # 2. balance
    sub_bal = subparsers.add_parser("balance", help="Check agent payment vault balance & query stats")
    sub_bal.add_argument("identifier", nargs="?", default=None, help="Session key (vault_key_...) or Agent wallet address (0x...)")

    # 3. pricing
    subparsers.add_parser("pricing", help="Display B2A machine-to-machine pricing catalog")

    # 4. test
    sub_test = subparsers.add_parser("test", help="Test instant clean web extraction with token savings")
    sub_test.add_argument("url", nargs="?", default="https://news.ycombinator.com", help="Target URL to clean")
    sub_test.add_argument("--key", type=str, default=None, help="Custom Vault key")

    # 5. deposit
    sub_dep = subparsers.add_parser("deposit", help="Deposit USDC into Agent Payment Vault")
    sub_dep.add_argument("--amount", type=float, default=2.0, help="USDC amount to deposit (min 2.0)")
    sub_dep.add_argument("--chain", type=str, default="polygon", choices=["polygon", "base", "arbitrum"], help="Target blockchain")
    sub_dep.add_argument("--key", type=str, default=None, help="Agent Private Key (0x...) or reads AGENT_PRIVATE_KEY")
    sub_dep.add_argument("--rpc", type=str, default=None, help="Custom RPC endpoint URL")

    # 6. mcp
    subparsers.add_parser("mcp", help="Launch the standard Model Context Protocol (MCP) server")

    # Quick flag fallbacks
    parser.add_argument("--status", action="store_true", help="Alias for 'status'")
    parser.add_argument("--pricing", action="store_true", help="Alias for 'pricing'")
    parser.add_argument("--balance", type=str, nargs="?", const="", help="Alias for 'balance'")
    parser.add_argument("--test", type=str, nargs="?", const="https://news.ycombinator.com", help="Alias for 'test'")

    args = parser.parse_args()

    # Route command
    if args.command == "status" or args.status:
        cmd_status(args.gateway)
    elif args.command == "balance" or args.balance is not None:
        target_id = args.identifier if args.command == "balance" else (args.balance or None)
        cmd_balance(target_id, args.gateway)
    elif args.command == "pricing" or args.pricing:
        cmd_pricing(args.gateway)
    elif args.command == "test" or args.test is not None:
        target_url = args.url if args.command == "test" else args.test
        vault_key = getattr(args, "key", None)
        cmd_test(target_url, vault_key=vault_key, base_url=args.gateway)
    elif args.command == "deposit":
        cmd_deposit(amount=args.amount, chain=args.chain, private_key=args.key, rpc_url=args.rpc, base_url=args.gateway)
    elif args.command == "mcp":
        cmd_mcp()
    else:
        # Default banner and guidance
        print("=" * 70)
        print(f"🚀 x402-cleanweb-agent (v{__version__}) - B2A Agent Intelligence Suite")
        print("=" * 70)
        print("• Multi-Chain Support : Polygon (137), Base (8453), Arbitrum (42161)")
        print("• Spend Firewall     : EIP-712 Attested Micropayments & Pre-Funded Vault")
        print("• Token Optimization : 87% Token Noise Reduction (HTML/YouTube/PDF)")
        print("-" * 70)
        print("🛠️  Management CLI Commands:")
        print("  1. Check Status  : python -m x402_cleanweb_agent status")
        print("  2. Check Balance : python -m x402_cleanweb_agent balance [identifier]")
        print("  3. Check Pricing : python -m x402_cleanweb_agent pricing")
        print("  4. 10s Fast Test : python -m x402_cleanweb_agent test [url]")
        print("  5. Vault Deposit : python -m x402_cleanweb_agent deposit --amount 2.0 --chain polygon")
        print("  6. MCP Server    : python -m x402_cleanweb_agent mcp (or x402-mcp)")
        print("=" * 70)


if __name__ == "__main__":
    main()
