import requests
import re
import json
import xml.etree.ElementTree as ET

def fetch_youtube_direct_captions(video_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8'
    }
    url = f"https://www.youtube.com/watch?v=jNQXAC9IVRw"
    res = requests.get(url, headers=headers)
    
    # Extract player response
    match = re.search(r'"captionTracks":(\[.*?\])', res.text)
    if not match:
        print("captionTracks not found")
        return []
    
    tracks = json.loads(match.group(1))
    print(f"Found {len(tracks)} caption tracks")
    caption_url = tracks[0].get("baseUrl") + "&fmt=json3"
    print("Caption URL with json3:", caption_url)
    cap_res = requests.get(caption_url, headers=headers)
    print("Caption status:", cap_res.status_code, "Length:", len(cap_res.text))
    print("Sample response:", cap_res.text[:300])
    return []

if __name__ == "__main__":
    snips = fetch_youtube_direct_captions("jNQXAC9IVRw")
    print(f"Extracted {len(snips)} snippets:")
    for s in snips[:3]:
        print(" -", s)
