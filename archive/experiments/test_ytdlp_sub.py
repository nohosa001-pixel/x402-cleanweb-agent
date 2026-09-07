import yt_dlp
import json

def get_subtitles_via_ytdlp(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'ko'],
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        subtitles = info.get('subtitles', {})
        auto_subtitles = info.get('automatic_captions', {})
        print("Manual Subtitles keys:", list(subtitles.keys()))
        print("Auto Subtitles keys:", list(auto_subtitles.keys())[:10])
        
        target_subs = subtitles.get('en') or auto_subtitles.get('en') or []
        for s in target_subs:
            if s.get('ext') == 'json3' or s.get('ext') == 'vtt' or s.get('ext') == 'srv3':
                print("Found format:", s.get('ext'), "URL:", s.get('url')[:80])
                import requests
                r = requests.get(s['url'])
                print("Downloaded format length:", len(r.text))
                return r.text
    return None

if __name__ == "__main__":
    text = get_subtitles_via_ytdlp("aircAruvnKk")
    if text:
        print("Preview:\n", text[:500])
