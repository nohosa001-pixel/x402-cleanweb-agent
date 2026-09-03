"""
On-Chain EIP-712 Cryptographic Signer and Web3 Calldata Relay Engine for CleanWeb Studio.
Produces EIP-712 typed data signatures (v, r, s) and ABI-encoded calldata for CleanWebOracleConsumer.sol on Polygon/Base/Arbitrum.
"""

import os
import time
import hashlib
from typing import Dict, Any, Optional, Tuple

from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3
from dotenv import load_dotenv

from app.schemas import OnChainProof

load_dotenv()

POLYGON_CHAIN_ID = int(os.getenv("POLYGON_CHAIN_ID", os.getenv("CHAIN_ID", "137")))
CLEANWEB_CONTRACT_ADDRESS = os.getenv(
    "CLEANWEB_ORACLE_CONTRACT_ADDRESS",
    "0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7"
)
ORACLE_SIGNER_PRIVATE_KEY = os.getenv(
    "ORACLE_SIGNER_PRIVATE_KEY",
    # Safe default for local/sandbox development: Hardhat Account #0
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)


class OnChainCleanWebSigner:
    """
    Cryptographic signer for CleanWeb verified data attestation.
    Produces EIP-712 typed data signatures (v, r, s) and ABI-encoded calldata.
    """

    def __init__(
        self,
        private_key: str = ORACLE_SIGNER_PRIVATE_KEY,
        chain_id: int = POLYGON_CHAIN_ID,
        contract_address: str = CLEANWEB_CONTRACT_ADDRESS,
    ):
        self.chain_id = chain_id
        try:
            self.contract_address = Web3.to_checksum_address(contract_address)
        except Exception:
            self.contract_address = Web3.to_checksum_address("0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7")
        self.account = Account.from_key(private_key)
        self.signer_address = self.account.address

    def get_domain_data(self) -> Dict[str, Any]:
        """Returns the EIP-712 domain separator matching CleanWebOracleConsumer.sol."""
        return {
            "name": "CleanWebOracle",
            "version": "1.0.0",
            "chainId": self.chain_id,
            "verifyingContract": self.contract_address,
        }

    def sign_cleanweb_attestation(
        self,
        target_url: str,
        content_text: str,
        timestamp: Optional[int] = None,
    ) -> OnChainProof:
        """
        Signs a CleanWeb content attestation and constructs ABI calldata.
        """
        ts = timestamp or int(time.time())
        # keccak256 hash of UTF-8 content
        raw_hash = Web3.keccak(text=content_text).hex()
        content_hash = ("0x" + raw_hash) if not raw_hash.startswith("0x") else raw_hash

        # EIP-712 Structured Data definition
        structured_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "CleanWebAttestation": [
                    {"name": "targetUrl", "type": "string"},
                    {"name": "contentHash", "type": "bytes32"},
                    {"name": "timestamp", "type": "uint256"},
                ],
            },
            "primaryType": "CleanWebAttestation",
            "domain": self.get_domain_data(),
            "message": {
                "targetUrl": target_url,
                "contentHash": bytes.fromhex(content_hash.replace("0x", "")),
                "timestamp": ts,
            },
        }

        encoded_message = encode_typed_data(full_message=structured_data)
        signed_message = self.account.sign_message(encoded_message)

        v = signed_message.v
        r = hex(signed_message.r)
        s = hex(signed_message.s)

        # Build ABI calldata for Solidity function:
        # recordAttestation(string targetUrl, bytes32 contentHash, uint256 timestamp, uint8 v, bytes32 r, bytes32 s)
        # Function Selector: keccak256("recordAttestation(string,bytes32,uint256,uint8,bytes32,bytes32)") -> 4 bytes
        w3 = Web3()
        types = ["string", "bytes32", "uint256", "uint8", "bytes32", "bytes32"]
        values = [
            target_url,
            bytes.fromhex(content_hash.replace("0x", "")),
            ts,
            v,
            bytes.fromhex(r.replace("0x", "").zfill(64)),
            bytes.fromhex(s.replace("0x", "").zfill(64)),
        ]
        func_sig = w3.keccak(text="recordAttestation(string,bytes32,uint256,uint8,bytes32,bytes32)")[:4]
        encoded_args = w3.codec.encode(types, values)
        abi_calldata = "0x" + func_sig.hex() + encoded_args.hex()

        return OnChainProof(
            content_hash=content_hash,
            target_url=target_url,
            timestamp=ts,
            oracle_signer=self.signer_address,
            v=v,
            r=r,
            s=s,
            abi_calldata=abi_calldata,
        )

    def sign_oracle_grounding(
        self,
        query: str,
        data_hash: str,
        timestamp: Optional[int] = None,
    ):
        """
        Signs an EIP-712 CleanWebOracleFeed typed message for autonomous AI agents.
        """
        from app.schemas import OracleAttestation
        ts = timestamp or int(time.time())
        clean_hash = ("0x" + data_hash) if not data_hash.startswith("0x") else data_hash
        hash_bytes = bytes.fromhex(clean_hash.replace("0x", "").zfill(64))

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
            "domain": self.get_domain_data(),
            "message": {
                "query": query,
                "dataHash": hash_bytes,
                "timestamp": ts,
            },
        }

        encoded_message = encode_typed_data(full_message=structured_data)
        signed = self.account.sign_message(encoded_message)

        return OracleAttestation(
            query=query,
            data_hash=clean_hash,
            timestamp=ts,
            oracle_signer=self.signer_address,
            v=signed.v,
            r=hex(signed.r),
            s=hex(signed.s),
            signature="0x" + signed.signature.hex(),
            domain_chain_id=self.chain_id,
        )

    def verify_oracle_grounding(
        self,
        query: str,
        data_hash: str,
        timestamp: int,
        signature: str,
    ) -> Tuple[bool, str]:
        """
        Verifies an EIP-712 signature against the Oracle signer address.
        """
        try:
            clean_hash = ("0x" + data_hash) if not data_hash.startswith("0x") else data_hash
            hash_bytes = bytes.fromhex(clean_hash.replace("0x", "").zfill(64))

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
                "domain": self.get_domain_data(),
                "message": {
                    "query": query,
                    "dataHash": hash_bytes,
                    "timestamp": timestamp,
                },
            }

            encoded_message = encode_typed_data(full_message=structured_data)
            sig_bytes = bytes.fromhex(signature.replace("0x", ""))
            recovered = Account.recover_message(encoded_message, signature=sig_bytes)
            is_valid = recovered.lower() == self.signer_address.lower()
            return is_valid, recovered
        except Exception:
            return False, ""


onchain_signer = OnChainCleanWebSigner()

