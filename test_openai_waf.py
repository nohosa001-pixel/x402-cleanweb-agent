import requests
from bs4 import BeautifulSoup

def test_fetch_openai():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # 1. Direct fetch
    try:
        r = requests.get('https://openai.com/news/', headers=headers, timeout=10)
        print("Direct OpenAI News status:", r.status_code, "Length:", len(r.text))
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print("Direct failed:", e)
        
    # 2. Open Relay / Fallback fetch
    try:
        r2 = requests.get('https://r.jina.ai/https://openai.com/news/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        print("Relay OpenAI News status:", r2.status_code, "Length:", len(r2.text))
        if r2.status_code == 200:
            return r2.text
    except Exception as e:
        print("Relay failed:", e)

    return None

if __name__ == "__main__":
    content = test_fetch_openai()
    if content:
        print("First 300 chars:\n", content[:300])
