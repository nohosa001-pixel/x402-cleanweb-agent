"""
Agent Payment Vault Manager for CleanWeb Studio.
Maintains in-memory and SQLite-backed pre-funded agent USDC balances for zero-latency (<1ms) querying.
"""

import os
import time
import secrets
import threading
from typing import Dict, Any, Optional, Tuple, List
from web3 import Web3

from app.schemas import VaultBalanceResponse
from app.storage import storage_manager
from app.multi_chain import multi_chain_manager


class VaultManager:
    """Thread-safe and SQLite-backed manager for pre-funded agent payment vault accounts."""

    def __init__(self):
        self._lock = threading.Lock()
        self._seed_demo_account()

    def _seed_demo_account(self):
        demo_addr = Web3.to_checksum_address("0x70997970C51812dc3A010C7d01b50e0d17dc79C8")
        demo_key = "vault_key_demo_agent_sandbox_2026"
        existing = storage_manager.get_vault(demo_addr)
        if not existing:
            storage_manager.deposit_vault(demo_addr, 20.00, demo_key)

    def deposit(self, agent_address: str, amount_usdc: float, chain: str = "polygon", tx_hash: Optional[str] = None) -> Dict[str, Any]:
        """Deposits USDC into an agent's pre-funded vault balance."""
        if amount_usdc <= 0:
            raise ValueError("Deposit amount must be positive.")

        checksum_addr = Web3.to_checksum_address(agent_address)
        
        # If tx_hash is provided, verify on-chain transfer and check replay
        if tx_hash:
            if storage_manager.is_tx_used(tx_hash):
                raise ValueError("Transaction hash has already been used.")
            
            is_valid, reason, details = multi_chain_manager.verify_usdc_transfer(
                tx_hash=tx_hash,
                chain_identifier=chain,
                min_amount_usdc=amount_usdc
            )
            if not is_valid:
                raise ValueError(f"On-chain deposit verification failed: {reason}")
            
            # Record tx
            storage_manager.record_used_tx(tx_hash, chain, checksum_addr, amount_usdc)

        # Generate or retain session key
        existing = storage_manager.get_vault(checksum_addr)
        session_key = existing["session_key"] if existing and existing.get("session_key") else f"vault_key_{secrets.token_hex(16)}"
        
        updated_acc = storage_manager.deposit_vault(checksum_addr, amount_usdc, session_key)
        return updated_acc

    def deduct(self, identifier: str, amount_usdc: float) -> Tuple[bool, float, Optional[Dict[str, Any]]]:
        """
        Deducts cost from pre-funded vault balance using either agent_address or session_key.
        Returns (success, remaining_balance, account_dict).
        """
        vault = storage_manager.get_vault(identifier)
        if not vault:
            return False, 0.0, None
        
        addr = vault["agent_address"]
        return storage_manager.deduct_vault(addr, amount_usdc)

    def get_balance(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieves vault account details by agent address or session key."""
        return storage_manager.get_vault(identifier)

    def to_response(self, acc_dict: Dict[str, Any]) -> VaultBalanceResponse:
        last_act = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(acc_dict.get("last_active", time.time())))
        return VaultBalanceResponse(
            agent_address=Web3.to_checksum_address(acc_dict["agent_address"]),
            balance_usdc=round(float(acc_dict["balance_usdc"]), 6),
            total_deposited_usdc=round(float(acc_dict["total_deposited"]), 6),
            total_consumed_usdc=round(float(acc_dict["total_consumed"]), 6),
            session_key=acc_dict["session_key"],
            last_active_utc=last_act,
            query_count=int(acc_dict.get("query_count", 0)),
        )


vault_manager = VaultManager()
