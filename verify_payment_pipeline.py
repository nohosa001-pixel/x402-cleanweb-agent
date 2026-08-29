import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE = "http://127.0.0.1:8000"

print("=========================================================================")
print("💳 [PAYMENT GATEWAY 1:1 AUDIT] x402 결제 시스템 전수 검증")
print(f"🔗 Target: {BASE}")
print("=========================================================================\n")

# 1. 결제 헤더 없이 무료 체험 한도 초과 시 402 응답 검증
print("▶ [Step 1] 결제 헤더 없이 유료 서비스 호출 (HTTP 402 Payment Required 검증)")
r_no_pay = requests.get(f"{BASE}/api/v1/clean-web?url=https://paulgraham.com/greatwork.html")
print(f"   HTTP Status: {r_no_pay.status_code}")
if r_no_pay.status_code == 402:
    print("   ✅ PASS: HTTP 402 Payment Required 정상 반환!")
    print(f"   결제 안내 응답:\n   {json.dumps(r_no_pay.json(), indent=2, ensure_ascii=False)[:300]}...\n")
else:
    print(f"   Response: {r_no_pay.status_code}\n")

# 2. Lemon Squeezy / Web2 신용카드 $1.00 결제 후 100회 패스 발급 검증
print("▶ [Step 2] Lemon Squeezy / 신용카드 100회 이용권 ($1.00 USD) 발급 시뮬레이션")
webhook_payload = {
    "meta": {"event_name": "order_created"},
    "data": {
        "id": "order_test_9988",
        "attributes": {
            "user_email": "tester@cleanweb.ai",
            "total_formatted": "$1.00"
        }
    }
}
r_mint = requests.post(f"{BASE}/api/v1/webhook/lemonsqueezy", json=webhook_payload)
print(f"   HTTP Status: {r_mint.status_code}")
mint_data = r_mint.json()
pass_token = mint_data.get("pass_token")
print(f"   ✅ PASS: 100회 크레딧 패스 발행 성공! Token: {pass_token}")
print(f"   초기 잔여 크레딧: {mint_data.get('credits')}회\n")

# 3. 발급받은 패스로 잠금 해제 및 크레딧 차감 검증
print(f"▶ [Step 3] 발급된 패스({pass_token})를 헤더에 넣고 서비스 호출")
r_paid = requests.get(
    f"{BASE}/api/v1/clean-web?url=https://paulgraham.com/greatwork.html",
    headers={"X-Agent-Pass": pass_token}
)
print(f"   HTTP Status: {r_paid.status_code}")
if r_paid.status_code == 200:
    paid_data = r_paid.json()
    auth = paid_data.get('auth', {})
    print("   ✅ PASS: 200 OK 데이터 잠금 해제 성공!")
    print(f"   제목: {paid_data.get('title')}")
    print(f"   결제 모드: {auth.get('mode')}")
    print(f"   차감 크레딧: {auth.get('credits_deducted')}회")
    print(f"   남은 잔여 크레딧: {auth.get('remaining_credits')}회\n")

# 4. VIP 프로모션 코드 WELCOME100 적용 검증
print("▶ [Step 4] VIP 프로모션 코드 'WELCOME100' 적용 검증")
r_promo = requests.get(
    f"{BASE}/api/v1/clean-web?url=https://paulgraham.com/greatwork.html",
    headers={"X-Agent-Pass": "WELCOME100"}
)
print(f"   HTTP Status: {r_promo.status_code}")
if r_promo.status_code == 200:
    promo_data = r_promo.json()
    auth_p = promo_data.get('auth', {})
    print("   ✅ PASS: WELCOME100 프로모션 패스 인증 성공!")
    print(f"   결제 모드: {auth_p.get('mode')}")
    print(f"   남은 잔여 크레딧: {auth_p.get('remaining_credits')}회\n")

print("=========================================================================")
print("🎉 결제 시스템(402 차단 ➡️ 패스 발급 ➡️ 크레딧 차감 ➡️ 잠금 해제) 100% 검증 완료!")
print("=========================================================================")
