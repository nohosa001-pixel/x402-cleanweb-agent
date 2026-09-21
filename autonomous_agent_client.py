"""
Autonomous AI Agent x402 Client SDK
--------------------------------------------------------------------------------
Zero-Human-in-the-Loop Web3 Data Scraper for Autonomous AI Agents.
Enables AI agents with a Polygon wallet (Private Key) to autonomously handle
HTTP 402 Payment Required flows, transfer USDC on-chain, and fetch LLM-ready data.
"""

import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

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

SUPPORTED_CHAINS: Dict[str, Dict[str, Any]] = {
    "polygon": {
        "chain_id": 137,
        "usdc": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
        "rpcs": [
            "https://polygon-bor-rpc.publicnode.com",
            "https://polygon.llamarpc.com",
            "https://1rpc.io/matic",
            "https://rpc.ankr.com/polygon"
        ]
    },
    "base": {
        "chain_id": 8453,
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "rpcs": [
            "https://mainnet.base.org",
            "https://base.llamarpc.com",
            "https://1rpc.io/base"
        ]
    },
    "arbitrum": {
        "chain_id": 42161,
        "usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "rpcs": [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum.llamarpc.com",
            "https://1rpc.io/arb"
        ]
    }
}

DEFAULT_RPC_URLS = SUPPORTED_CHAINS["polygon"]["rpcs"]


class AutonomousX402Agent:
    """
    Autonomous Web3 AI Agent Client for x402 Protocol on Multi-Chain (Polygon, Base, Arbitrum).
    
    Usage:
        agent = AutonomousX402Agent(private_key="0x...", default_chain="polygon", auto_refill=True)
        result = agent.clean_web("https://example.com/article")
        print(result["markdown_content"])
    """

    def __init__(
        self,
        private_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        rpc_url: Optional[str] = None,
        vault_key: Optional[str] = None,
        default_chain: str = "polygon",
        auto_refill: bool = False,
        auto_refill_threshold_usdc: float = 0.5
    ):
        self.private_key = private_key or os.getenv("AGENT_PRIVATE_KEY")
        self.base_url = base_url.rstrip("/")
        self.vault_key = vault_key or os.getenv("AGENT_VAULT_KEY")
        self.default_chain = default_chain.lower()
        self.auto_refill = auto_refill
        self.auto_refill_threshold_usdc = auto_refill_threshold_usdc
        self.session = requests.Session()
        
        # Web3 Providers cache per chain
        self._w3_cache: Dict[str, Web3] = {}
        self.w3 = self._init_web3(self.default_chain, rpc_url)
        
        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)
            self.wallet_address = self.account.address
        else:
            self.account = None
            self.wallet_address = None
        self.default_nonce = f"agent_session_{int(time.time() * 1000)}"

    def _init_web3(self, chain: str = "polygon", rpc_url: Optional[str] = None) -> Web3:
        chain_key = chain.lower()
        if chain_key in self._w3_cache and not rpc_url:
            return self._w3_cache[chain_key]

        chain_info = SUPPORTED_CHAINS.get(chain_key, SUPPORTED_CHAINS["polygon"])
        urls = [rpc_url] + chain_info["rpcs"] if rpc_url else chain_info["rpcs"]
        
        for url in urls:
            if not url:
                continue
            try:
                w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 10}))
                if w3.is_connected():
                    self._w3_cache[chain_key] = w3
                    return w3
            except Exception:
                continue
        w3_fallback = Web3(Web3.HTTPProvider(chain_info["rpcs"][0]))
        self._w3_cache[chain_key] = w3_fallback
        return w3_fallback

    def _pay_and_get_tx_hash(self, x402_info: Dict[str, Any], chain: Optional[str] = None) -> str:
        """Executes on-chain USDC transfer based on 402 instructions on Polygon, Base, or Arbitrum."""
        if not self.account:
            raise ValueError(
                "Agent private key is required to execute on-chain micropayments. "
                "Set AGENT_PRIVATE_KEY env var or pass private_key to AutonomousX402Agent()."
            )

        # Resolve chain
        target_chain = (chain or x402_info.get("chain") or self.default_chain).lower()
        chain_info = SUPPORTED_CHAINS.get(target_chain, SUPPORTED_CHAINS["polygon"])
        chain_id = int(x402_info.get("chain_id") or chain_info["chain_id"])

        w3_instance = self._init_web3(target_chain)
        token_contract_addr = Web3.to_checksum_address(x402_info.get("token_contract") or chain_info["usdc"])
        recipient_addr = Web3.to_checksum_address(x402_info["recipient"])
        amount_raw = int(x402_info["amount_raw"])

        token_contract = w3_instance.eth.contract(address=token_contract_addr, abi=ERC20_ABI)
        nonce = w3_instance.eth.get_transaction_count(self.wallet_address, "pending")
        gas_price = w3_instance.eth.gas_price

        # Build ERC20 Transfer transaction
        tx = token_contract.functions.transfer(
            recipient_addr,
            amount_raw
        ).build_transaction({
            "from": self.wallet_address,
            "nonce": nonce,
            "gas": 90000,
            "gasPrice": int(gas_price * 1.2),  # +20% for fast inclusion
            "chainId": chain_id
        })

        # Sign & Send
        signed_tx = w3_instance.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = w3_instance.eth.send_raw_transaction(signed_tx.raw_transaction).hex()
        
        # Wait for receipt
        receipt = w3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt.get("status") != 1:
            raise RuntimeError(f"USDC Transfer reverted on-chain on {target_chain}: {tx_hash}")

        return tx_hash

    def _execute_x402_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        agent_pass: Optional[str] = None,
        agent_nonce: Optional[str] = None,
        vault_key: Optional[str] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {}
        active_vault_key = vault_key or self.vault_key
        if active_vault_key:
            headers["X-Vault-Key"] = active_vault_key
        elif not self.account:
            headers["X-Agent-Nonce"] = agent_nonce or self.default_nonce
        if agent_pass:
            headers["X-Agent-Pass"] = agent_pass
        if agent_nonce:
            headers["X-Agent-Nonce"] = agent_nonce

        # 1. Initial Request
        if method == "POST":
            res = self.session.post(url, params=params, json=json_body, headers=headers)
        else:
            res = self.session.get(url, params=params, headers=headers)

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
            chain_name = x402_info.get("chain", self.default_chain)

            # Auto-Refill Guard Trigger: If agent has auto_refill enabled and wallet has balance
            if self.auto_refill and self.account:
                print(f"[x402 AutoRefill] 402 intercepted. Auto-refilling vault with 2.0 USDC on {chain_name}...")
                try:
                    new_vault_key = self.deposit_vault(amount_usdc=2.0, chain=chain_name)
                    headers["X-Vault-Key"] = new_vault_key
                    if method == "POST":
                        retried = self.session.post(url, params=params, json=json_body, headers=headers)
                    else:
                        retried = self.session.get(url, params=params, headers=headers)
                    if retried.status_code == 200:
                        print("[x402 AutoRefill] Success! Vault refilled and query served seamlessly.")
                        return retried.json()
                except Exception as refill_err:
                    print(f"[x402 AutoRefill] Refill attempt failed: {refill_err}. Falling back to direct tx...")

            print(f"[x402 Agent] 402 Payment Required: {required_usdc} USDC on {chain_name}.")
            if suggested_action:
                print(f"[x402 Agent Action]: {suggested_action}")
            print(f"[x402 Agent] Paying from agent wallet: {self.wallet_address}...")

            # 2. Autonomous On-Chain Payment
            tx_hash = self._pay_and_get_tx_hash(x402_info, chain=chain_name)
            print(f"[x402 Agent] On-chain payment confirmed! Tx: {tx_hash}")

            # 3. Re-request with X-Payment-Tx Header
            headers["X-Payment-Tx"] = tx_hash
            headers["X-Chain"] = chain_name
            if method == "POST":
                paid_res = self.session.post(url, params=params, json=json_body, headers=headers)
            else:
                paid_res = self.session.get(url, params=params, headers=headers)

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

    def deposit_vault(self, amount_usdc: float = 2.0, chain: Optional[str] = None) -> str:
        """
        [Zero-Latency Agent Vault] Pre-funds Agent Vault on-chain:
        Deposits 2.0+ USDC to recipient_wallet on Polygon, Base, or Arbitrum,
        verifies on-chain, and receives X-Vault-Key.
        Returns the session_key (vault_key) for zero-gas, sub-1ms requests.
        """
        if amount_usdc < 2.0:
            raise ValueError("Minimum deposit is 2.0 USDC.")

        target_chain = (chain or self.default_chain).lower()
        chain_info = SUPPORTED_CHAINS.get(target_chain, SUPPORTED_CHAINS["polygon"])
        raw_amount = int(amount_usdc * 10**6)

        x402_info = {
            "chain": target_chain,
            "chain_id": chain_info["chain_id"],
            "token_contract": chain_info["usdc"],
            "recipient": "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf",
            "amount_raw": str(raw_amount)
        }
        print(f"[x402 Agent] Depositing {amount_usdc} USDC into Agent Vault on {target_chain}...")
        tx_hash = self._pay_and_get_tx_hash(x402_info, chain=target_chain)
        
        payload = {
            "agent_address": self.wallet_address,
            "amount_usdc": amount_usdc,
            "chain": target_chain,
            "tx_hash": tx_hash
        }

        dep_res = requests.post(f"{self.base_url}/api/v1/vault/deposit", json=payload)
        dep_res.raise_for_status()
        data = dep_res.json()
        vault_key = data["session_key"]
        self.vault_key = vault_key
        print(f"[x402 Agent] Vault funded successfully! Balance: {data['balance_usdc']} USDC, Key: {vault_key}")
        return vault_key

    def mint_credit_pass(self, amount_usdc: float = 2.0, referral_wallet: Optional[str] = None) -> str:
        """Compatibility alias for deposit_vault."""
        return self.deposit_vault(amount_usdc=amount_usdc)

    def clean_web(
        self,
        url: str,
        density: str = "standard",
        max_tokens: Optional[int] = None,
        respect_robots_txt: bool = False,
        agent_pass: Optional[str] = None,
        agent_nonce: Optional[str] = None
    ) -> Dict[str, Any]:
        """Scrapes and converts messy HTML to clean Markdown with token savings (0.001 USDC / 1 credit)."""
        params: Dict[str, Any] = {"url": url, "density": density}
        if max_tokens:
            params["max_tokens"] = max_tokens
        if respect_robots_txt:
            params["respect_robots_txt"] = "true"
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

    def map_site(self, url: str, max_links: int = 50, agent_pass: Optional[str] = None, agent_nonce: Optional[str] = None) -> Dict[str, Any]:
        """Discovers domain sitemap or internal URL tree (0.002 USDC / 2 credits). Firecrawl /map equivalent."""
        return self._execute_x402_request("/api/v1/map-site", params={"url": url, "max_links": max_links}, agent_pass=agent_pass, agent_nonce=agent_nonce)

    def search(self, query: str, max_results: int = 5, agent_pass: Optional[str] = None, agent_nonce: Optional[str] = None) -> Dict[str, Any]:
        """Executes fast real-time keyword web search returning snippets (0.002 USDC / 2 credits). Tavily equivalent."""
        return self._execute_x402_request("/api/v1/search", params={"query": query, "max_results": max_results}, agent_pass=agent_pass, agent_nonce=agent_nonce)

    def oracle_grounding(
        self,
        query: str,
        target_schema: Optional[Dict[str, Any]] = None,
        max_sources: int = 3,
        secure_audit: bool = False,
        agent_pass: Optional[str] = None,
        agent_nonce: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        [B2A Web3 Signed Oracle Grounding] (0.035 USDC / 0.040 USDC with Security Gate audit)
        Executes real-time search, noise-free extraction, Gemini 3.6 Flash JSON structuring,
        and returns on-chain verifiable EIP-712 attestation.
        """
        payload: Dict[str, Any] = {
            "query": query,
            "max_sources": max_sources,
            "secure_audit": secure_audit
        }
        if target_schema:
            payload["target_schema"] = target_schema
        return self._execute_x402_request("/api/v1/oracle/grounding", json_body=payload, method="POST", agent_pass=agent_pass, agent_nonce=agent_nonce)

    def verify_oracle_attestation(
        self,
        query: str,
        data_hash: str,
        timestamp: int,
        signature: str
    ) -> Dict[str, Any]:
        """Verifies an EIP-712 signed Oracle attestation via CleanWeb verification endpoint."""
        payload = {
            "data_hash": data_hash,
            "timestamp": timestamp,
            "signature": signature
        }
        res = self.session.post(f"{self.base_url}/api/v1/oracle/verify", params={"query": query}, json=payload)
        res.raise_for_status()
        return res.json()

    def verify_attestation_offline(
        self,
        query: str,
        data_hash: str,
        timestamp: int,
        signature: str,
        expected_signer: Optional[str] = None,
        contract_address: Optional[str] = None,
        chain_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        [Zero-Cost Local EIP-712 Verification]
        Verifies the cryptographic signature entirely off-chain in agent local memory without API or gas costs.
        """
        try:
            from eth_account.messages import encode_typed_data
            clean_hash = ("0x" + data_hash) if not data_hash.startswith("0x") else data_hash
            hash_bytes = bytes.fromhex(clean_hash.replace("0x", "").zfill(64))

            target_chain_id = int(chain_id or os.getenv("POLYGON_CHAIN_ID", os.getenv("CHAIN_ID", "137")))
            target_contract = contract_address or os.getenv(
                "CLEANWEB_ORACLE_CONTRACT_ADDRESS",
                "0xAECbfBc171F522c35985AABa2FA1F9881A046D66"
            )

            structured_data = {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"},
                    ],
                    "CleanWebOracleFeed": [
                        {"name": "query", "type": "string"},
                        {"name": "dataHash", "type": "bytes32"},
                        {"name": "timestamp", "type": "uint256"},
                    ],
                },
                "primaryType": "CleanWebOracleFeed",
                "domain": {
                    "name": "CleanWebOracle",
                    "version": "1.0.0",
                    "chainId": target_chain_id,
                    "verifyingContract": Web3.to_checksum_address(target_contract),
                },
                "message": {
                    "query": query,
                    "dataHash": hash_bytes,
                    "timestamp": timestamp,
                },
            }

            encoded = encode_typed_data(full_message=structured_data)
            recovered = self.w3.eth.account.recover_message(encoded, signature=signature)
            target_expected = expected_signer or "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf"

            is_valid = recovered.lower() == target_expected.lower()
            return {
                "valid": is_valid,
                "recovered_signer": recovered,
                "expected_signer": target_expected,
                "timestamp": timestamp,
                "verification_method": "local_offline_eip712"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "verification_method": "local_offline_eip712"
            }

    def get_legal_terms(self) -> Dict[str, Any]:
        """[Compliance] Retrieves machine-readable B2A terms of service, TDM fair use doctrine, and GDPR policies."""
        res = self.session.get(f"{self.base_url}/api/v1/legal/terms")
        res.raise_for_status()
        return res.json()

    def get_legal_disclaimer(self) -> Dict[str, Any]:
        """[Compliance] Retrieves AS-IS financial & smart-contract liability disclaimer."""
        res = self.session.get(f"{self.base_url}/api/v1/legal/disclaimer")
        res.raise_for_status()
        return res.json()

    def get_service_health(self, deep: bool = False) -> Dict[str, Any]:
        """[Telemetry] Checks service health, storage stats, and connected EVM chains."""
        res = self.session.get(f"{self.base_url}/health", params={"deep": deep})
        res.raise_for_status()
        return res.json()


if __name__ == "__main__":
    print("🤖 Autonomous x402 AI Agent SDK v2.0 initialized.")
    print("Example usage:")
    print("""
    from autonomous_agent_client import AutonomousX402Agent

    agent = AutonomousX402Agent(private_key="0xYOUR_AGENT_PRIVATE_KEY")
    
    # 1. Mint zero-latency credit pass (2.0 USDC minimum)
    pass_token = agent.mint_credit_pass(amount_usdc=2.0)
    
    # 2. Scrape with 0ms latency
    result = agent.clean_web("https://example.com/article", agent_pass=pass_token)
    print("Title:", result["title"])
    """)
