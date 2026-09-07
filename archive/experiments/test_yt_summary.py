import requests
import json
import re

def get_youtube_video_summary(video_id):
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
    r = requests.post(url, headers=headers, json=payload, timeout=8)
    data = r.json()
    details = data.get("videoDetails", {})
    title = details.get("title", f"YouTube Video ({video_id})")
    author = details.get("author", "YouTube Creator")
    desc = details.get("shortDescription", "")
    length_sec = int(details.get("lengthSeconds", 0))
    
    # Extract timestamp chapters from description if any
    chapters = []
    for line in desc.split("\n"):
        match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)\s*(?:-)?\s*(.*)", line)
        if match:
            chapters.append(f"- **`[{match.group(1)}]`** {match.group(2).strip()}")
            
    md_lines = [
        f"# 🎬 {title}\n",
        f"> **Channel**: {author} | **Duration**: {length_sec // 60}m {length_sec % 60}s",
        f"> **YouTube URL**: https://www.youtube.com/watch?v={video_id}\n"
    ]
    if chapters:
        md_lines.append("## 📌 Video Chapters & Timestamps\n")
        md_lines.extend(chapters)
        md_lines.append("\n")
        
    md_lines.append("## 📜 Video Overview & Description\n")
    md_lines.append(desc.strip())
    
    return "\n".join(md_lines)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    md = get_youtube_video_summary("aircAruvnKk")
    print(md[:1000])
