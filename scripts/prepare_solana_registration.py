import os
import shutil
import json

DESKTOP_DIR = os.path.join(os.environ.get("USERPROFILE", "C:\\Users\\nohos"), "OneDrive", "바탕 화면")
PACKAGE_DIR = os.path.join(DESKTOP_DIR, "CleanWeb_Solana_Registration_Package")
os.makedirs(PACKAGE_DIR, exist_ok=True)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDL_SOURCE_DIR = os.path.join(ROOT_DIR, "contracts", "solana", "idl")

PROGRAM_INFO = [
    {
        "name": "AgentPaymentVault",
        "file": "AgentPaymentVault.json",
        "program_id": "7oZ16YaazQzN6z5uA1nAZWD9oGUDXyvHwXGJLFYyWi3y",
        "desc": "자율 AI 에이전트 결제 및 예치금 금고 (contracts/AgentPaymentVault.sol 대응)",
        "solscan_url": "https://solscan.io/account/7oZ16YaazQzN6z5uA1nAZWD9oGUDXyvHwXGJLFYyWi3y",
        "solanafm_url": "https://solana.fm/address/7oZ16YaazQzN6z5uA1nAZWD9oGUDXyvHwXGJLFYyWi3y"
    },
    {
        "name": "CleanWebOracleConsumer",
        "file": "CleanWebOracleConsumer.json",
        "program_id": "21ZR1QCyAbNrRLs1iWEkdbNsfCFdJcy6ip9R2JxDbkTL",
        "desc": "오라클 그라운딩 데이터 소비자 컨트랙트 (contracts/CleanWebOracleConsumer.sol 대응)",
        "solscan_url": "https://solscan.io/account/21ZR1QCyAbNrRLs1iWEkdbNsfCFdJcy6ip9R2JxDbkTL",
        "solanafm_url": "https://solana.fm/address/21ZR1QCyAbNrRLs1iWEkdbNsfCFdJcy6ip9R2JxDbkTL"
    },
    {
        "name": "CleanWebOracleVerifier",
        "file": "CleanWebOracleVerifier.json",
        "program_id": "9nVrymJgNWCXkuGKn8CCQnSK6aDazFR7z3WL82jZiopC",
        "desc": "Ed25519 암호학적 서명 검증 라이브러리 (contracts/CleanWebOracleVerifier.sol 대응)",
        "solscan_url": "https://solscan.io/account/9nVrymJgNWCXkuGKn8CCQnSK6aDazFR7z3WL82jZiopC",
        "solanafm_url": "https://solana.fm/address/9nVrymJgNWCXkuGKn8CCQnSK6aDazFR7z3WL82jZiopC"
    }
]

def prepare():
    print(f"[PACKAGE] Preparing CleanWeb Solana Registration Package at:\n   {PACKAGE_DIR}\n")
    
    # Copy IDL files
    for item in PROGRAM_INFO:
        src = os.path.join(IDL_SOURCE_DIR, item["file"])
        dst = os.path.join(PACKAGE_DIR, item["file"])
        shutil.copy2(src, dst)
        print(f"  [COPIED] {item['file']} -> Desktop package")

    # Generate Quick Copy Text Sheet
    sheet_path = os.path.join(PACKAGE_DIR, "00_원클릭_등록_안내서.txt")
    with open(sheet_path, "w", encoding="utf-8") as f:
        f.write("======================================================================\n")
        f.write("☀️ [CleanWeb x402 Suite] Solscan / SolanaFM 공식 IDL 원클릭 등록 가이드\n")
        f.write("======================================================================\n\n")
        f.write("대표님 지갑 주소 (Owner / Treasury Public Key):\n")
        f.write("411ksMz9RHYVtVMe6RUUErzZYtrU9zzvkgzswKbqx9qp\n\n")
        f.write("----------------------------------------------------------------------\n")
        f.write("📋 [등록 단계 3단계 요약]\n")
        f.write("1. 웹 브라우저에서 https://solscan.io 또는 https://portal.solana.fm 접속\n")
        f.write("2. 대표님 팬텀(Phantom) 지갑 연결 (411ks...)\n")
        f.write("3. 아래 3개 프로그램의 Program ID를 검색창에 입력 -> [Upload IDL] 클릭 -> 같은 폴더의 JSON 파일 선택!\n\n")
        f.write("----------------------------------------------------------------------\n")
        f.write("📌 [1번 컨트랙트] AgentPaymentVault (가장 핵심!)\n")
        f.write("  - 설명: 자율 AI 에이전트 결제 및 선입금 금고\n")
        f.write(f"  - Program ID (복사): {PROGRAM_INFO[0]['program_id']}\n")
        f.write(f"  - 업로드할 파일: {PROGRAM_INFO[0]['file']}\n")
        f.write(f"  - Solscan 바로가기: {PROGRAM_INFO[0]['solscan_url']}\n\n")
        f.write("----------------------------------------------------------------------\n")
        f.write("📌 [2번 컨트랙트] CleanWebOracleConsumer\n")
        f.write("  - 설명: 오라클 그라운딩 데이터 검증 소비자\n")
        f.write(f"  - Program ID (복사): {PROGRAM_INFO[1]['program_id']}\n")
        f.write(f"  - 업로드할 파일: {PROGRAM_INFO[1]['file']}\n")
        f.write(f"  - Solscan 바로가기: {PROGRAM_INFO[1]['solscan_url']}\n\n")
        f.write("----------------------------------------------------------------------\n")
        f.write("📌 [3번 컨트랙트] CleanWebOracleVerifier\n")
        f.write("  - 설명: Ed25519 암호학적 디지털 서명 검증 라이브러리\n")
        f.write(f"  - Program ID (복사): {PROGRAM_INFO[2]['program_id']}\n")
        f.write(f"  - 업로드할 파일: {PROGRAM_INFO[2]['file']}\n")
        f.write(f"  - Solscan 바로가기: {PROGRAM_INFO[2]['solscan_url']}\n\n")
        f.write("======================================================================\n")
        f.write("🎉 업로드 완료 즉시 Solscan 탐색기에서 온체인 인터페이스가 활성화됩니다!\n")
        f.write("======================================================================\n")

    print(f"\n  [CREATED] 00_원클릭_등록_안내서.txt 생성 완료")
    print(f"\n[DONE] All assets ready in: {PACKAGE_DIR}")

if __name__ == "__main__":
    prepare()
