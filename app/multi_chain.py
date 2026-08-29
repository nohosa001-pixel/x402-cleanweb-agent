"""
Multi-Chain Network Registry and Transaction Verifier.
Supports Polygon (137), Base (8453), and Arbitrum One (42161) Native USDC micro-settlements.
"""

import os
import re
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
            "https://rpc.ankr.com/polygon"
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
            "https://1rpc.io/base"
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
            "https://1rpc.io/arb"
        ],
        explorer_url="https://arbiscan.io",
        decimals=6
    ),
}

# ERC-20 Transfer Event Signature: Transfer(address,address,uint256)
TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


class MultiChainManager:
    """Manages Web3 connections and cross-chain USDC verification across Polygon, Base, and Arbitrum."""

    def __init__(self):
        self.default_recipient = safe_checksum(
            os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")
        )

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

    def get_web3_for_chain(self, chain_identifier: Any) -> Tuple[Web3, ChainConfig]:
        cfg = self.get_chain_config(chain_identifier)
        for rpc in cfg.rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 8}))
                if w3.is_connected():
                    return w3, cfg
            except Exception:
                continue
        # Fallback to first RPC
        return Web3(Web3.HTTPProvider(cfg.rpc_urls[0])), cfg

    def verify_usdc_transfer(
        self,
        tx_hash: str,
        chain_identifier: Any = "polygon",
        expected_recipient: Optional[str] = None,
        min_amount_usdc: float = 0.001
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Verifies on-chain ERC-20 USDC Transfer event for a given transaction hash.
        Returns (is_valid, reason, details_dict).
        """
        target_recipient = safe_checksum(expected_recipient or self.default_recipient)
        
        # Clean tx_hash
        tx_hash = tx_hash.strip()
        if not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
            return False, "Invalid transaction hash format. Must be 0x followed by 64 hex characters.", None

        w3, cfg = self.get_web3_for_chain(chain_identifier)
        
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if not receipt:
                return False, f"Transaction not yet mined or not found on {cfg.display_name}.", None

            if receipt.get("status") != 1:
                return False, f"Transaction reverted on {cfg.display_name}.", None

            # Parse logs for ERC20 Transfer to target_recipient
            usdc_contract_lower = cfg.usdc_address.lower()
            target_topic_addr = "0x" + target_recipient.lower().replace("0x", "").zfill(64)

            transferred_amount_usdc = 0.0
            payer_addr = None

            for log in receipt.get("logs", []):
                # Verify token address matches canonical USDC
                log_addr = log.get("address", "").lower()
                if log_addr != usdc_contract_lower:
                    continue

                topics = log.get("topics", [])
                if not topics or len(topics) < 3:
                    continue

                topic_0 = topics[0].hex().lower() if hasattr(topics[0], "hex") else str(topics[0]).lower()
                if topic_0 != TRANSFER_EVENT_TOPIC:
                    continue

                # Topic 1: from, Topic 2: to
                topic_2 = topics[2].hex().lower() if hasattr(topics[2], "hex") else str(topics[2]).lower()
                if topic_2 == target_topic_addr.lower():
                    # Matched recipient
                    raw_data = log.get("data", "0x0")
                    if hasattr(raw_data, "hex"):
                        raw_data = raw_data.hex()
                    
                    raw_int = int(raw_data, 16) if isinstance(raw_data, str) else int(raw_data)
                    amount_usdc = raw_int / (10 ** cfg.decimals)
                    transferred_amount_usdc += amount_usdc

                    # Extract sender
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

        except Exception as e:
            return False, f"RPC Verification error on {cfg.display_name}: {str(e)}", None


multi_chain_manager = MultiChainManager()
