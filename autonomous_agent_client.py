"""
Autonomous AI Agent x402 Client SDK
--------------------------------------------------------------------------------
Zero-Human-in-the-Loop Web3 Data Scraper for Autonomous AI Agents.
Enables AI agents with a Polygon wallet (Private Key) to autonomously handle
HTTP 402 Payment Required flows, transfer USDC on-chain, and fetch LLM-ready data.
"""

import os
import time
import requests
from typing import Dict, Any, Optional
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# ERC-20 Transfer ABI
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

DEFAULT_BASE_URL = "https://x402-cleanweb-agent.onrender.com"
DEFAULT_RPC_URLS = [
    "https://polygon-bor-rpc.publicnode.com",
    "https://polygon.llamarpc.com",
    "https://1rpc.io/matic",
    "https://polygon-rpc.com"
]

class AutonomousX402Agent:
    """
    Autonomous Web3 AI Agent Client for x402 Protocol on Polygon Mainnet.
    
    Usage:
        agent = AutonomousX402Agent(private_key="0x...")
        result = agent.clean_web("https://example.com/article")
        print(result["markdown_content"])
    """

    def __init__(
        self,
        private_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        rpc_url: Optional[str] = None
    ):
        self.private_key = private_key or os.getenv("AGENT_PRIVATE_KEY")
        self.base_url = base_url.rstrip("/")
        
        # Initialize Web3 Provider with fallback
        self.w3 = self._init_web3(rpc_url)
        
        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)
            self.wallet_address = self.account.address
        else:
            self.account = None
            self.wallet_address = None

    def _init_web3(self, rpc_url: Optional[str] = None) -> Web3:
        urls = [rpc_url] + DEFAULT_RPC_URLS if rpc_url else DEFAULT_RPC_URLS
        for url in urls:
            if not url:
                continue
            try:
                w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 10}))
                if w3.is_connected():
                    return w3
            except Exception:
                continue
        return Web3(Web3.HTTPProvider(DEFAULT_RPC_URLS[0]))

    def _pay_and_get_tx_hash(self, x402_info: Dict[str, Any]) -> str:
        """Executes on-chain USDC transfer based on 402 instructions."""
        if not self.account:
            raise ValueError(
                "Agent private key is required to execute on-chain micropayments. "
                "Set AGENT_PRIVATE_KEY env var or pass private_key to AutonomousX402Agent()."
            )

        token_contract_addr = Web3.to_checksum_address(x402_info["token_contract"])
        recipient_addr = Web3.to_checksum_address(x402_info["recipient"])
        amount_raw = int(x402_info["amount_raw"])

        token_contract = self.w3.eth.contract(address=token_contract_addr, abi=ERC20_ABI)
        nonce = self.w3.eth.get_transaction_count(self.wallet_address, "pending")
        gas_price = self.w3.eth.gas_price

        # Build ERC20 Transfer transaction
        tx = token_contract.functions.transfer(
            recipient_addr,
            amount_raw
        ).build_transaction({
            "from": self.wallet_address,
            "nonce": nonce,
            "gas": 90000,
            "gasPrice": int(gas_price * 1.2),  # +20% for fast inclusion
            "chainId": 137
        })

        # Sign & Send
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction).hex()
        
        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt.get("status") != 1:
            raise RuntimeError(f"USDC Transfer reverted on-chain: {tx_hash}")

        return tx_hash

    def _execute_x402_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        
        # 1. Initial Request (Check if payment required)
        res = requests.get(url, params=params)
        
        if res.status_code == 200:
            return res.json()
        
        if res.status_code == 402:
            data = res.json()
            x402_info = data.get("x402", {})
            required_usdc = x402_info.get("amount", "0.01")
            
            print(f"[🤖 x402 Agent] 402 Payment Required: {required_usdc} USDC on Polygon.")
            print(f"[🤖 x402 Agent] Paying from agent wallet: {self.wallet_address}...")
            
            # 2. Autonomous On-Chain Payment
            tx_hash = self._pay_and_get_tx_hash(x402_info)
            print(f"[🤖 x402 Agent] On-chain payment confirmed! Tx: {tx_hash}")
            
            # 3. Re-request with X-Payment-Tx Header
            paid_res = requests.get(
                url,
                params=params,
                headers={"X-Payment-Tx": tx_hash}
            )
            
            if paid_res.status_code == 200:
                print(f"[🤖 x402 Agent] Data successfully acquired.")
                return paid_res.json()
            else:
                raise RuntimeError(f"Failed to fetch data after payment: {paid_res.text}")

        res.raise_for_status()
        return res.json()

    # --- High-level Agent Tools ---

    def clean_web(self, url: str) -> Dict[str, Any]:
        """Scrapes and converts messy HTML to clean Markdown with token savings (0.01 USDC)."""
        return self._execute_x402_request("/api/v1/clean-web", {"url": url})

    def clean_youtube(self, url: str, language: str = "en") -> Dict[str, Any]:
        """Extracts complete YouTube video transcripts with timestamps (0.02 USDC)."""
        return self._execute_x402_request("/api/v1/clean-youtube", {"url": url, "language": language})

    def clean_pdf(self, url: str) -> Dict[str, Any]:
        """Converts research papers and reports from PDF to structured Markdown (0.05 USDC)."""
        return self._execute_x402_request("/api/v1/clean-pdf", {"url": url})

    def clean_text(self, url: str) -> Dict[str, Any]:
        """Extracts ultra-lightweight raw text for embedding and vector indexing (0.005 USDC)."""
        return self._execute_x402_request("/api/v1/clean-text", {"url": url})


if __name__ == "__main__":
    print("🤖 Autonomous x402 AI Agent SDK initialized.")
    print("Example usage:")
    print("""
    from autonomous_agent_client import AutonomousX402Agent

    agent = AutonomousX402Agent(private_key="0xYOUR_AGENT_PRIVATE_KEY")
    result = agent.clean_web("https://example.com/article")
    
    print("Title:", result["title"])
    print("Markdown:", result["markdown_content"][:200])
    print("Tokens Saved:", result["token_analytics"]["tokens_saved"])
    """)
