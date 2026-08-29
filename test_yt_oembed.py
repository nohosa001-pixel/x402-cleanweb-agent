import requests
import json
from bs4 import BeautifulSoup
import re

def scrape_youtube_page(video_id):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    # 1. oEmbed
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    oembed_res = requests.get(oembed_url, headers=headers, timeout=5)
    oembed_data = oembed_res.json() if oembed_res.status_code == 200 else {}
    title = oembed_data.get("title", f"YouTube Video ({video_id})")
    author = oembed_data.get("author_name", "YouTube Creator")
    
    # 2. Watch HTML page
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    page_res = requests.get(watch_url, headers=headers, timeout=8)
    soup = BeautifulSoup(page_res.text, "html.parser")
    
    desc = ""
    desc_meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if desc_meta and desc_meta.get("content"):
        desc = desc_meta["content"].strip()
        
    keywords = ""
    kw_meta = soup.find("meta", attrs={"name": "keywords"})
    if kw_meta and kw_meta.get("content"):
        keywords = kw_meta["content"].strip()

    chapters = []
    if desc:
        for line in desc.split("\n"):
            m = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)\s*(?:-)?\s*(.*)", line)
            if m and len(m.group(2).strip()) > 2:
                chapters.append(f"- **`[{m.group(1)}]`** {m.group(2).strip()}")

    lines = [
        f"# 🎬 {title}\n",
        f"> **Creator**: {author} | **YouTube URL**: https://www.youtube.com/watch?v={video_id}\n"
    ]
    if chapters:
        lines.append("## 📌 Key Chapters & Timestamps\n")
        lines.extend(chapters)
        lines.append("\n")
        
    if desc:
        lines.append("## 📝 Video Summary & Description\n")
        lines.append(desc)
        lines.append("\n")
        
    if keywords:
        lines.append(f"> **Tags & Topics**: `{keywords}`")
        
    return "\n".join(lines)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    md = scrape_youtube_page("aircAruvnKk")
    print("Length:", len(md))
    print(md[:600])
