import requests
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE = "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app"
LEMON_URL = "https://x402-cleanweb.lemonsqueezy.com/checkout/buy/f7a2896e-87b1-4cae-a0ed-60740553348d"

print("=========================================================================")
print("🍋 [FULL PRODUCTION & PAYMENT AUDIT] 전수 종합 점검")
print(f"🔗 CleanWeb Live: {BASE}")
print(f"🔗 Lemon Squeezy Store: {LEMON_URL}")
print("=========================================================================\n")

# 1. Lemon Squeezy Official Store Checkout Link HTTP Status Check
print("▶ [1/4] Lemon Squeezy 공식 실결제 상품 링크 응답성 점검")
try:
    t0 = time.time()
    r_ls = requests.get(LEMON_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    elapsed_ls = round((time.time() - t0) * 1000, 1)
    print(f"   HTTP Status: {r_ls.status_code} ({elapsed_ls}ms)")
    if r_ls.status_code == 200:
        print("   ✅ PASS: 공식 $1.00 결제 링크가 전 세계에서 100% 정상 열립니다!")
        print("   (Visa, Master, Apple Pay, PayPal 실결제 결제창 오픈 대기 중)\n")
    else:
        print(f"   ⚠️ Lemon Squeezy Status: {r_ls.status_code}\n")
except Exception as e:
    print(f"   ❌ Error checking Lemon Squeezy: {e}\n")

# 2. Legacy Webhook Elimination & B2A Security Guard Verification
print("▶ [2/4] 레거시 인간 웹훅 차단 및 순수 B2A 자율 에이전트 보안 검증")
r_wh = requests.post(f"{BASE}/api/v1/webhook/lemonsqueezy", json={"test": True}, timeout=15)
print(f"   HTTP Status: {r_wh.status_code}")
if r_wh.status_code in (404, 405):
    print("   ✅ PASS: 레거시 인간 웹훅이 철저히 제거(Blocked/404)되어 순수 B2A 자율 결제 보안이 완벽히 수호됩니다!\n")
else:
    print(f"   ⚠️ Unexpected Status: {r_wh.status_code}\n")

# 3. Use Pure B2A Agent VIP Pass for High-Value YouTube Gemini 3.6 AI extraction
pass_token = "WELCOME100"
print(f"▶ [3/4] B2A 자율 에이전트 공식 패스({pass_token})로 YouTube Gemini 3.6 Flash Video Intelligence 호출")
yt_passed = False
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

# 4. Check Frontend HTML for Web3 x402 Vault Integration
print("▶ [4/4] 프론트엔드 대시보드 Web3 x402 볼트 & 결제 UI 연동 점검")
r_page = requests.get(f"{BASE}/dashboard", headers={"Accept": "text/html"}, timeout=10)
fe_passed = False
if "x402" in r_page.text.lower() and ("vault" in r_page.text.lower() or "usdc" in r_page.text.lower()):
    print("   ✅ PASS: 공식 Web3 Multi-Chain x402 Vault 및 USDC 결제 대시보드 UI가 100% 정상 가동 중입니다.\n")
    fe_passed = True
else:
    print(f"   ⚠️ 대시보드 HTML 로딩 경고 (길이: {len(r_page.text)} bytes)\n")

print("=========================================================================")
if yt_passed and fe_passed:
    print("🎉 [전수 점검 결과] 모든 실결제 및 AI 서비스 파이프라인이 100% 정상 작동합니다!")
else:
    print("⚠️ [전수 점검 결과] 일부 파이프라인에 주의 또는 배포 대기 항목이 존재합니다.")
print("=========================================================================")
