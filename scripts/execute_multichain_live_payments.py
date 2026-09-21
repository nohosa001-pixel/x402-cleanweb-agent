"""
Multi-Chain Live On-Chain Settlement Script for Base (8453) and Arbitrum One (42161).
Executes real 0.001 USDC micro-payments, confirms receipts on block explorers,
and verifies production API redemption on Google Cloud Run.
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

SERVER_PK = os.getenv("SERVER_PRIVATE_KEY")
LIVE_API_URL = "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app"

CHAINS_TO_EXECUTE = [
    {
        "name": "Base (Coinbase L2)",
        "chain_key": "base",
        "chain_id": 8453,
        "rpc": "https://mainnet.base.org",
        "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "recipient": "0x28292D76E07E5539F15F3b97935dE8E0432E76DD",
        "explorer": "https://basescan.org/tx",
        "gas_limit": 100000
    },
    {
        "name": "Arbitrum One",
        "chain_key": "arbitrum",
        "chain_id": 42161,
        "rpc": "https://arb1.arbitrum.io/rpc",
        "usdc_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "recipient": "0x28292D76E07E5539F15F3b97935dE8E0432E76DD",
        "explorer": "https://arbiscan.io/tx",
        "gas_limit": 150000
    }
]

ERC20_ABI = [
    {
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def run_chain_payment(chain_info: dict) -> dict:
    name = chain_info["name"]
    chain_key = chain_info["chain_key"]
    chain_id = chain_info["chain_id"]
    rpc = chain_info["rpc"]
    usdc_addr = chain_info["usdc_address"]
    recipient = chain_info["recipient"]
    explorer_base = chain_info["explorer"]

    print("\n" + "=" * 76)
    print(f"🚀 [EXECUTING LIVE PAYMENT ON {name.upper()}] (Chain ID: {chain_id})")
    print("=" * 76)

    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
    account = w3.eth.account.from_key(SERVER_PK)
    sender = account.address
    print(f"💼 Payer Address: {sender}")

    usdc = w3.eth.contract(address=w3.to_checksum_address(usdc_addr), abi=ERC20_ABI)
    bal_usdc = usdc.functions.balanceOf(sender).call() / 1e6
    eth_bal = w3.eth.get_balance(sender) / 1e18
    print(f"💰 USDC Balance: {bal_usdc:.6f} USDC | ETH Gas Balance: {eth_bal:.6f} ETH")

    if bal_usdc < 0.001:
        raise ValueError(f"Insufficient USDC balance on {name}")
    if eth_bal < 0.00005:
        raise ValueError(f"Insufficient ETH gas on {name}")

    # Build ERC-20 transfer
    amount_raw = 1000  # 0.001000 USDC
    nonce = w3.eth.get_transaction_count(sender, "pending")
    gas_price = int(w3.eth.gas_price * 1.25)

    tx_params = {
        "from": sender,
        "nonce": nonce,
        "gas": chain_info["gas_limit"],
        "chainId": chain_id
    }

    # EIP-1559 vs Legacy gas
    try:
        latest_block = w3.eth.get_block("latest")
        if "baseFeePerGas" in latest_block and latest_block["baseFeePerGas"] is not None:
            max_priority = w3.eth.max_priority_fee if hasattr(w3.eth, "max_priority_fee") else w3.to_wei(0.001, "gwei")
            tx_params["maxFeePerGas"] = int(latest_block["baseFeePerGas"] * 1.5 + max_priority)
            tx_params["maxPriorityFeePerGas"] = max_priority
        else:
            tx_params["gasPrice"] = gas_price
    except Exception:
        tx_params["gasPrice"] = gas_price

    tx = usdc.functions.transfer(w3.to_checksum_address(recipient), amount_raw).build_transaction(tx_params)

    print(f"💸 Transferring 0.001000 USDC to Vault: {recipient}...")
    signed = w3.eth.account.sign_transaction(tx, SERVER_PK)
    raw_tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction).hex()
    tx_hash = "0x" + raw_tx_hash if not raw_tx_hash.startswith("0x") else raw_tx_hash

    print(f"⚡ Broadcasted! Tx Hash: {tx_hash}")
    print(f"🔗 Explorer URL: {explorer_base}/{tx_hash}")

    print("⏳ Waiting for block confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60, poll_latency=1.0)
    if receipt.status != 1:
        raise RuntimeError(f"Transaction reverted on {name}!")

    print(f"✅ Confirmed in Block #{receipt.blockNumber} (Gas Used: {receipt.gasUsed})")

    # Give RPC indexers 2 seconds
    time.sleep(2.5)

    # Call production Cloud Run endpoint
    print(f"🌐 Calling Production Cloud Run API ({chain_key})...")
    headers = {
        "x-payment-tx": tx_hash,
        "x-chain": chain_key
    }
    resp = requests.get(
        f"{LIVE_API_URL}/api/v1/clean-web?url=https://example.com",
        headers=headers,
        timeout=15
    )

    print(f"📥 Response HTTP Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        rcpt = data.get("payment_receipt", {})
        print(f"🎉 [SETTLEMENT CONFIRMED ON {name.upper()}!]")
        print(f"   Receipt ID: {rcpt.get('receipt_id')}")
        print(f"   Method: {rcpt.get('payment_method')} ({rcpt.get('cost_usdc')} USDC)")
        print(f"   Title: {data.get('title')}")
        return {
            "chain": name,
            "tx_hash": tx_hash,
            "block": receipt.blockNumber,
            "receipt_id": rcpt.get("receipt_id"),
            "status": "SUCCESS"
        }
    else:
        print(f"⚠️ Verification Failed Body: {resp.text[:300]}")
        return {
            "chain": name,
            "tx_hash": tx_hash,
            "block": receipt.blockNumber,
            "status": f"HTTP_{resp.status_code}"
        }

def main():
    print("=" * 76)
    print("💎 [x402 MULTI-CHAIN LIVE SETTLEMENT] Base & Arbitrum One Dual Execution")
    print("=" * 76)

    results = []
    for chain_info in CHAINS_TO_EXECUTE:
        res = run_chain_payment(chain_info)
        results.append(res)
        time.sleep(2)

    print("\n" + "=" * 76)
    print("📊 FINAL MULTI-CHAIN SETTLEMENT SUMMARY")
    print("=" * 76)
    for r in results:
        print(f"  • {r['chain']}: {r['status']} | Tx: {r['tx_hash']} (Block #{r['block']})")

    # Query health endpoint
    h = requests.get(f"{LIVE_API_URL}/health").json()
    stats = h.get("storage_stats", {})
    print(f"\n📈 Live Cloud Run used_transactions_count: {stats.get('used_transactions_count')} (Total Recorded)")
    print("=" * 76)

if __name__ == "__main__":
    main()
