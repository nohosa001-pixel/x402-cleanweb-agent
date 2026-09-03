"""
Multi-Chain Network Registry and Transaction Verifier with Robust Multi-RPC Failover Pool.
Supports Polygon (137), Base (8453), and Arbitrum One (42161) Native USDC micro-settlements.
"""

import os
import re
import time
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from pydantic import BaseModel
from web3 import Web3


class SupportedChain(str, Enum):
    POLYGON = "polygon"      # Chain ID 137
    BASE = "base"            # Chain ID 8453 (Coinbase L2)
    ARBITRUM = "arbitrum"    # Chain ID 42161 (Arbitrum One)


class ChainConfig(BaseModel):
    chain_name: str
    chain_id: int
    display_name: str
    usdc_address: str
    rpc_urls: List[str]
    explorer_url: str
    permit2_address: str = "0x000000000022D473030F116dDEE9F6B43aC78BA3"
    decimals: int = 6


def safe_checksum(addr: str) -> str:
    try:
        return Web3.to_checksum_address(addr)
    except Exception:
        return addr


CHAIN_REGISTRY: Dict[str, ChainConfig] = {
    SupportedChain.POLYGON.value: ChainConfig(
        chain_name="polygon",
        chain_id=137,
        display_name="Polygon Mainnet",
        usdc_address=safe_checksum(os.getenv("USDC_CONTRACT_ADDRESS", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")),
        rpc_urls=[
            os.getenv("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com"),
            "https://polygon.llamarpc.com",
            "https://1rpc.io/matic",
            "https://rpc.ankr.com/polygon",
            "https://polygon-rpc.com"
        ],
        explorer_url="https://polygonscan.com",
        decimals=6
    ),
    SupportedChain.BASE.value: ChainConfig(
        chain_name="base",
        chain_id=8453,
        display_name="Base (Coinbase L2)",
        usdc_address=safe_checksum("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
        rpc_urls=[
            "https://mainnet.base.org",
            "https://base.llamarpc.com",
            "https://1rpc.io/base",
            "https://base-rpc.publicnode.com",
            "https://rpc.ankr.com/base"
        ],
        explorer_url="https://basescan.org",
        decimals=6
    ),
    SupportedChain.ARBITRUM.value: ChainConfig(
        chain_name="arbitrum",
        chain_id=42161,
        display_name="Arbitrum One",
        usdc_address=safe_checksum("0xaf88d065e77c8cC2239327C5EDb3A432268e5831"),
        rpc_urls=[
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum.llamarpc.com",
            "https://1rpc.io/arb",
            "https://arbitrum-one-rpc.publicnode.com",
            "https://rpc.ankr.com/arbitrum"
        ],
        explorer_url="https://arbiscan.io",
        decimals=6
    ),
}

# ERC-20 Transfer Event Signature: Transfer(address,address,uint256)
TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


class MultiChainManager:
    """Manages resilient Web3 connections and cross-chain USDC verification with multi-RPC failover."""

    def __init__(self):
        self.default_recipient = safe_checksum(
            os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")
        )
        self._rpc_latencies: Dict[str, float] = {}

    def get_chain_config(self, chain_identifier: Any) -> ChainConfig:
        if isinstance(chain_identifier, int) or (isinstance(chain_identifier, str) and chain_identifier.isdigit()):
            c_id = int(chain_identifier)
            for cfg in CHAIN_REGISTRY.values():
                if cfg.chain_id == c_id:
                    return cfg
        c_str = str(chain_identifier).lower()
        if c_str in CHAIN_REGISTRY:
            return CHAIN_REGISTRY[c_str]
        return CHAIN_REGISTRY[SupportedChain.POLYGON.value]

    def get_healthy_web3(self, chain_identifier: Any) -> Tuple[Web3, ChainConfig, str]:
        """Iterates through RPC failover pool and returns the first responsive Web3 connection."""
        cfg = self.get_chain_config(chain_identifier)
        for rpc in cfg.rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 6}))
                if w3.is_connected():
                    return w3, cfg, rpc
            except Exception:
                continue
        # Fallback default
        return Web3(Web3.HTTPProvider(cfg.rpc_urls[0])), cfg, cfg.rpc_urls[0]

    def ping_all_chains(self) -> Dict[str, Any]:
        """Pings all chains and returns latency metrics and block heights."""
        results = {}
        for chain_key, cfg in CHAIN_REGISTRY.items():
            start_t = time.time()
            try:
                w3, _, active_rpc = self.get_healthy_web3(chain_key)
                block_num = w3.eth.block_number
                lat_ms = round((time.time() - start_t) * 1000, 2)
                results[chain_key] = {
                    "status": "healthy",
                    "chain_id": cfg.chain_id,
                    "display_name": cfg.display_name,
                    "active_rpc": active_rpc,
                    "latest_block": block_num,
                    "latency_ms": lat_ms
                }
            except Exception as e:
                results[chain_key] = {
                    "status": "degraded",
                    "chain_id": cfg.chain_id,
                    "error": str(e)
                }
        return results

    def verify_usdc_transfer(
        self,
        tx_hash: str,
        chain_identifier: Any = "polygon",
        expected_recipient: Optional[str] = None,
        min_amount_usdc: float = 0.001
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Verifies on-chain ERC-20 USDC Transfer event for a given transaction hash.
        Includes automatic RPC failover if the primary RPC times out.
        """
        target_recipient = safe_checksum(expected_recipient or self.default_recipient)
        
        tx_hash = tx_hash.strip()
        if not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
            return False, "Invalid transaction hash format. Must be 0x followed by 64 hex characters.", None

        cfg = self.get_chain_config(chain_identifier)
        receipt = None
        last_err = None

        # Multi-RPC Failover Loop
        for rpc in cfg.rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 6}))
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                if receipt:
                    break
            except Exception as e:
                last_err = e
                continue

        if not receipt:
            return False, f"Transaction not yet mined or not found on {cfg.display_name} (Last error: {last_err}).", None

        if receipt.get("status") != 1:
            return False, f"Transaction reverted on {cfg.display_name}.", None

        # Parse logs for ERC20 Transfer to target_recipient
        usdc_contract_lower = cfg.usdc_address.lower()
        target_topic_addr = "0x" + target_recipient.lower().replace("0x", "").zfill(64)

        transferred_amount_usdc = 0.0
        payer_addr = None

        for log in receipt.get("logs", []):
            log_addr = log.get("address", "").lower()
            if log_addr != usdc_contract_lower:
                continue

            topics = log.get("topics", [])
            if not topics or len(topics) < 3:
                continue

            topic_0 = topics[0].hex().lower() if hasattr(topics[0], "hex") else str(topics[0]).lower()
            if topic_0 != TRANSFER_EVENT_TOPIC:
                continue

            # Topic 2: to
            topic_2 = topics[2].hex().lower() if hasattr(topics[2], "hex") else str(topics[2]).lower()
            if topic_2 == target_topic_addr.lower():
                raw_data = log.get("data", "0x0")
                if hasattr(raw_data, "hex"):
                    raw_data = raw_data.hex()
                
                raw_int = int(raw_data, 16) if isinstance(raw_data, str) else int(raw_data)
                amount_usdc = raw_int / (10 ** cfg.decimals)
                transferred_amount_usdc += amount_usdc

                topic_1 = topics[1].hex().lower() if hasattr(topics[1], "hex") else str(topics[1]).lower()
                payer_addr = safe_checksum("0x" + topic_1[-40:])

        if transferred_amount_usdc < min_amount_usdc:
            return False, (
                f"Insufficient USDC transferred. Found {transferred_amount_usdc:.4f} USDC, "
                f"expected at least {min_amount_usdc:.4f} USDC to {target_recipient} on {cfg.display_name}."
            ), None

        details = {
            "chain": cfg.chain_name,
            "chain_id": cfg.chain_id,
            "tx_hash": tx_hash,
            "payer": payer_addr or receipt.get("from"),
            "recipient": target_recipient,
            "amount_usdc": transferred_amount_usdc,
            "block_number": receipt.get("blockNumber")
        }
        return True, "USDC Payment verified successfully.", details

    def get_chain_balances(self, chain_identifier: Any, wallet_address: Optional[str] = None) -> Dict[str, Any]:
        """Fetches live on-chain Native and USDC balances for a wallet on a specified chain."""
        target_addr = safe_checksum(wallet_address or self.default_recipient)
        cfg = self.get_chain_config(chain_identifier)
        
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            }
        ]

        native_bal = 0.0
        usdc_bal = 0.0
        block_num = None
        last_rpc_used = None

        for rpc in cfg.rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 4}))
                if not w3.is_connected():
                    continue
                
                # Fetch Native Coin Balance
                raw_native = w3.eth.get_balance(target_addr)
                native_bal = float(Web3.from_wei(raw_native, "ether"))

                # Fetch ERC20 USDC Balance
                usdc_contract = w3.eth.contract(address=cfg.usdc_address, abi=erc20_abi)
                raw_usdc = usdc_contract.functions.balanceOf(target_addr).call()
                usdc_bal = float(raw_usdc) / (10 ** cfg.decimals)

                block_num = w3.eth.block_number
                last_rpc_used = rpc
                break
            except Exception:
                continue

        return {
            "chain": cfg.chain_name,
            "chain_id": cfg.chain_id,
            "display_name": cfg.display_name,
            "wallet_address": target_addr,
            "usdc_balance": round(usdc_bal, 4),
            "native_balance": round(native_bal, 6),
            "native_symbol": "MATIC" if cfg.chain_id == 137 else "ETH",
            "block_number": block_num,
            "rpc_node": last_rpc_used
        }

    def get_multi_chain_treasury_summary(self, wallet_address: Optional[str] = None) -> Dict[str, Any]:
        """Aggregates real-time on-chain USDC treasury balances across all 3 supported chains."""
        target_addr = safe_checksum(wallet_address or self.default_recipient)
        chains_data = {}
        total_usdc = 0.0

        for chain_key in [SupportedChain.POLYGON.value, SupportedChain.BASE.value, SupportedChain.ARBITRUM.value]:
            info = self.get_chain_balances(chain_key, target_addr)
            chains_data[chain_key] = info
            total_usdc += info.get("usdc_balance", 0.0)

        return {
            "treasury_wallet": target_addr,
            "total_usdc_accumulated": round(total_usdc, 4),
            "networks": chains_data,
            "timestamp": int(time.time()),
            "status": "HEALTHY_ONLINE"
        }


multi_chain_manager = MultiChainManager()

