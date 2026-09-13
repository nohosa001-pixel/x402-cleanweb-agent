"""
Multi-Chain Automated Deployment Script for Base Mainnet and Arbitrum One.
Deploys:
1. AgentPaymentVault
2. CleanWebOracleConsumer
3. CleanWebOracleVerifier
To Base Mainnet (Chain ID 8453) and Arbitrum One (Chain ID 42161).
"""

import os
import sys
import json
import solcx
from web3 import Web3
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

DEPLOYER_KEY = os.getenv("DEPLOYER_PRIVATE_KEY") or os.getenv("SERVER_PRIVATE_KEY")
if not DEPLOYER_KEY:
    neighbor_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "security-gate-x402", ".env"))
    if os.path.exists(neighbor_env):
        with open(neighbor_env, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("DEPLOYER_PRIVATE_KEY="):
                    DEPLOYER_KEY = line.strip().split("=", 1)[1].strip()
                    break

SERVER_WALLET = os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")

CHAINS = [
    {
        "name": "Base Mainnet",
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "explorer": "https://basescan.org",
        "env_prefix": "BASE",
    },
    {
        "name": "Arbitrum One",
        "chain_id": 42161,
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "usdc_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "explorer": "https://arbiscan.io",
        "env_prefix": "ARBITRUM",
    },
]

def update_env_variable(key: str, value: str, env_path: str = ".env"):
    if not os.path.exists(env_path):
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def compile_contracts():
    print("📦 Solidity 0.8.20 컴파일 중...")
    solcx.set_solc_version_pragma("^0.8.20")
    contracts_dir = os.path.join(os.path.dirname(__file__), "contracts")
    vault_path = os.path.join(contracts_dir, "AgentPaymentVault.sol")
    consumer_path = os.path.join(contracts_dir, "CleanWebOracleConsumer.sol")
    verifier_path = os.path.join(contracts_dir, "CleanWebOracleVerifier.sol")

    compiled = solcx.compile_files(
        [vault_path, consumer_path, verifier_path],
        output_values=["abi", "bin"],
        solc_version="0.8.20"
    )
    print("✅ 컴파일 완료!")
    return compiled

def get_compiled(compiled: dict, contract_name: str):
    for k, v in compiled.items():
        if k.endswith(f":{contract_name}"):
            return v
    raise KeyError(f"Contract {contract_name} not found")

def deploy_chain(chain_config: dict, compiled: dict):
    chain_name = chain_config["name"]
    chain_id = chain_config["chain_id"]
    rpc_url = chain_config["rpc_url"]
    usdc_address = chain_config["usdc_address"]
    explorer = chain_config["explorer"]
    prefix = chain_config["env_prefix"]

    print("\n" + "=" * 60)
    print(f"🌐 [{chain_name}] (Chain ID: {chain_id}) 배포 시작")
    print("=" * 60)

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"❌ RPC 연결 실패: {rpc_url}")
        return None

    account = w3.eth.account.from_key(DEPLOYER_KEY)
    sender = account.address
    bal_wei = w3.eth.get_balance(sender)
    bal_eth = w3.from_wei(bal_wei, "ether")
    print(f"   👤 배포자 주소: {sender}")
    print(f"   💰 가스비 잔액: {bal_eth:.6f} ETH")

    if bal_eth < 0.0001:
        print(f"   ❌ 잔액 부족 (최소 0.0001 ETH 필요)")
        return None

    deployed = {}

    def deploy_single(contract_name: str, contract_interface, *args):
        abi = contract_interface["abi"]
        bytecode = contract_interface["bin"]
        contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        nonce = w3.eth.get_transaction_count(sender, "pending")
        gas_price = w3.eth.gas_price

        # EIP-1559 or legacy
        tx = contract.constructor(*args).build_transaction({
            "from": sender,
            "nonce": nonce,
            "gasPrice": int(gas_price * 1.2),
            "chainId": chain_id,
        })

        try:
            est_gas = w3.eth.estimate_gas(tx)
            tx["gas"] = int(est_gas * 1.25)
        except Exception:
            tx["gas"] = 3000000

        signed_tx = w3.eth.account.sign_transaction(tx, DEPLOYER_KEY)
        raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction")
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        print(f"   ⏳ [{contract_name}] TX 전송됨: {explorer}/tx/{tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        contract_addr = receipt.contractAddress
        print(f"   🎉 [{contract_name}] 배포 완료! 주소: {contract_addr}")
        return contract_addr

    # 1. AgentPaymentVault
    vault_addr = deploy_single("AgentPaymentVault", get_compiled(compiled, "AgentPaymentVault"), usdc_address, SERVER_WALLET)
    deployed["AgentPaymentVault"] = vault_addr

    # 2. CleanWebOracleConsumer
    consumer_addr = deploy_single("CleanWebOracleConsumer", get_compiled(compiled, "CleanWebOracleConsumer"), SERVER_WALLET)
    deployed["CleanWebOracleConsumer"] = consumer_addr

    # 3. CleanWebOracleVerifier
    verifier_addr = deploy_single("CleanWebOracleVerifier", get_compiled(compiled, "CleanWebOracleVerifier"), SERVER_WALLET)
    deployed["CleanWebOracleVerifier"] = verifier_addr

    # Update .env
    update_env_variable(f"{prefix}_AGENT_PAYMENT_VAULT_ADDRESS", vault_addr)
    update_env_variable(f"{prefix}_CLEANWEB_ORACLE_CONTRACT_ADDRESS", consumer_addr)
    update_env_variable(f"{prefix}_CLEANWEB_ORACLE_VERIFIER_ADDRESS", verifier_addr)

    return deployed

def main():
    print("=" * 60)
    print("🚀 CleanWeb Studio Multi-Chain Deployer (Base & Arbitrum)")
    print("=" * 60)

    compiled = compile_contracts()
    results = {}

    for chain in CHAINS:
        res = deploy_chain(chain, compiled)
        if res:
            results[chain["name"]] = res

    # Save to JSON
    json_path = "deployed_contracts_multichain.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("🎯 Base 및 Arbitrum 배포 및 설정 등록 완료!")
    print(f"📄 결과 파일 저장: {json_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
