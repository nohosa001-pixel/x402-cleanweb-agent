import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_enhance_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    
    sample_raw = """[00:01] Welcome everyone to today's lecture on artificial general intelligence and neural networks.
[00:15] Today we're going to discuss transformer attention mechanisms, specifically scaled dot-product attention.
[00:45] When we compute Q, K, V matrices, the dimension scaling factor 1 over square root of d_k prevents softmax saturation.
[01:20] In multi-head attention, we project queries, keys, and values h times with different learned linear projections."""

    prompt = f"""You are an elite AI Video Intelligence Agent.
Convert and enhance this YouTube video content into clean, high-density Markdown.

Video URL: https://www.youtube.com/watch?v=aircAruvnKk
Title: 3Blue1Brown - Attention Mechanism in Transformers
Raw Transcript:
{sample_raw}

Formatting Requirements:
# 🎬 3Blue1Brown - Attention Mechanism in Transformers
> **Source**: https://www.youtube.com/watch?v=aircAruvnKk
> **AI Engine**: Gemini 3.6 Flash Video Intelligence

## 💡 Executive Summary
- 3 key takeaways

## ⏱️ Structured Timestamps & Key Topics
- [MM:SS] format breakdown

## 📜 Cleaned Spoken Notes
"""
    res = requests.post(url, headers={"Content-Type": "application/json"}, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20)
    print("Status:", res.status_code)
    if res.status_code == 200:
        print("Output:\n", res.json()['candidates'][0]['content']['parts'][0]['text'])

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    test_enhance_gemini()
