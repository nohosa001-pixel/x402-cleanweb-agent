import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_gemini_transcript(video_url, api_key=None):
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment.")
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    prompt = f"""You are a professional video transcriber. 
Transcribe and break down this YouTube video into detailed spoken transcripts with precise timestamps:
Video URL: {video_url}

Output Format:
# 🎬 [Video Title]
> **YouTube URL**: {video_url}

## 📜 Spoken Transcript & Timestamps
- **`[MM:SS]`** Spoken text / key dialogue...
"""
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }
    r = requests.post(url, headers=headers, json=payload, timeout=20)
    print("Gemini Status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        candidates = data.get("candidates", [])
        if candidates:
            return candidates[0]["content"]["parts"][0]["text"]
    else:
        print("Gemini Error:", r.text)
    return None

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    res = test_gemini_transcript("https://www.youtube.com/watch?v=aircAruvnKk")
    if res:
        print("--- GEMINI 1.5 FLASH TRANSCRIPT OUTPUT ---")
        print(res[:1000])
