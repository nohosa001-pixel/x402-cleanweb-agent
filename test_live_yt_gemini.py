import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE = 'https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app'
headers = {'X-Agent-Nonce': 'live_yt_gemini_test_002'}
url = f'{BASE}/api/v1/clean-youtube?url=https://www.youtube.com/watch?v=aircAruvnKk'

print("Sending request to:", url)
r = requests.get(url, headers=headers, timeout=30)
print('HTTP Status:', r.status_code)
d = r.json()
print('Title:', d.get('title'))
print('Engine:', d.get('engine'))
print('\n=== GEMINI 3.6 FLASH YOUTUBE REPORT ===\n')
print(d.get('markdown_content', ''))
