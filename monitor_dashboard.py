"""
x402 AI Agent Suite - Real-Time Operations & Business Monitor Dashboard (v2.1.0)
Cloud Run Gateway, Polygon Mainnet On-Chain Balance, Economic Arbitrage & Latency Monitoring
"""

import os
import sys
import time
import argparse
import requests
from typing import Dict, Any, Optional
from web3 import Web3
from dotenv import load_dotenv

# Windows UTF-8 콘솔 인코딩 대응
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# .env 로드
load_dotenv(override=True)

# Configuration & Constants
GCP_URL = os.getenv("GCP_GATEWAY_URL", "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app")
RECIPIENT_WALLET = os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")
USDC_CONTRACT = os.getenv("USDC_CONTRACT_ADDRESS", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
POLYGON_RPC = os.getenv("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def fetch_gateway_health() -> Dict[str, Any]:
    try:
        t0 = time.time()
        res = requests.get(f"{GCP_URL}/health", timeout=6)
        latency_ms = round((time.time() - t0) * 1000, 1)
        if res.status_code == 200:
            data = res.json()
            data["latency_ms"] = latency_ms
            data["status_code"] = 200
            return data
        return {"status_code": res.status_code, "latency_ms": latency_ms, "status": "unhealthy"}
    except Exception as e:
        return {"status_code": 0, "error": str(e), "status": "down"}


def fetch_arbitrage_metrics() -> Optional[Dict[str, Any]]:
    try:
        res = requests.get(f"{GCP_URL}/api/v1/agent/arbitrage-roi", timeout=6)
        if res.status_code == 200:
            return res.json().get("economic_arbitrage", {})
    except Exception:
        pass
    return None


def fetch_onchain_balances() -> Dict[str, Any]:
    result = {"connected": False, "rpc_latency_ms": 0, "usdc": 0.0, "pol": 0.0, "error": None}
    try:
        t0 = time.time()
        w3 = Web3(Web3.HTTPProvider(POLYGON_RPC, request_kwargs={"timeout": 6}))
        if w3.is_connected():
            result["connected"] = True
            result["rpc_latency_ms"] = round((time.time() - t0) * 1000, 1)
            
            # POL Balance
            pol_wei = w3.eth.get_balance(Web3.to_checksum_address(RECIPIENT_WALLET))
            result["pol"] = float(w3.from_wei(pol_wei, "ether"))

            # USDC Balance
            usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_CONTRACT), abi=ERC20_ABI)
            raw_usdc = usdc.functions.balanceOf(Web3.to_checksum_address(RECIPIENT_WALLET)).call()
            result["usdc"] = raw_usdc / 10**6
        else:
            result["error"] = "RPC node unreachable"
    except Exception as e:
        result["error"] = str(e)
    return result


def render_dashboard(iteration: int = 1):
    health = fetch_gateway_health()
    balances = fetch_onchain_balances()
    arbitrage = fetch_arbitrage_metrics()

    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"{CYAN}{BOLD}{'=' * 74}{RESET}")
    print(f"{CYAN}{BOLD} 🚀 Polygon x402 AI Agent Suite — Real-Time Operations Monitor {RESET} {YELLOW}(v2.1.0){RESET}")
    print(f"{CYAN}{BOLD}{'=' * 74}{RESET}")
    print(f" ⏱️  Check Timestamp : {current_time} (Cycle #{iteration})")
    print(f" 🌐 Cloud Run Gateway: {GCP_URL}")
    print(f" 💼 Server Wallet    : {RECIPIENT_WALLET}")
    print(f" ⛓️  Blockchain       : Polygon Mainnet (PoS Chain ID 137)")
    print(f"{CYAN}{'-' * 74}{RESET}")

    # 1. Cloud Run Gateway Status
    if health.get("status_code") == 200:
        ver = health.get("version", "2.1.0")
        proto = health.get("protocol", "x402-v2")
        passes = health.get("active_credit_passes", 0)
        trials = health.get("free_trials_claimed", 0)
        lat = health.get("latency_ms", 0)
        
        lat_color = GREEN if lat < 800 else (YELLOW if lat < 2000 else RED)
        print(f" 🟢 {BOLD}Cloud Run Gateway{RESET} : {GREEN}ONLINE{RESET} ({lat_color}{lat}ms{RESET}, Rev v{ver}, Proto: {proto})")
        print(f"    ├─ 🎟️  Active Credit Passes : {BOLD}{passes}{RESET} active passes")
        print(f"    └─ 🎁 Free Onboarding Nonces: {BOLD}{trials}{RESET} agents claimed")
    else:
        err = health.get("error") or f"HTTP {health.get('status_code')}"
        print(f" 🔴 {BOLD}Cloud Run Gateway{RESET} : {RED}OFFLINE / ERROR ({err}){RESET}")

    # 2. On-Chain Balances & Gas Health
    if balances["connected"]:
        usdc_val = balances["usdc"]
        pol_val = balances["pol"]
        rpc_lat = balances["rpc_latency_ms"]

        gas_warning = ""
        if pol_val < 0.005:
            gas_warning = f" {RED}[⚠️ LOW GAS WARNING: Top up POL]{RESET}"
        elif pol_val < 0.02:
            gas_warning = f" {YELLOW}[⚠️ Moderate Gas]{RESET}"

        print(f" ⚡ {BOLD}Polygon RPC Node{RESET}  : {GREEN}CONNECTED{RESET} ({rpc_lat}ms via {POLYGON_RPC.split('/')[2]})")
        print(f" 💰 {BOLD}USDC Revenue Acc.{RESET} : {GREEN}${usdc_val:.4f} USDC{RESET}")
        print(f" ⛽ {BOLD}Server Gas (POL){RESET}  : {BOLD}{pol_val:.4f} POL{RESET}{gas_warning}")
    else:
        print(f" ⚠️  {BOLD}On-Chain Status{RESET}   : {YELLOW}RPC Failed ({balances.get('error')}){RESET}")

    # 3. Economic Arbitrage & AI Efficiency ROI
    if arbitrage:
        token_stats = arbitrage.get("token_reduction", {})
        econ_stats = arbitrage.get("dollar_economics_per_query", {})
        print(f"{CYAN}{'-' * 74}{RESET}")
        print(f" 📊 {BOLD}Value Proposition & Machine Arbitrage Performance:{RESET}")
        print(f"    ├─ 📉 Token Noise Cut  : {GREEN}{token_stats.get('savings_percentage', '87.2%')}{RESET} reduction (Avg {token_stats.get('raw_web_tokens', '15,000')} -> {token_stats.get('clean_tokens', '1,920')} tokens)")
        print(f"    ├─ 📈 AI Economic ROI  : {GREEN}{econ_stats.get('roi_percentage', '445.0%')}{RESET} net savings vs uncleaned LLM input")
        print(f"    └─ 💵 Net Agent Profit : {GREEN}${econ_stats.get('net_savings_usd', '0.0445')}{RESET} saved / query")

    print(f"{CYAN}{BOLD}{'=' * 74}{RESET}")
    print(f" 🔍 PolygonScan Explorer : https://polygonscan.com/address/{RECIPIENT_WALLET}#tokentxns")
    print(f"{CYAN}{BOLD}{'=' * 74}{RESET}")


def main():
    parser = argparse.ArgumentParser(description="Real-Time Business & Ops Monitor for x402 AI Agent Suite")
    parser.add_argument("-w", "--watch", action="store_true", help="Enable continuous real-time monitoring mode")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Refresh interval in seconds (default: 5s)")
    args = parser.parse_args()

    if args.watch:
        print(f"{CYAN}Starting continuous monitoring every {args.interval}s... (Press Ctrl+C to exit){RESET}")
        cycle = 1
        try:
            while True:
                clear_screen()
                render_dashboard(cycle)
                print(f"\n{YELLOW}▶ Refreshing in {args.interval} seconds... [Press Ctrl+C to stop]{RESET}")
                time.sleep(args.interval)
                cycle += 1
        except KeyboardInterrupt:
            print(f"\n{GREEN}Monitoring stopped by user.{RESET}")
    else:
        render_dashboard(1)


if __name__ == "__main__":
    main()
