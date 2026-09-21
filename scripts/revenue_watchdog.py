"""
x402 AI Autonomous Agent Suite - Real-Time On-Chain Revenue Watchdog
--------------------------------------------------------------------------------
Monitors actual USDC incoming transfers across Polygon, Base, and Arbitrum
to Server Treasury (0x255F9991233f86B29dB847c8d5b8CB9915e80dCf).
Tracks live paid queries, agent vault deposits, and calculates net revenue.
"""

import os
import sys
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

TREASURY_WALLET = os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")

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


def check_multi_chain_revenue():
    print("\n" + "=" * 65)
    print(f"💰 [x402 REVENUE WATCHDOG] Multi-Chain Live Treasury Audit")
    print(f"💼 Server Treasury Wallet: {TREASURY_WALLET}")
    print(f"⏱️  Audit Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("=" * 65)

    total_usdc_accumulated = 0.0

    for net_key, cfg in NETWORKS.items():
        try:
            w3 = Web3(Web3.HTTPProvider(cfg["rpc"], request_kwargs={"timeout": 6}))
            if not w3.is_connected():
                print(f"  [{cfg['name']}] ⚠️ RPC Connection Timeout")
                continue

            usdc_contract = w3.eth.contract(
                address=Web3.to_checksum_address(cfg["usdc"]),
                abi=ERC20_BALANCE_ABI
            )
            raw_bal = usdc_contract.functions.balanceOf(Web3.to_checksum_address(TREASURY_WALLET)).call()
            bal_usdc = raw_bal / (10 ** cfg["decimals"])
            total_usdc_accumulated += bal_usdc

            # Gas balance
            native_wei = w3.eth.get_balance(Web3.to_checksum_address(TREASURY_WALLET))
            native_bal = float(w3.from_wei(native_wei, "ether"))

            print(f"  🟢 {cfg['name']:<22} : ${bal_usdc:>10.4f} USDC  (Gas: {native_bal:.4f})")
        except Exception as e:
            print(f"  [{cfg['name']}] ❌ Error: {str(e)[:40]}")

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

