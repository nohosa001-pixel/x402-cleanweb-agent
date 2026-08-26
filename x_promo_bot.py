"""
x402 AI Data Agent Suite - X (Twitter) Automated Promotion & Alert Bot
사용자 서비스 혜택 및 브라우저 UI 중심의 X(Twitter) 자동 홍보 & 알림 봇
"""

import os
import sys
import time
import urllib.parse
import webbrowser
import requests
from dotenv import load_dotenv

# Windows 콘솔 UTF-8 인코딩 대응
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# .env 로드
load_dotenv(override=True)

# Configuration & Links
GCP_URL = "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app"
PYPI_URL = "https://pypi.org/project/x402-cleanweb-agent/"
GITHUB_URL = "https://github.com/nohosa001-pixel/x402-cleanweb-agent"

# X API Credentials (from .env)
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET", "")

# 1. 한국어 사용자 서비스 & UI 중심 스레드
KOREAN_THREAD = [
    (
        "복잡하고 광고 많은 웹페이지, 긴 유튜브 영상 대본, 두꺼운 PDF 논문 요약할 때 답답하셨죠? 🛑\n\n"
        "비싼 월 5만원 정기 결제 없이, 필요한 문서만 1건당 10원대로 깔끔하게 본문만 뽑아주는 웹 서비스를 오픈했습니다! 📄✨\n\n"
        "브라우저에서 로그인 없이 바로 써보실 수 있습니다👇 (1/3)\n"
        "#웹서비스 #문서요약 #유튜브자막 #PDF변환 #AI도구"
    ),
    (
        "💻 누구나 브라우저 UI에서 클릭 한 번으로 바로 사용 가능:\n\n"
        "🌐 웹 링크 입력 ➡️ 광고·메뉴 싹 지우고 핵심 본문만 추출\n"
        "🎬 유튜브 링크 입력 ➡️ 타임스탬프가 포함된 전체 대본 추출\n"
        "📑 PDF·논문 업로드 ➡️ 읽기 편한 깔끔한 문서로 변환\n"
        "📝 순수 텍스트 추출 ➡️ AI 요약이나 메모장에 바로 붙여넣기\n\n"
        "(2/3)"
    ),
    (
        "지금 바로 브라우저 UI에서 무료로 체험해보세요 🚀\n\n"
        f"✨ 웹 UI 무료 체험: {GCP_URL}\n"
        "👉 화면의 [⚡ 1초 무료 체험] 버튼을 누르면 설치 없이 즉시 결과를 확인하실 수 있습니다!\n\n"
        "#생산성도구 #칼퇴치트키 #자료조사 #리포트작성 (3/3)"
    )
]

# 2. 글로벌 사용자 서비스 & UI 중심 스레드 (Global Launch Thread)
GLOBAL_THREAD = [
    (
        "Tired of messy ads, cluttered websites, and expensive $49/mo subscriptions? 🛑\n\n"
        "Introducing our Clean Web & Document Extraction Web App! 📄✨\n"
        "Turn any messy webpage, YouTube video, or PDF into clean, ready-to-read text in 1 second.\n\n"
        "Pay only when you use it (from $0.005). Try the live Web UI 👇 (1/3)\n"
        f"🌐 {GCP_URL}\n"
        "#Productivity #WebTools #Summary #CleanWeb #AI"
    ),
    (
        "⚡ What you can do directly on the Web UI:\n\n"
        "• 🌐 Clean Web: Strip all ads & clutter for clean reading\n"
        "• 🎬 YouTube Transcripts: Extract full timestamped video scripts\n"
        "• 📑 PDF & Papers: Convert research papers into digestible text\n"
        "• 📝 Pure Text: Copy-paste directly into your favorite AI tool\n\n"
        "(2/3)"
    ),
    (
        "✨ Experience the interactive Web UI right now!\n\n"
        f"👉 Click [⚡ Free Instant Test] on the site to see it in action without any login:\n\n"
        f"🌐 Live Web App: {GCP_URL}\n"
        f"📦 Python Tool: {PYPI_URL}\n\n"
        "#Productivity #AITools #Workflow #Reading (3/3)"
    )
]

def build_status_alert_tweet():
    """사용자 관점의 서비스 UI 및 편의성 강조 단일 트윗"""
    return (
        f"📄 [자료 조사 & 문서 정리 웹 서비스 안내]\n\n"
        f"광고 많은 웹페이지, 유튜브 영상 대본, PDF 논문을 1초 만에 깔끔한 본문으로 뽑아주는 웹 도구입니다 ✨\n\n"
        f"• 월 정기 결제 X (건당 10원대)\n"
        f"• 로그인 없이 브라우저에서 바로 사용\n\n"
        f"지금 웹 UI에서 바로 무료 체험해보세요 👇\n"
        f"🌐 {GCP_URL}\n\n"
        f"#웹서비스 #문서정리 #자료조사 #생산성도구"
    )

def post_tweet_api(text: str, in_reply_to_tweet_id: str = None) -> dict:
    """X API v2를 사용하여 트윗 게시"""
    if not (X_API_KEY and X_API_SECRET and X_ACCESS_TOKEN and X_ACCESS_TOKEN_SECRET):
        return {"success": False, "error": "MISSING_API_KEYS"}

    try:
        from requests_oauthlib import OAuth1
        auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
        url = "https://api.twitter.com/2/tweets"
        payload = {"text": text}
        if in_reply_to_tweet_id:
            payload["reply"] = {"in_reply_to_tweet_id": in_reply_to_tweet_id}
            
        resp = requests.post(url, json=payload, auth=auth, headers={"Content-Type": "application/json"})
        if resp.status_code in (200, 201):
            return {"success": True, "data": resp.json()}
        else:
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except ImportError:
        return {"success": False, "error": "requests_oauthlib_not_installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def open_intent_tweet(text: str):
    """트위터 웹 브라우저 인텐트를 열어 1초 만에 트윗 작성창 띄우기"""
    encoded_text = urllib.parse.quote(text)
    intent_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
    print(f"\n🔗 [X Web Intent URL 생성 완료]")
    print(f"👉 브라우저를 열어 트윗을 게시합니다...")
    try:
        webbrowser.open(intent_url)
    except Exception:
        pass
    print(f"직접 링크: {intent_url}\n")

def run_post_thread(thread_tweets: list, name: str):
    """스레드 포스팅 실행 (API 우선 시도 -> 미설정 시 Web Intent 안내)"""
    print(f"\n==================================================")
    print(f" 🚀 X(Twitter) [{name}] 프로모션 발송 시작")
    print(f"==================================================")
    
    has_api_keys = bool(X_API_KEY and X_API_SECRET and X_ACCESS_TOKEN and X_ACCESS_TOKEN_SECRET)
    
    if has_api_keys:
        print("🔑 X API V2 인증키 감지! 완전 자동 API 스레드 포스팅을 진행합니다...")
        parent_id = None
        for idx, tweet_text in enumerate(thread_tweets, 1):
            print(f"\n[{idx}/{len(thread_tweets)}] 트윗 전송 중...")
            result = post_tweet_api(tweet_text, in_reply_to_tweet_id=parent_id)
            if result.get("success"):
                tweet_id = result["data"]["data"]["id"]
                print(f"  ✅ 전송 성공! Tweet ID: {tweet_id}")
                parent_id = tweet_id
                time.sleep(2)
            else:
                print(f"  ❌ API 전송 실패: {result.get('error')}")
                print("  ➡️ 브라우저 원클릭 Intent로 전환합니다.")
                open_intent_tweet(tweet_text)
        print("\n🎉 모든 스레드 포스팅 완료!")
    else:
        print("💡 X API Key가 .env에 설정되지 않았습니다.")
        print("👉 브라우저 1클릭 트윗 작성창을 자동으로 띄웁니다.")
        for idx, tweet_text in enumerate(thread_tweets, 1):
            print(f"\n--- [스레드 {idx}/{len(thread_tweets)}] ---")
            print(tweet_text)
            print("-" * 50)
            open_intent_tweet(tweet_text)
            if idx < len(thread_tweets):
                input(f"👉 {idx}번 트윗 게시 후 다음 트윗 작성을 위해 [Enter]를 누르세요...")

def run_scheduler(interval_hours: int = 6):
    """주기적 자동 알림 모드"""
    print(f"\n⏰ x402 X 자동 알림 봇 스케줄러 가동 (주기: {interval_hours}시간)")
    print("종료하려면 Ctrl+C를 누르세요.\n")
    
    while True:
        status_tweet = build_status_alert_tweet()
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 정기 홍보 트윗 발송 시도...")
        
        has_api_keys = bool(X_API_KEY and X_API_SECRET and X_ACCESS_TOKEN and X_ACCESS_TOKEN_SECRET)
        if has_api_keys:
            res = post_tweet_api(status_tweet)
            if res.get("success"):
                print(f"✅ 정기 트윗 발송 성공: {res['data']['data']['id']}")
            else:
                print(f"❌ 발송 실패: {res.get('error')}")
        else:
            print("📢 발송할 트윗 내용:\n" + status_tweet)
            open_intent_tweet(status_tweet)
            
        print(f"\n⏳ 다음 발송까지 {interval_hours}시간 대기합니다...")
        time.sleep(interval_hours * 3600)

def main():
    print("==========================================================")
    print(" 🤖 x402 웹 서비스 - X (Twitter) 자동 홍보 & 알림 봇")
    print(" (사용자 서비스 혜택 및 브라우저 UI 중심)")
    print("==========================================================")
    print(" 1. 🇰🇷 한국 사용자 서비스 & UI 중심 스레드 게시")
    print(" 2. 🚀 글로벌 사용자 서비스 & UI 중심 스레드 게시")
    print(" 3. 📄 웹 서비스 UI 소개 단일 트윗 게시")
    print(" 4. ⏰ 백그라운드 정기 자동 알림 스케줄러 실행")
    print(" 5. ⚙️ X API 연동 안내 및 상태 확인")
    print("==========================================================")
    
    choice = input("👉 원하는 작업 번호를 입력하세요 (기본값: 1): ").strip() or "1"
    
    if choice == "1":
        run_post_thread(KOREAN_THREAD, "한국 사용자 서비스 스레드")
    elif choice == "2":
        run_post_thread(GLOBAL_THREAD, "글로벌 사용자 서비스 스레드")
    elif choice == "3":
        tweet = build_status_alert_tweet()
        print("\n" + tweet)
        if X_API_KEY and X_API_SECRET:
            res = post_tweet_api(tweet)
            if res.get("success"):
                print("✅ 트윗 전송 성공!")
            else:
                print("❌ API 전송 실패, 브라우저로 엽니다.")
                open_intent_tweet(tweet)
        else:
            open_intent_tweet(tweet)
    elif choice == "4":
        hours = input("알림 주기(시간)를 입력하세요 (기본값: 6): ").strip() or "6"
        run_scheduler(int(hours))
    elif choice == "5":
        print("\n[X API 연동 상태]")
        print(f" - X_API_KEY: {'✅ 설정됨' if X_API_KEY else '❌ 미설정 (Web Intent로 작동)'}")
        print(f" - X_API_SECRET: {'✅ 설정됨' if X_API_SECRET else '❌ 미설정'}")
        print(f" - X_ACCESS_TOKEN: {'✅ 설정됨' if X_ACCESS_TOKEN else '❌ 미설정'}")
        print(f" - X_ACCESS_TOKEN_SECRET: {'✅ 설정됨' if X_ACCESS_TOKEN_SECRET else '❌ 미설정'}")
        print("\n💡 .env 파일에 X API 키를 입력하시면 완전 자동 무인 포스팅이 활성화됩니다.")
    else:
        print("잘못된 입력입니다.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--auto-korean":
            run_post_thread(KOREAN_THREAD, "한국 사용자 서비스 스레드")
        elif arg == "--auto-global":
            run_post_thread(GLOBAL_THREAD, "글로벌 사용자 서비스 스레드")
        elif arg == "--status":
            t = build_status_alert_tweet()
            print(t)
            open_intent_tweet(t)
        elif arg == "--schedule":
            run_scheduler(6)
        else:
            main()
    else:
        main()
