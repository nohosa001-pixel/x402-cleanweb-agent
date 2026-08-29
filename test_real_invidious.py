import requests
import re
import json

instances = [
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://invidious.f5.si",
    "https://yt.chocolatemoo53.com",
    "https://invidious.tiekoetter.com",
    "https://iv.melmac.space"
]

for uri in instances:
    try:
        print(f"Testing {uri} ...")
        r = requests.get(f"{uri}/api/v1/captions/aircAruvnKk", timeout=4)
        print("Status:", r.status_code)
        if r.status_code == 200:
            caps = r.json().get("captions", [])
            print(f"Captions count: {len(caps)}")
            if caps:
                sub_url = f"{uri}{caps[0]['url']}"
                sub_r = requests.get(sub_url, timeout=5)
                print(f"Downloaded sub length: {len(sub_r.text)}")
                print(sub_r.text[:300])
                break
    except Exception as e:
        print(f"Error {uri}: {e}")
