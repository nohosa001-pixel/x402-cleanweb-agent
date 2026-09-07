import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

LIVE_GCP_URL = "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/api/v1/clean-youtube"
headers = {"X-Agent-Nonce": "gcp_direct_verification_nonce_99"}
params = {"url": "https://www.youtube.com/watch?v=aircAruvnKk"}

print("================================================================")
print(f"📡 [GCP Cloud Run] Direct Live Request to: {LIVE_GCP_URL}")
print(f"🎯 Target YouTube: {params['url']}")
print("================================================================\n")

response = requests.get(LIVE_GCP_URL, headers=headers, params=params, timeout=40)

print(f"✅ HTTP Status Code: {response.status_code}")
data = response.json()

print(f"🎬 Video Title    : {data.get('title')}")
print(f"👤 Creator / Channel: {data.get('author')}")
print(f"🧠 AI Engine      : {data.get('engine')}")
print(f"📊 Analytics      : {json.dumps(data.get('transcript_analytics', {}), indent=2)}")
print(f"🔐 Auth Mode      : {json.dumps(data.get('auth', {}), indent=2)}")
print("\n" + "="*60)
print("📜 [GCP Cloud Run Response: Full Clean Markdown Content]")
print("="*60 + "\n")
print(data.get('markdown_content', ''))
print("\n" + "="*60)
