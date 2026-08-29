import requests
import json

def fetch_youtube_subtitles_via_invidious(video_id):
    # Public active Invidious instances with open CORS/API
    instances = [
        "https://invidious.asir.dev",
        "https://vid.priv.au",
        "https://invidious.jing.rocks",
        "https://yt.drgnz.club",
        "https://invidious.io.lol",
        "https://iv.ggtyler.dev",
        "https://invidious.slipfox.xyz"
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for base in instances:
        try:
            api_url = f"{base}/api/v1/captions/{video_id}"
            print(f"Trying {api_url} ...")
            r = requests.get(api_url, headers=headers, timeout=4)
            if r.status_code == 200:
                captions = r.json().get("captions", [])
                if not captions:
                    continue
                # pick english or first
                target = captions[0]
                for c in captions:
                    if "en" in c.get("languageCode", "").lower():
                        target = c
                        break
                
                # Fetch the VTT / SRT subtitle text
                sub_url = f"{base}{target['url']}"
                print(f"Fetching subtitle from {sub_url} ...")
                sub_res = requests.get(sub_url, headers=headers, timeout=5)
                if sub_res.status_code == 200 and len(sub_res.text) > 100:
                    print(f"SUCCESS from {base}! Length: {len(sub_res.text)}")
                    return sub_res.text
        except Exception as e:
            print(f"Failed on {base}: {e}")
    return None

if __name__ == "__main__":
    vtt = fetch_youtube_subtitles_via_invidious("aircAruvnKk")
    if vtt:
        print("--- SUBTITLE PREVIEW (First 500 chars) ---")
        print(vtt[:500])
    else:
        print("ALL FAILED")
