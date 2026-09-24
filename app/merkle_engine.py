"""
Cryptographic Merkle Tree Engine for CleanWeb Studio Treasury & Settlement Ledger.
Constructs binary Merkle trees using standard Keccak-256 (SHA3) hashes over settled transactions,
generating Merkle Roots and audit inclusion proofs for autonomous agent verification.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from web3 import Web3


def keccak256_hex(data: bytes) -> str:
    """Computes Keccak-256 hash and returns 0x-prefixed hex string."""
    h = Web3.keccak(data).hex()
    return h if h.startswith("0x") else f"0x{h}"


def compute_tx_leaf(tx_hash: str, chain: str, agent_address: str, amount_usdc: float, timestamp: int) -> str:
    """
    Deterministically computes a 32-byte Merkle leaf for a settled transaction.
    Leaf = Keccak256(tx_hash || chain || agent_address.lower() || amount_usdc_int_micro || timestamp)
    """
    norm_tx = tx_hash.strip().lower()
    norm_chain = chain.strip().lower()
    norm_agent = agent_address.strip().lower()
    amount_int = int(round(amount_usdc * 1_000_000))
    
    payload = f"{norm_tx}:{norm_chain}:{norm_agent}:{amount_int}:{timestamp}".encode("utf-8")
    return keccak256_hex(payload)


class MerkleTreeEngine:
    """
    Deterministic binary Merkle tree implementation with Keccak-256 hashing.
    Supports root generation, audit proof generation, and verification.
    """

    def __init__(self):
        pass

    @staticmethod
    def _hash_pair(left: str, right: str) -> str:
        """Hashes two 32-byte hex nodes in canonical sorted order to avoid 2nd preimage attacks."""
        left_clean = left[2:] if left.startswith("0x") else left
        right_clean = right[2:] if right.startswith("0x") else right
        left_bytes = bytes.fromhex(left_clean)
        right_bytes = bytes.fromhex(right_clean)
        
        # Sort canonically (Ethereum standard)
        if left_bytes > right_bytes:
            left_bytes, right_bytes = right_bytes, left_bytes
            
        return keccak256_hex(left_bytes + right_bytes)

    def build_tree(self, leaves: List[str]) -> Tuple[str, List[List[str]]]:
        """
        Builds Merkle tree levels from list of leaf hex strings.
        Returns (merkle_root, levels).
        """
        if not leaves:
            empty_root = keccak256_hex(b"EMPTY_CLEANWEB_MERKLE_TREE")
            return empty_root, [[]]

        # Clean 0x prefixes
        current_level = [l if l.startswith("0x") else f"0x{l}" for l in leaves]
        levels = [current_level]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    # Duplicate last node if odd number of leaves (standard Bitcoin/Ethereum practice)
                    right = current_level[i]
                next_level.append(self._hash_pair(left, right))
            levels.append(next_level)
            current_level = next_level

        merkle_root = levels[-1][0]
        return merkle_root, levels

    def get_proof(self, target_leaf: str, leaves: List[str]) -> List[Dict[str, str]]:
        """
        Generates inclusion audit proof for a target leaf against the provided leaves list.
        Returns list of {'position': 'left'|'right', 'data': '0x...'}
        """
        if not leaves:
            return []

        norm_target = target_leaf if target_leaf.startswith("0x") else f"0x{target_leaf}"
        current_leaves = [l if l.startswith("0x") else f"0x{l}" for l in leaves]

        if norm_target not in current_leaves:
            return []

        index = current_leaves.index(norm_target)
        proof: List[Dict[str, str]] = []

        _, levels = self.build_tree(current_leaves)

        for level in levels[:-1]:
            is_right_node = (index % 2 == 1)
            pair_index = index - 1 if is_right_node else index + 1
            
            if pair_index < len(level):
                sibling = level[pair_index]
            else:
                sibling = level[index]  # odd duplicate

            position = "left" if is_right_node else "right"
            proof.append({"position": position, "data": sibling})
            index = index // 2

        return proof

    def verify_proof(self, target_leaf: str, proof: List[Dict[str, str]], root: str) -> bool:
        """
        Verifies inclusion proof for a target leaf against the root.
        """
        current = target_leaf if target_leaf.startswith("0x") else f"0x{target_leaf}"
        expected_root = root if root.startswith("0x") else f"0x{root}"

        for p in proof:
            sibling = p["data"]
            current = self._hash_pair(current, sibling)

        return current.lower() == expected_root.lower()


merkle_engine = MerkleTreeEngine()
