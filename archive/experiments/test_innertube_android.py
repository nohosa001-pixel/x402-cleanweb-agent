import requests
import json
import re
import xml.etree.ElementTree as ET
import html

def fetch_youtube_captions_via_innertube(video_id):
    url = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json"
    }
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240101.00.00",
                "hl": "en",
                "gl": "US"
            }
        },
        "videoId": video_id
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=8)
        print("InnerTube Status:", r.status_code)
        data = r.json()
        captions = data.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
        print(f"Found {len(captions)} caption tracks via InnerTube Android")
        if captions:
            base_url = captions[0].get("baseUrl")
            print("Caption baseUrl found:", base_url[:80])
            cap_res = requests.get(base_url, timeout=8)
            print("Captions xml status:", cap_res.status_code, "Length:", len(cap_res.text))
            
            # parse xml
            root = ET.fromstring(cap_res.text)
            snippets = []
            for elem in root.findall("text"):
                start = float(elem.get("start", 0))
                text = html.unescape(elem.text or "").strip()
                if text:
                    snippets.append({"start": start, "text": text})
            return snippets
    except Exception as e:
        print("InnerTube error:", e)
    return []

if __name__ == "__main__":
    snips = fetch_youtube_captions_via_innertube("aircAruvnKk")
    print(f"Extracted {len(snips)} snippets:")
    for s in snips[:5]:
        print(" -", s)
