import requests
import re
import json
import xml.etree.ElementTree as ET
import html

def test_proxy_youtube(video_id):
    # Free public CORS/HTTP proxies to bypass Cloud IP ban
    proxies = [
        f"https://api.allorigins.win/raw?url=https://www.youtube.com/watch?v={video_id}",
        f"https://corsproxy.io/?url=https://www.youtube.com/watch?v={video_id}"
    ]
    for p in proxies:
        try:
            print("Trying proxy:", p[:40])
            res = requests.get(p, timeout=8)
            if res.status_code == 200:
                match = re.search(r'"captionTracks":(\[.*?\])', res.text)
                if match:
                    tracks = json.loads(match.group(1))
                    base_url = tracks[0].get("baseUrl")
                    if base_url:
                        # fetch caption xml via proxy as well
                        cap_proxy = f"https://api.allorigins.win/raw?url={requests.utils.quote(base_url)}"
                        cap_res = requests.get(cap_proxy, timeout=8)
                        root = ET.fromstring(cap_res.text)
                        snippets = []
                        for elem in root.findall("text"):
                            snippets.append({
                                "start": float(elem.get("start", 0)),
                                "text": html.unescape(elem.text or "").strip()
                            })
                        return snippets
        except Exception as e:
            print("Proxy failed:", e)
    return []

if __name__ == "__main__":
    snips = test_proxy_youtube("aircAruvnKk")
    print(f"Result count: {len(snips)}")
    for s in snips[:3]:
        print(s)
