import yt_dlp
import json
import requests

def format_sec(ms):
    sec = int(ms // 1000)
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"

def extract_full_youtube_transcript(video_id, preferred_langs=['en', 'ko']):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': preferred_langs,
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', f"YouTube Video ({video_id})")
        uploader = info.get('uploader', 'Creator')
        duration = info.get('duration', 0)
        subtitles = info.get('subtitles', {}) or {}
        auto_subtitles = info.get('automatic_captions', {}) or {}
        
        target_list = None
        for lang in preferred_langs:
            if lang in subtitles:
                target_list = subtitles[lang]
                break
            elif lang in auto_subtitles:
                target_list = auto_subtitles[lang]
                break
                
        if not target_list:
            # fallback to first available
            all_subs = {**subtitles, **auto_subtitles}
            if all_subs:
                target_list = list(all_subs.values())[0]

        lines = [
            f"# 🎬 {title}\n",
            f"> **Creator**: {uploader} | **Duration**: {duration // 60}m {duration % 60}s | **YouTube URL**: https://www.youtube.com/watch?v={video_id}\n",
            "## 📜 Full Spoken Transcript & Timestamps\n"
        ]

        if target_list:
            # pick json3 format
            sub_url = None
            for s in target_list:
                if s.get('ext') == 'json3':
                    sub_url = s.get('url')
                    break
            if not sub_url and target_list:
                sub_url = target_list[0].get('url')
                
            if sub_url:
                r = requests.get(sub_url, timeout=10)
                sub_data = r.json()
                events = sub_data.get('events', [])
                for ev in events:
                    t_start = ev.get('tStartMs', 0)
                    time_str = format_sec(t_start)
                    segs = ev.get('segs', [])
                    text = "".join(seg.get('utf8', '') for seg in segs).strip()
                    if text and text != "\n":
                        lines.append(f"- **`[{time_str}]`** {text}")
                        
        return "\n".join(lines)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    md = extract_full_youtube_transcript("aircAruvnKk")
    print(f"Total lines: {len(md.splitlines())}")
    print("\n--- FIRST 15 LINES OF REAL SPOKEN TRANSCRIPT ---")
    print("\n".join(md.splitlines()[:18]))
