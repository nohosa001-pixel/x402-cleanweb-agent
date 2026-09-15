"""
Automated Contract Verification & Public Explorer Disclosure Script for CleanWeb Oracle / x402.
Supports Polygonscan (137), BaseScan (8453), and Arbiscan (42161).
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

CONTRACTS_DIR = ROOT_DIR / "contracts"
VERIFICATION_DIR = CONTRACTS_DIR / "verification"

# Multi-chain configurations
NETWORKS = {
    "polygon": {
        "chainId": 137,
        "name": "Polygon Mainnet",
        "explorer": "https://polygonscan.com",
        "usdc": os.getenv("USDC_CONTRACT_ADDRESS", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"),
        "contracts": {
            "AgentPaymentVault": os.getenv("AGENT_PAYMENT_VAULT_ADDRESS", "0x45ecBfAa2F4B0Bc6ccD3eB2dB9B1Ca49CF121861"),
            "CleanWebOracleConsumer": os.getenv("CLEANWEB_ORACLE_CONTRACT_ADDRESS", "0xAECbfBc171F522c35985AABa2FA1F9881A046D66"),
            "CleanWebOracleVerifier": os.getenv("CLEANWEB_ORACLE_VERIFIER_ADDRESS", "0x18fA451b1d9A9FbbDa6Ebd86F8b42891866ADc46"),
        }
    },
    "base": {
        "chainId": 8453,
        "name": "Base Mainnet",
        "explorer": "https://basescan.org",
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "contracts": {
            "AgentPaymentVault": os.getenv("BASE_AGENT_PAYMENT_VAULT_ADDRESS", "0x28292D76E07E5539F15F3b97935dE8E0432E76DD"),
            "CleanWebOracleConsumer": os.getenv("BASE_CLEANWEB_ORACLE_CONTRACT_ADDRESS", "0x2394d888Bd4FFeD472318B891FA17f7F9119dabe"),
            "CleanWebOracleVerifier": os.getenv("BASE_CLEANWEB_ORACLE_VERIFIER_ADDRESS", "0x3eD259e47ebA439A9A35489787482B0003310740"),
        }
    },
    "arbitrum": {
        "chainId": 42161,
        "name": "Arbitrum One",
        "explorer": "https://arbiscan.io",
        "usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "contracts": {
            "AgentPaymentVault": os.getenv("ARBITRUM_AGENT_PAYMENT_VAULT_ADDRESS", "0x28292D76E07E5539F15F3b97935dE8E0432E76DD"),
            "CleanWebOracleConsumer": os.getenv("ARBITRUM_CLEANWEB_ORACLE_CONTRACT_ADDRESS", "0x2394d888Bd4FFeD472318B891FA17f7F9119dabe"),
            "CleanWebOracleVerifier": os.getenv("ARBITRUM_CLEANWEB_ORACLE_VERIFIER_ADDRESS", "0x3eD259e47ebA439A9A35489787482B0003310740"),
        }
    }
}

TREASURY = os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")


def encode_address(addr: str) -> str:
    """Encodes an Ethereum address to a 32-byte (64 hex characters) ABI representation."""
    cleaned = addr.lower().replace("0x", "")
    return cleaned.zfill(64)


def get_constructor_args(contract_name: str, chain: str) -> str:
    """Encodes constructor arguments into hex string without requiring external eth_abi dependency."""
    net = NETWORKS[chain]
    if contract_name == "AgentPaymentVault":
        usdc_hex = encode_address(net["usdc"])
        treasury_hex = encode_address(TREASURY)
        return usdc_hex + treasury_hex
    elif contract_name in ("CleanWebOracleConsumer", "CleanWebOracleVerifier"):
        return encode_address(TREASURY)
    else:
        raise ValueError(f"Unknown contract {contract_name}")


def display_verification_details(chain: str):
    """Outputs structured verification parameters and direct URLs."""
    net = NETWORKS[chain]
    print(f"\n========================================================")
    print(f"  VERIFICATION PARAMETERS: {net['name']} (Chain ID {net['chainId']})")
    print(f"========================================================")
    print(f"Compiler Version:  v0.8.20+commit.a1b79de6")
    print(f"Optimization:      No (or Enabled 200 runs if compiled with optimizer)")
    print(f"License:           MIT License")
    print(f"Treasury / Signer: {TREASURY}")
    print(f"Native USDC:       {net['usdc']}")

    for cname, address in net["contracts"].items():
        if not address:
            continue
        c_args = get_constructor_args(cname, chain)
        source_file = VERIFICATION_DIR / f"{cname}.flattened.sol"
        verify_url = f"{net['explorer']}/verifyContract?a={address}"
        
        print(f"\n--- [{cname}] ---")
        print(f"Contract Address:  {address}")
        print(f"Direct Verify URL: {verify_url}")
        print(f"Flattened Source:  {source_file}")
        print(f"Constructor Hex:   {c_args}")


def main():
    parser = argparse.ArgumentParser(description="Contract Verification Helper for CleanWeb Oracle / x402")
    parser.add_argument("--chain", choices=["polygon", "base", "arbitrum", "all"], default="polygon")
    args = parser.parse_args()

    chains = ["polygon", "base", "arbitrum"] if args.chain == "all" else [args.chain]
    for c in chains:
        display_verification_details(c)


if __name__ == "__main__":
    main()
