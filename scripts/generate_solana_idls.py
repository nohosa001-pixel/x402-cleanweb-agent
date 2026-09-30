import os
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDL_DIR = os.path.join(ROOT_DIR, "contracts", "solana", "idl")
os.makedirs(IDL_DIR, exist_ok=True)

# CleanWeb x402 Suite: 3 Dedicated Solana Program IDs & Anchor IDL Specs (1:1 with contracts/*.sol)
CONTRACT_SPECS = [
    {
        "file": "AgentPaymentVault.json",
        "name": "agent_payment_vault",
        "program_id": "7oZ16YaazQzN6z5uA1nAZWD9oGUDXyvHwXGJLFYyWi3y",
        "description": "Agent Payment Vault: On-chain pre-funded deposit vault for autonomous AI agents paying x402 micropayments",
        "instructions": [
            {
                "name": "initialize",
                "docs": ["Initialize the global vault and treasury configuration"],
                "accounts": [
                    {"name": "vaultConfig", "isMut": True, "isSigner": False},
                    {"name": "usdcMint", "isMut": False, "isSigner": False},
                    {"name": "vaultTokenAccount", "isMut": True, "isSigner": False},
                    {"name": "authority", "isMut": True, "isSigner": True},
                    {"name": "systemProgram", "isMut": False, "isSigner": False},
                    {"name": "tokenProgram", "isMut": False, "isSigner": False},
                    {"name": "rent", "isMut": False, "isSigner": False}
                ],
                "args": [
                    {"name": "treasuryWallet", "type": "publicKey"}
                ]
            },
            {
                "name": "deposit",
                "docs": ["Agent pre-funds their on-chain vault with Native SPL USDC"],
                "accounts": [
                    {"name": "vaultConfig", "isMut": False, "isSigner": False},
                    {"name": "vaultTokenAccount", "isMut": True, "isSigner": False},
                    {"name": "agentRecord", "isMut": True, "isSigner": False},
                    {"name": "agent", "isMut": True, "isSigner": True},
                    {"name": "agentTokenAccount", "isMut": True, "isSigner": False},
                    {"name": "tokenProgram", "isMut": False, "isSigner": False},
                    {"name": "systemProgram", "isMut": False, "isSigner": False}
                ],
                "args": [
                    {"name": "amount", "type": "u64"}
                ]
            },
            {
                "name": "settleAgentBatch",
                "docs": ["Settle spent USDC amounts from agent vaults to Treasury (Authority only)"],
                "accounts": [
                    {"name": "vaultConfig", "isMut": True, "isSigner": False},
                    {"name": "vaultTokenAccount", "isMut": True, "isSigner": False},
                    {"name": "agentRecord", "isMut": True, "isSigner": False},
                    {"name": "treasuryTokenAccount", "isMut": True, "isSigner": False},
                    {"name": "authority", "isMut": False, "isSigner": True},
                    {"name": "tokenProgram", "isMut": False, "isSigner": False}
                ],
                "args": [
                    {"name": "amount", "type": "u64"}
                ]
            },
            {
                "name": "updateTreasury",
                "docs": ["Update the treasury destination wallet (Authority only)"],
                "accounts": [
                    {"name": "vaultConfig", "isMut": True, "isSigner": False},
                    {"name": "authority", "isMut": False, "isSigner": True}
                ],
                "args": [
                    {"name": "newTreasuryWallet", "type": "publicKey"}
                ]
            }
        ],
        "accounts": [
            {
                "name": "VaultConfig",
                "type": {
                    "kind": "struct",
                    "fields": [
                        {"name": "authority", "type": "publicKey"},
                        {"name": "treasuryWallet", "type": "publicKey"},
                        {"name": "usdcMint", "type": "publicKey"},
                        {"name": "vaultTokenAccount", "type": "publicKey"},
                        {"name": "bump", "type": "u8"},
                        {"name": "totalSettledUsdc", "type": "u64"}
                    ]
                }
            },
            {
                "name": "AgentVaultRecord",
                "type": {
                    "kind": "struct",
                    "fields": [
                        {"name": "agent", "type": "publicKey"},
                        {"name": "balance", "type": "u64"},
                        {"name": "totalDeposited", "type": "u64"},
                        {"name": "totalSpent", "type": "u64"},
                        {"name": "createdAt", "type": "i64"},
                        {"name": "lastUpdatedAt", "type": "i64"}
                    ]
                }
            }
        ]
    },
    {
        "file": "CleanWebOracleConsumer.json",
        "name": "cleanweb_oracle_consumer",
        "program_id": "21ZR1QCyAbNrRLs1iWEkdbNsfCFdJcy6ip9R2JxDbkTL",
        "description": "CleanWeb Oracle Consumer: Consumer mixin for verifying AI web groundings & RAG proofs on Solana",
        "instructions": [
            {
                "name": "consumeGroundingProof",
                "docs": ["Consume and verify on-chain oracle data grounding proof"],
                "accounts": [
                    {"name": "consumerRecord", "isMut": True, "isSigner": False},
                    {"name": "consumer", "isMut": True, "isSigner": True},
                    {"name": "verifierProgram", "isMut": False, "isSigner": False}
                ],
                "args": [
                    {"name": "dataHash", "type": {"array": ["u8", 32]}},
                    {"name": "timestamp", "type": "i64"},
                    {"name": "signature", "type": {"array": ["u8", 64]}}
                ]
            }
        ],
        "accounts": [
            {
                "name": "ConsumerProofRecord",
                "type": {
                    "kind": "struct",
                    "fields": [
                        {"name": "consumer", "type": "publicKey"},
                        {"name": "dataHash", "type": {"array": ["u8", 32]}},
                        {"name": "timestamp", "type": "i64"},
                        {"name": "verified", "type": "bool"}
                    ]
                }
            }
        ]
    },
    {
        "file": "CleanWebOracleVerifier.json",
        "name": "cleanweb_oracle_verifier",
        "program_id": "9nVrymJgNWCXkuGKn8CCQnSK6aDazFR7z3WL82jZiopC",
        "description": "CleanWeb Oracle Verifier: Native Ed25519 / EIP-712 cryptographic signature proof verification library on Solana",
        "instructions": [
            {
                "name": "verifyOracleSignature",
                "docs": ["Verify Ed25519 cryptographic signature issued by CleanWeb Oracle Signer"],
                "accounts": [
                    {"name": "oracleAuthority", "isMut": False, "isSigner": False}
                ],
                "args": [
                    {"name": "dataHash", "type": {"array": ["u8", 32]}},
                    {"name": "timestamp", "type": "i64"},
                    {"name": "signature", "type": {"array": ["u8", 64]}}
                ]
            }
        ],
        "accounts": [
            {
                "name": "OracleAuthorityAccount",
                "type": {
                    "kind": "struct",
                    "fields": [
                        {"name": "oraclePublicKey", "type": "publicKey"},
                        {"name": "totalAttestationsVerified", "type": "u64"}
                    ]
                }
            }
        ]
    }
]

def main():
    print(f"Generating 3 dedicated CleanWeb Solana Anchor IDLs in {IDL_DIR}...")
    for spec in CONTRACT_SPECS:
        idl_content = {
            "version": "0.1.0",
            "name": spec["name"],
            "metadata": {
                "address": spec["program_id"],
                "origin": "anchor",
                "description": spec["description"]
            },
            "instructions": spec["instructions"],
            "accounts": spec["accounts"],
            "types": [],
            "events": [
                {
                    "name": "ActionRecorded",
                    "fields": [
                        {"name": "caller", "type": "publicKey", "index": True},
                        {"name": "timestamp", "type": "i64", "index": False}
                    ]
                }
            ],
            "errors": [
                {"code": 6000, "name": "InvalidSignature", "msg": "Cryptographic signature verification failed"},
                {"code": 6001, "name": "UnauthorizedCaller", "msg": "Caller lacks required authority"}
            ]
        }
        target_path = os.path.join(IDL_DIR, spec["file"])
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(idl_content, f, indent=2)
        print(f"  [OK] {spec['file']} -> {spec['program_id']}")
    print("Done! Exactly 3 dedicated IDL files generated.")

if __name__ == "__main__":
    main()
