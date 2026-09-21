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

# 1. 한국어 자율 AI 에이전트 개발자 & 빌더 전용 스레드 (B2A AI Agent Thread)
KOREAN_THREAD = [
    (
        "자율 AI 에이전트(LangChain, CrewAI, AutoGen, Eliza)를 구축 중이신가요? 🤖🛑\n\n"
        "웹 검색/스크래핑 시 80KB의 더러운 HTML 태그와 광고로 LLM 토큰 예산을 태우지 마세요.\n\n"
        "토큰 노이즈 87% 압축 + 악성 프롬프트 인젝션 실시간 차단 + EIP-712 온체인 검증 오라클:\n"
        "순수 자율 에이전트를 위한 B2A 머신-투-머신 인프라 x402를 소개합니다👇 (1/3)\n"
        "#AIAgents #LangChain #CrewAI #자율에이전트 #Web3 #MCP"
    ),
    (
        "⚡ 자율 에이전트 운영자가 x402를 선택하는 4가지 이유:\n\n"
        "• 📉 토큰 비용 86.2% 절감: 87% 텍스트 압축으로 GPT-4o/Claude 인퍼런스 비용 극대화 절약\n"
        "• 🛡️ Ingress Defense: 악성 프롬프트 인젝션·탈옥 코드 실시간 AST 검역\n"
        "• 🔐 EIP-712 온체인 서명: Polygon, Base, Arbitrum 스마트 컨트랙트에서 위변조 독립 검증\n"
        "• 💳 Zero-Human 결제: 인간 개입 없이 자율 에이전트가 USDC 볼트(<1ms 무가스)로 직접 정산\n\n"
        "(2/3)"
    ),
    (
        "🚀 1분 만에 자율 에이전트에 무인 연동하기:\n\n"
        "pip install x402-cleanweb-agent\n\n"
        "터미널/에이전트 즉시 테스트 (3회 무료 샌드박스):\n"
        f"curl \"{GCP_URL}/r/https://news.ycombinator.com\"\n\n"
        f"🌐 게이트웨이 & API 명세: {GCP_URL}/docs\n"
        f"📜 공식 깃허브: {GITHUB_URL} (3/3)\n"
        "#Python #MachineToMachine #스마트컨트랙트 #LLM"
    )
]

# 2. 글로벌 자율 AI 에이전트 인프라 스레드 (Global Autonomous Agent Infrastructure Thread)
GLOBAL_THREAD = [
    (
        "Building Autonomous AI Agents & Swarms with LangChain, CrewAI, or AutoGen? 🤖🛑\n\n"
        "Stop burning 87% of your LLM context window on raw HTML noise, scripts, and ads.\n\n"
        "Introducing x402 CleanWeb: The 100% Autonomous B2A (Machine-to-Machine) Real-Time Data Oracle with cryptographic EIP-712 proofs 👇 (1/3)\n"
        f"📦 PyPI: {PYPI_URL}\n"
        "#AIAgents #LangChain #CrewAI #Web3 #MCP #AgenticAI"
    ),
    (
        "💡 Mathematical Token Arbitrage Proof for Agent Operators:\n\n"
        "• 80KB Raw Web HTML ≈ 20,000 tokens ($0.05 USD on GPT-4o / Claude 3.5)\n"
        "• x402 Clean Markdown ≈ 2,600 tokens + $0.001 API fee = $0.0075 Total\n"
        "• Net Savings: 86.2% dollar reduction on EVERY single agent web search\n"
        "• Zero Human In-The-Loop: 1ms zero-gas USDC micropayments via Pre-funded Vaults\n\n"
        "(2/3)"
    ),
    (
        "⚡ Zero-Friction Instant Test for Autonomous Agents:\n\n"
        f"curl \"{GCP_URL}/r/https://news.ycombinator.com\"\n\n"
        "Equip your agent in 60 seconds:\n"
        "pip install x402-cleanweb-agent\n\n"
        f"🌐 Production Gateway: {GCP_URL}\n"
        f"🛡️ Verified Contracts on Polygon, Base & Arbitrum\n"
        f"📜 Open Architecture: {GITHUB_URL} (3/3)\n"
        "#Python #AutonomousAgents #EIP712 #SmartContracts"
    )
]

# 3. 순수 B2A 자율 에이전트 개발자 스레드 (B2A Autonomous Agent Infrastructure Thread)
B2A_AGENT_THREAD = [
    (
        "Building AI Agents with LangChain, CrewAI, AutoGen, or Eliza? 🤖🛑\n\n"
        "Stop burning 87% of your LLM context budget on messy HTML ads & boilerplate noise!\n\n"
        "Introducing x402 CleanWeb Agent: The 100% Autonomous B2A (Machine-to-Machine) Data Oracle with HTTP 402 Micropayments 👇 (1/3)\n"
        f"📦 PyPI: {PYPI_URL}\n"
        "#AIAgents #LangChain #CrewAI #Web3 #MCP #x402"
    ),
    (
        "⚡ Why Autonomous Agents choose x402:\n\n"
        "• 📉 87.0% Token Noise Reduction (-86.2% Net LLM Inference Costs)\n"
        "• 🛡️ Ingress Security Gate: Real-time Prompt Injection & Jailbreak Defense\n"
        "• 🔐 Multi-Chain EIP-712 Cryptographic Signatures (Polygon, Base, Arbitrum)\n"
        "• ⚡ Zero-Human In-the-Loop: 35ms Agent Vault settlement via X-Vault-Key\n\n"
        "(2/3)"
    ),
    (
        "🚀 Integrate into your AI agents in under 1 minute:\n\n"
        "pip install x402-cleanweb-agent\n\n"
        f"🌐 Live Production Gateway: {GCP_URL}\n"
        f"🏛️ Smart Contracts Verified: Polygon | Base | Arbitrum\n"
        f"📜 Docs & Architecture: {GITHUB_URL}\n\n"
        "#Python #AutonomousAgents #EIP712 #Solidity (3/3)"
    )
]

def build_status_alert_tweet():
    """자율 AI 에이전트 빌더를 위한 핵심 소구점 강조 단일 트윗"""
    return (
        "🤖 [B2A Autonomous Agent Data Infrastructure]\n\n"
        "자율 AI 에이전트의 웹 브라우징 토큰 비용을 87% 절감하고, 위변조 방지 EIP-712 암호학적 오라클 서명을 즉시 발급합니다.\n\n"
        "• LangChain / CrewAI / AutoGen 1분 연동\n"
        "• Polygon, Base, Arbitrum USDC 머신 결제\n"
        "• 3회 무료 샌드박스 테스트 지원\n\n"
        f"⚡ 1초 테스트: {GCP_URL}/r/https://news.ycombinator.com\n\n"
        "#AIAgents #자율에이전트 #LangChain #Web3 #MCP"
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
    print(" 3. 🤖 순수 B2A 자율 에이전트 인프라 스레드 게시 (LangChain/CrewAI/AutoGen 개발자용)")
    print(" 4. 📄 웹 서비스 UI 소개 단일 트윗 게시")
    print(" 5. ⏰ 백그라운드 정기 자동 알림 스케줄러 실행")
    print(" 6. ⚙️ X API 연동 안내 및 상태 확인")
    print("==========================================================")
    
    choice = input("👉 원하는 작업 번호를 입력하세요 (기본값: 3): ").strip() or "3"
    
    if choice == "1":
        run_post_thread(KOREAN_THREAD, "한국 사용자 서비스 스레드")
    elif choice == "2":
        run_post_thread(GLOBAL_THREAD, "글로벌 사용자 서비스 스레드")
    elif choice == "3":
        run_post_thread(B2A_AGENT_THREAD, "B2A 자율 에이전트 인프라 스레드")
    elif choice == "4":
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
    elif choice == "5":
        hours = input("알림 주기(시간)를 입력하세요 (기본값: 6): ").strip() or "6"
        run_scheduler(int(hours))
    elif choice == "6":
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
        elif arg in ("--b2a", "--auto-b2a"):
            run_post_thread(B2A_AGENT_THREAD, "B2A 자율 에이전트 인프라 스레드")
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
