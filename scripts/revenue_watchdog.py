"""
x402 AI Autonomous Agent Suite - Real-Time On-Chain Revenue Watchdog
--------------------------------------------------------------------------------
Monitors actual USDC incoming transfers across Polygon, Base, and Arbitrum
to Server Treasury (0xA185B43fDD19619f99952AAed6eabf1029bF36a1).
Tracks live paid queries, agent vault deposits, and calculates net revenue.
"""

import os
import sys
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import requests
from web3 import Web3
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

TREASURY_WALLET = os.getenv("SERVER_WALLET_ADDRESS", "0xA185B43fDD19619f99952AAed6eabf1029bF36a1")

NETWORKS = {
    "polygon": {
        "name": "Polygon Mainnet",
        "rpc": os.getenv("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com"),
        "usdc": os.getenv("USDC_CONTRACT_ADDRESS", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"),
        "decimals": 6
    },
    "base": {
        "name": "Base (Coinbase L2)",
        "rpc": "https://mainnet.base.org",
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "decimals": 6
    },
    "arbitrum": {
        "name": "Arbitrum One",
        "rpc": "https://arb1.arbitrum.io/rpc",
        "usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "decimals": 6
    }
}

ERC20_BALANCE_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]


from app.multi_chain import multi_chain_manager


def check_multi_chain_revenue():
    print("\n" + "=" * 65)
    print(f"💰 [x402 REVENUE WATCHDOG] Multi-Chain Live Treasury Audit")
    print(f"💼 Server EVM Wallet: {TREASURY_WALLET}")
    print(f"💼 Server Solana Wallet: {multi_chain_manager.solana_recipient}")
    print(f"⏱️  Audit Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("=" * 65)

    summary = multi_chain_manager.get_multi_chain_treasury_summary()
    total_usdc_accumulated = summary.get("total_usdc_accumulated", 0.0)

    for net_key, info in summary.get("networks", {}).items():
        name = info.get("display_name", net_key)
        bal_usdc = info.get("usdc_balance", 0.0)
        native_bal = info.get("native_balance", 0.0)
        native_sym = info.get("native_symbol", "GAS")
        print(f"  🟢 {name:<22} : ${bal_usdc:>10.4f} USDC  (Gas: {native_bal:.4f} {native_sym})")

    print("-" * 65)
    print(f"  💵 TOTAL MULTI-CHAIN TREASURY : ${total_usdc_accumulated:>10.4f} USDC")
    print("=" * 65 + "\n")
    return total_usdc_accumulated


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        print(f"📡 Starting continuous treasury surveillance (polling every {interval}s)...")
        while True:
            try:
                check_multi_chain_revenue()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n🛑 Surveillance stopped by user.")
                break
    else:
        check_multi_chain_revenue()

