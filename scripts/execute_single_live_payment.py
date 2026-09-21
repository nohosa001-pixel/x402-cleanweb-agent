"""
Execution Script: Real Live On-Chain Micro-Payment (0.001 USDC) on Polygon Mainnet.
1. Broadcasts live ERC-20 transfer of 0.001 USDC to AgentPaymentVault.
2. Captures mined tx_hash on Polygonscan.
3. Submits tx_hash to live production endpoint (Cloud Run) to unlock paid content.
4. Verifies 100% on-chain settlement & anti-replay protection.
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

# Configuration
POLYGON_RPC = os.getenv("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")
SERVER_PK = os.getenv("SERVER_PRIVATE_KEY")
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
RECIPIENT_VAULT = "0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861"  # Polygon AgentPaymentVault
LIVE_API_URL = "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app"

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

def execute_live_payment():
    print("=" * 72)
    print("💎 [x402 LIVE PAYMENT] Executing Real On-Chain 0.001 USDC Settlement")
    print("=" * 72)

    if not SERVER_PK:
        print("❌ Error: SERVER_PRIVATE_KEY not found in .env")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    account = w3.eth.account.from_key(SERVER_PK)
    sender_addr = account.address
    print(f"💼 Payer Wallet Address: {sender_addr}")

    usdc = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=ERC20_ABI)
    balance_raw = usdc.functions.balanceOf(sender_addr).call()
    balance_usdc = balance_raw / 1e6
    print(f"💰 Initial USDC Balance: {balance_usdc:.6f} USDC")

    if balance_usdc < 0.001:
        print("❌ Insufficient USDC balance for 0.001 USDC payment")
        sys.exit(1)

    # 1. Build and send transaction
    amount_raw = 1000  # 0.001000 USDC (6 decimals)
    recipient_checksum = w3.to_checksum_address(RECIPIENT_VAULT)
    print(f"🎯 Target Recipient (AgentPaymentVault): {recipient_checksum}")
    print(f"💸 Transfer Amount: 0.001000 USDC")

    nonce = w3.eth.get_transaction_count(sender_addr, "pending")
    gas_price = int(w3.eth.gas_price * 1.35)  # 35% premium for instant block inclusion

    tx = usdc.functions.transfer(recipient_checksum, amount_raw).build_transaction({
        "from": sender_addr,
        "nonce": nonce,
        "gas": 80000,
        "gasPrice": gas_price,
        "chainId": 137
    })

    print("\n⏳ Signing and broadcasting transaction to Polygon Mainnet...")
    signed_tx = w3.eth.account.sign_transaction(tx, SERVER_PK)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction).hex()
    print(f"🚀 Broadcasted! Tx Hash: {tx_hash}")
    print(f"🔗 Polygonscan URL: https://polygonscan.com/tx/{tx_hash}")

    # 2. Wait for block mining
    print("⏳ Waiting for transaction receipt on Polygon...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60, poll_latency=1.5)
    if receipt.status != 1:
        print(f"❌ Transaction reverted! Status: {receipt.status}")
        sys.exit(1)

    print(f"✅ Transaction Confirmed in Block #{receipt.blockNumber}!")
    print(f"⛽ Gas Used: {receipt.gasUsed}")

    # 3. Call Live Cloud Run Endpoint with the Real Tx Hash
    print("\n" + "=" * 72)
    print("🌐 [LIVE API VERIFICATION] Calling Production Cloud Run with Real Tx")
    print(f"🔗 Endpoint: {LIVE_API_URL}/api/v1/clean-web?url=https://example.com")
    print("=" * 72)

    headers = {
        "x-payment-tx": tx_hash,
        "x-payment-chain": "polygon"
    }

    # Small delay for RPC indexers to sync
    time.sleep(2)

    resp = requests.get(
        f"{LIVE_API_URL}/api/v1/clean-web?url=https://example.com",
        headers=headers,
        timeout=15
    )

    print(f"📥 Response HTTP Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print("🎉 [PAYMENT SUCCESSFUL & ACCEPTED!]")
        print(f"   Title: {data.get('title')}")
        print(f"   Clean Markdown Length: {len(data.get('content', ''))} chars")
        print(f"   Payment Receipt: {data.get('receipt', headers)}")
    else:
        print(f"⚠️ Response Body: {resp.text[:300]}")

    # 4. Anti-Replay Attack Check (Re-submitting the same Tx must be rejected)
    print("\n🛡️ [ANTI-REPLAY TEST] Re-submitting identical tx_hash to test security...")
    replay_resp = requests.get(
        f"{LIVE_API_URL}/api/v1/clean-web?url=https://example.com",
        headers=headers,
        timeout=15
    )
    if replay_resp.status_code in [400, 402]:
        print(f"✅ Anti-Replay Guard Working: Duplicate Tx Blocked (HTTP {replay_resp.status_code})")
    else:
        print(f"⚠️ Unexpected Replay Status: {replay_resp.status_code}")

    print("\n" + "=" * 72)
    print(f"🏁 LIVE SETTLEMENT COMPLETE! Polygonscan: https://polygonscan.com/tx/{tx_hash}")
    print("=" * 72)

if __name__ == "__main__":
    execute_live_payment()
