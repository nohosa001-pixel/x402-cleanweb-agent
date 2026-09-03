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

DEFAULT_BASE_URL = "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app"
DEFAULT_RPC_URLS = [
    "https://polygon-bor-rpc.publicnode.com",
    "https://polygon.llamarpc.com",
    "https://1rpc.io/matic",
    "https://rpc.ankr.com/polygon",
    "https://polygon.drpc.org"
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

    def _execute_x402_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        agent_pass: Optional[str] = None,
        agent_nonce: Optional[str] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {}
        if agent_pass:
            headers["X-Agent-Pass"] = agent_pass
        if agent_nonce:
            headers["X-Agent-Nonce"] = agent_nonce

        # 1. Initial Request
        if method == "POST":
            res = requests.post(url, params=params, json=json_body, headers=headers)
        else:
            res = requests.get(url, params=params, headers=headers)

        if res.status_code == 200:
            return res.json()

        if res.status_code == 402:
            data = res.json()
            x402_info = data.get("x402") or data.get("challenge") or {}
            if "token_address" in x402_info and "token_contract" not in x402_info:
                x402_info["token_contract"] = x402_info["token_address"]
            if "recipient_wallet" in x402_info and "recipient" not in x402_info:
                x402_info["recipient"] = x402_info["recipient_wallet"]
            if "amount_usdc" in x402_info and "amount" not in x402_info:
                x402_info["amount"] = x402_info["amount_usdc"]
            if "amount" in x402_info and "amount_raw" not in x402_info:
                x402_info["amount_raw"] = str(int(float(x402_info["amount"]) * 1_000_000))

            required_usdc = x402_info.get("amount", data.get("required_usdc", "0.001"))
            suggested_action = data.get("suggested_action", "")

            print(f"[x402 Agent] 402 Payment Required: {required_usdc} USDC on Polygon.")
            if suggested_action:
                print(f"[x402 Agent Action]: {suggested_action}")
            print(f"[x402 Agent] Paying from agent wallet: {self.wallet_address}...")

            # 2. Autonomous On-Chain Payment
            tx_hash = self._pay_and_get_tx_hash(x402_info)
            print(f"[x402 Agent] On-chain payment confirmed! Tx: {tx_hash}")

            # 3. Re-request with X-Payment-Tx Header
            headers["X-Payment-Tx"] = tx_hash
            if method == "POST":
                paid_res = requests.post(url, params=params, json=json_body, headers=headers)
            else:
                paid_res = requests.get(url, params=params, headers=headers)

            if paid_res.status_code == 200:
                print(f"[x402 Agent] Data successfully acquired.")
                return paid_res.json()
            else:
                raise RuntimeError(f"Failed to fetch data after payment: {paid_res.text}")

        res.raise_for_status()
        return res.json()

    # --- High-level Agent Tools ---

    def get_arbitrage_roi(self, url: Optional[str] = None) -> Dict[str, Any]:
        """[Economic Rationality Proof] Calculates mathematical token savings and ROI."""
        params = {}
        if url:
            params["url"] = url
        res = requests.get(f"{self.base_url}/api/v1/agent/arbitrage-roi", params=params)
        res.raise_for_status()
        return res.json()

    def mint_credit_pass(self, amount_usdc: float = 1.0, referral_wallet: Optional[str] = None) -> str:
        """
        [Zero-Latency Pass] Mints a reusable prepaid credit pass:
        - 1.0 USDC = 100 API Calls
        - 5.0 USDC = 600 API Calls (20% bonus)
        Returns the pass_token string to reuse across calls without per-call on-chain transactions.
        """
        raw_amount = int(amount_usdc * 10**6)
        x402_info = {
            "token_contract": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
            "recipient": "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf",
            "amount_raw": str(raw_amount)
        }
        print(f"[x402 Agent] Minting Prepaid Credit Pass for {amount_usdc} USDC...")
        tx_hash = self._pay_and_get_tx_hash(x402_info)
        
        payload = {"tx_hash": tx_hash, "amount_usdc": amount_usdc}
        if referral_wallet:
            payload["referral_wallet"] = referral_wallet

        mint_res = requests.post(f"{self.base_url}/api/v1/pass/mint", json=payload)
        mint_res.raise_for_status()
        data = mint_res.json()
        pass_token = data["pass_token"]
        print(f"[x402 Agent] Pass minted successfully! Token: {pass_token} ({data['credits']} credits)")
        return pass_token

    def clean_web(
        self,
        url: str,
        density: str = "standard",
        max_tokens: Optional[int] = None,
        agent_pass: Optional[str] = None,
        agent_nonce: Optional[str] = None
    ) -> Dict[str, Any]:
        """Scrapes and converts messy HTML to clean Markdown with token savings (0.01 USDC / 1 credit)."""
        params: Dict[str, Any] = {"url": url, "density": density}
        if max_tokens:
            params["max_tokens"] = max_tokens
        return self._execute_x402_request("/api/v1/clean-web", params=params, agent_pass=agent_pass, agent_nonce=agent_nonce)

    def batch_clean(
        self,
        urls: List[str],
        density: str = "standard",
        max_tokens_per_url: Optional[int] = None,
        agent_pass: Optional[str] = None,
        agent_nonce: Optional[str] = None
    ) -> Dict[str, Any]:
        """[Agent Swarm] Batch scrapes up to 10 URLs concurrently in 1 transaction (0.01 USDC / 1 credit per URL)."""
        payload: Dict[str, Any] = {"urls": urls, "density": density}
        if max_tokens_per_url:
            payload["max_tokens_per_url"] = max_tokens_per_url
        return self._execute_x402_request("/api/v1/batch-clean", json_body=payload, method="POST", agent_pass=agent_pass, agent_nonce=agent_nonce)

    def clean_youtube(self, url: str, language: str = "ko,en", agent_pass: Optional[str] = None, agent_nonce: Optional[str] = None) -> Dict[str, Any]:
        """Extracts complete YouTube video transcripts with timestamps (0.02 USDC / 2 credits)."""
        return self._execute_x402_request("/api/v1/clean-youtube", params={"url": url, "language": language}, agent_pass=agent_pass, agent_nonce=agent_nonce)

    def clean_pdf(self, url: str, agent_pass: Optional[str] = None, agent_nonce: Optional[str] = None) -> Dict[str, Any]:
        """Converts research papers and reports from PDF to structured Markdown (0.05 USDC / 5 credits)."""
        return self._execute_x402_request("/api/v1/clean-pdf", params={"url": url}, agent_pass=agent_pass, agent_nonce=agent_nonce)

    def clean_text(self, url: str, agent_pass: Optional[str] = None, agent_nonce: Optional[str] = None) -> Dict[str, Any]:
        """Extracts ultra-lightweight raw text for embedding and vector indexing (0.005 USDC / 1 credit)."""
        return self._execute_x402_request("/api/v1/clean-text", params={"url": url}, agent_pass=agent_pass, agent_nonce=agent_nonce)

    def extract_json(self, url: str, schema_description: str, agent_pass: Optional[str] = None, agent_nonce: Optional[str] = None) -> Dict[str, Any]:
        """Extracts structured JSON schema data from any webpage (0.03 USDC / 3 credits)."""
        payload = {"url": url, "schema_description": schema_description}
        return self._execute_x402_request("/api/v1/extract-json", json_body=payload, method="POST", agent_pass=agent_pass, agent_nonce=agent_nonce)

    def deep_research(self, query: str, max_sources: int = 3, agent_pass: Optional[str] = None, agent_nonce: Optional[str] = None) -> Dict[str, Any]:
        """Generates multi-source synthesized AI deep research briefings (0.15 USDC / 15 credits)."""
        return self._execute_x402_request("/api/v1/deep-research", params={"query": query, "max_sources": max_sources}, agent_pass=agent_pass, agent_nonce=agent_nonce)


if __name__ == "__main__":
    print("🤖 Autonomous x402 AI Agent SDK v2.0 initialized.")
    print("Example usage:")
    print("""
    from autonomous_agent_client import AutonomousX402Agent

    agent = AutonomousX402Agent(private_key="0xYOUR_AGENT_PRIVATE_KEY")
    
    # 1. Mint zero-latency credit pass
    pass_token = agent.mint_credit_pass(amount_usdc=1.0)
    
    # 2. Scrape with 0ms latency
    result = agent.clean_web("https://example.com/article", agent_pass=pass_token)
    print("Title:", result["title"])
    """)
