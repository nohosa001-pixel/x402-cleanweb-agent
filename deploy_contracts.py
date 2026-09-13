"""
Automated On-Chain Contract Deployment Script for Polygon Mainnet.
Compiles and deploys:
1. AgentPaymentVault.sol
2. CleanWebOracleConsumer.sol
3. CleanWebOracleVerifier.sol
Saves deployed contract addresses automatically into .env.
"""

import os
import sys
import solcx
from web3 import Web3
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


load_dotenv()

POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "https://polygon-bor-rpc.publicnode.com")
USDC_ADDRESS = os.getenv("USDC_CONTRACT_ADDRESS", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
SERVER_WALLET = os.getenv("SERVER_WALLET_ADDRESS", "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf")
DEPLOYER_KEY = os.getenv("DEPLOYER_PRIVATE_KEY") or os.getenv("SERVER_PRIVATE_KEY")

if not DEPLOYER_KEY:
    # Try reading from neighbor project: security-gate-x402/.env
    neighbor_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "security-gate-x402", ".env"))
    if os.path.exists(neighbor_env):
        with open(neighbor_env, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("DEPLOYER_PRIVATE_KEY="):
                    DEPLOYER_KEY = line.strip().split("=", 1)[1].strip()
                    break


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

def main():
    print("=" * 60)
    print("🚀 CleanWeb Studio / x402 Polygon Mainnet Auto-Deployer")
    print("=" * 60)

    if not DEPLOYER_KEY:
        print("\n❌ [오류] DEPLOYER_PRIVATE_KEY가 .env에 설정되어 있지 않습니다.")
        print("💡 .env 파일에 다음 줄을 추가해주세요:")
        print("   DEPLOYER_PRIVATE_KEY=0x당신의_개인키")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))
    if not w3.is_connected():
        print(f"❌ RPC 연결 실패: {POLYGON_RPC_URL}")
        sys.exit(1)

    account = w3.eth.account.from_key(DEPLOYER_KEY)
    sender = account.address
    balance_wei = w3.eth.get_balance(sender)
    balance_pol = w3.from_wei(balance_wei, 'ether')
    print(f"✅ 배포자 지갑 주소: {sender}")
    print(f"✅ 잔액: {balance_pol:.4f} POL")

    if balance_pol < 0.05:
        print("❌ 가스비(POL)가 부족합니다. 최소 0.05 POL 이상 필요합니다.")
        sys.exit(1)

    # 1. Compile Contracts
    print("\n📦 Solidity 0.8.20 컴파일 시작...")
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
    print("✅ 컴파일 성공!")

    def deploy_contract(name: str, contract_interface, *args):
        print(f"\n⏳ [{name}] 배포 트랜잭션 전송 중...")
        abi = contract_interface["abi"]
        bytecode = contract_interface["bin"]
        contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        nonce = w3.eth.get_transaction_count(sender, "pending")
        gas_price = w3.eth.gas_price
        effective_gas_price = max(int(gas_price * 1.35), w3.to_wei(35, 'gwei'))

        # EIP-1559 or legacy
        tx = contract.constructor(*args).build_transaction({
            "from": sender,
            "nonce": nonce,
            "gasPrice": effective_gas_price,
            "chainId": 137,
        })
        
        # Estimate gas
        try:
            estimated_gas = w3.eth.estimate_gas(tx)
            tx["gas"] = int(estimated_gas * 1.2)
        except Exception:
            tx["gas"] = 3000000

        signed_tx = w3.eth.account.sign_transaction(tx, DEPLOYER_KEY)
        raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction")
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        print(f"   📡 TX 전송됨: https://polygonscan.com/tx/{tx_hash.hex()}")
        print("   ⏳ 블록 확정 대기 중 (약 5~15초)...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        contract_addr = receipt.contractAddress
        print(f"   🎉 [{name}] 배포 완료! 주소: {contract_addr}")
        return contract_addr

    def get_compiled(contract_name: str):
        for k, v in compiled.items():
            if k.endswith(f":{contract_name}"):
                return v
        raise KeyError(f"Contract {contract_name} not found in compilation results. Keys: {list(compiled.keys())}")

    # 2. Deploy AgentPaymentVault
    vault_addr = deploy_contract("AgentPaymentVault", get_compiled("AgentPaymentVault"), USDC_ADDRESS, SERVER_WALLET)

    # 3. Deploy CleanWebOracleConsumer
    consumer_addr = deploy_contract("CleanWebOracleConsumer", get_compiled("CleanWebOracleConsumer"), SERVER_WALLET)

    # 4. Deploy CleanWebOracleVerifier
    verifier_addr = deploy_contract("CleanWebOracleVerifier", get_compiled("CleanWebOracleVerifier"), SERVER_WALLET)


    # 5. Save to .env
    print("\n📝 .env 파일 자동 업데이트 중...")
    update_env_variable("AGENT_PAYMENT_VAULT_ADDRESS", vault_addr)
    update_env_variable("CLEANWEB_ORACLE_CONTRACT_ADDRESS", consumer_addr)
    update_env_variable("CLEANWEB_ORACLE_VERIFIER_ADDRESS", verifier_addr)

    print("\n" + "=" * 60)
    print("🎯 배포 및 등록이 모두 성공적으로 완료되었습니다!")
    print("=" * 60)
    print(f"1. AgentPaymentVault       : {vault_addr}")
    print(f"2. CleanWebOracleConsumer  : {consumer_addr}")
    print(f"3. CleanWebOracleVerifier  : {verifier_addr}")
    print(f"🔗 Polygonscan 확인 가능: https://polygonscan.com/address/{consumer_addr}")

if __name__ == "__main__":
    main()
