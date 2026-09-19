"""
x402-cleanweb-agent
~~~~~~~~~~~~~~~~~~~
Pure B2A Autonomous Agent Real-Time Data Oracle & x402 Signed Grounding Engine
on Polygon, Base, and Arbitrum.

Official Package Entrypoint:
    import x402_cleanweb_agent
    from x402_cleanweb_agent import AutonomousAgentClient, agent_tools, __version__
"""

import sys
from app import __version__
from autonomous_agent_client import AutonomousX402Agent

# Convenience alias
AutonomousAgentClient = AutonomousX402Agent

try:
    import agent_tools
except ImportError:
    agent_tools = None

__all__ = [
    "__version__",
    "AutonomousX402Agent",
    "AutonomousAgentClient",
    "agent_tools",
]

def main():
    """CLI Entrypoint for `python -m x402_cleanweb_agent`"""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 70)
    print(f"🚀 x402-cleanweb-agent (v{__version__}) - B2A Agent Intelligence Suite")
    print("=" * 70)
    print("• Multi-Chain Support : Polygon (137), Base (8453), Arbitrum (42161)")
    print("• Spend Firewall     : EIP-712 Attested Micropayments & Pre-Funded Vault")
    print("• Token Optimization : 87% Token Noise Reduction (HTML/YouTube/PDF)")
    print("-" * 70)
    print("💡 Quick Start:")
    print("  1. Launch MCP Server : x402-mcp  (or `uvx x402-cleanweb-agent`)")
    print("  2. Python Client     : from x402_cleanweb_agent import AutonomousAgentClient")
    print("  3. LangChain/CrewAI  : import agent_tools")
    print("=" * 70)

if __name__ == "__main__":
    main()
