import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE = 'https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app'
headers = {'X-Agent-Nonce': 'live_batch_openai_audit_002'}
payload = {
    'urls': [
        'https://openai.com/news/',
        'https://www.anthropic.com/news',
        'https://deepmind.google/news/'
    ],
    'density': 'standard'
}

r = requests.post(f'{BASE}/api/v1/batch-clean', headers=headers, json=payload, timeout=30)
print('HTTP Status:', r.status_code)
d = r.json()
print(f"Batch Success: {d.get('successful_count')} / {d.get('total_urls')}")
for item in d.get('results', []):
    status_str = item.get('status', '').upper()
    url_str = item.get('url')
    title_str = item.get('title')
    print(f" - [{status_str}] {url_str} => Title: {title_str}")
