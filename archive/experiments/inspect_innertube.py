import requests
import json

url = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json"
}
clients = ["ANDROID_TESTSUITE", "TVHTML5", "WEB_EMBEDDED_PLAYER", "IOS"]
for cname in clients:
    payload = {
        "context": {
            "client": {
                "clientName": cname,
                "clientVersion": "2.0" if "TV" in cname else "19.09.37",
                "hl": "en",
                "gl": "US"
            }
        },
        "videoId": "aircAruvnKk"
    }
    r = requests.post(url, headers=headers, json=payload)
    d = r.json()
    has_cap = "captions" in d
    print(f"Client {cname}: Status {r.status_code}, Has Captions: {has_cap}")
    if has_cap:
        tracks = d["captions"].get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
        print(f" -> Tracks found: {len(tracks)}")
        if tracks:
            print(" -> BaseUrl:", tracks[0].get("baseUrl")[:100])
