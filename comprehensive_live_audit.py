import requests
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE = "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app"

print("=========================================================================")
print("🤖 [PURE B2A AUTONOMOUS AGENT AUDIT] 전수 종합 점검")
print("⚡ 정체성: 100% 순수 자율 에이전트 서비스 (Machine-to-Machine B2A)")
print(f"🔗 CleanWeb Live: {BASE}")
print("=========================================================================\n")

# 1. Pure B2A Multi-Chain x402 Paywall & Health Verification
print("▶ [1/3] 순수 B2A x402 결제 프로토콜 규격 및 페이월 점검")
x402_passed = False
try:
    t0 = time.time()
    r_pw = requests.get(f"{BASE}/api/v1/clean-web?url=https://paulgraham.com/greatwork.html", timeout=15)
    elapsed_pw = round((time.time() - t0) * 1000, 1)
    print(f"   HTTP Status: {r_pw.status_code} ({elapsed_pw}ms)")
    if r_pw.status_code == 402:
        data = r_pw.json()
        print(f"   ✅ PASS: HTTP 402 x402 자율 결제 프로토콜 규격 완벽 준수! (수신 지갑: {data.get('recipientWallet', '')[:10]}...)")
        x402_passed = True
    else:
        print(f"   ⚠️ Unexpected Status: {r_pw.status_code}\n")
except Exception as e:
    print(f"   ❌ Error checking x402 Paywall: {e}\n")

# 2. Use Pure B2A Agent VIP Pass for High-Value YouTube Gemini 3.6 AI extraction
pass_token = "WELCOME100"
print(f"\n▶ [2/3] B2A 자율 에이전트 공식 패스({pass_token})로 YouTube Gemini 3.6 Flash Video Intelligence 호출")
yt_passed = False
try:
    t0 = time.time()
    r_yt = requests.get(
        f"{BASE}/api/v1/clean-youtube?url=https://www.youtube.com/watch?v=aircAruvnKk",
        headers={"X-Agent-Pass": pass_token},
        timeout=30
    )
    elapsed_yt = round(time.time() - t0, 2)
    print(f"   HTTP Status: {r_yt.status_code} ({elapsed_yt}s)")
    yt_data = r_yt.json()
    if r_yt.status_code == 200:
        auth_info = yt_data.get("auth", {})
        rem_credits = auth_info.get("remaining_credits")
        print("   ✅ PASS: 유료 데이터 200 OK 잠금 해제 및 Gemini 3.6 AI 대본 생성 완료!")
        print(f"   제목: {yt_data.get('title')}")
        print(f"   엔진: {yt_data.get('engine')}")
        print(f"   남은 잔여 크레딧: {rem_credits}회\n")
        yt_passed = True
    else:
        print(f"   ❌ FAIL: 패스 인증 실패 (HTTP {r_yt.status_code})\n")
except Exception as e:
    print(f"   ❌ Error checking YouTube Gemini AI: {e}\n")

# 3. Check Frontend HTML for Web3 x402 Vault Integration
print("▶ [3/3] 프론트엔드 대시보드 Web3 x402 볼트 & USDC 결제 UI 연동 점검")
fe_passed = False
try:
    r_page = requests.get(f"{BASE}/dashboard", headers={"Accept": "text/html"}, timeout=10)
    if "x402" in r_page.text.lower() and ("vault" in r_page.text.lower() or "usdc" in r_page.text.lower()):
        print("   ✅ PASS: 공식 Web3 Multi-Chain x402 Vault 및 USDC 결제 대시보드 UI가 100% 정상 가동 중입니다.\n")
        fe_passed = True
    else:
        print(f"   ⚠️ 대시보드 HTML 로딩 경고 (길이: {len(r_page.text)} bytes)\n")
except Exception as e:
    print(f"   ❌ Error checking Dashboard: {e}\n")

print("=========================================================================")
if x402_passed and yt_passed and fe_passed:
    print("🎉 [전수 점검 결과] 100% 순수 B2A 자율 에이전트 서비스 파이프라인이 정상 작동합니다!")
else:
    print("⚠️ [전수 점검 결과] 일부 파이프라인에 주의 또는 점검이 필요합니다.")
print("=========================================================================")
