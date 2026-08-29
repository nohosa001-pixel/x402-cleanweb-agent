"""
Unit and Integration Tests for Cleaners (Web, YouTube, PDF, Batch).
"""

import pytest
from app.cleaners.web_engine import web_cleaner_engine
from app.cleaners.youtube_engine import youtube_cleaner_engine
from app.cleaners.pdf_engine import pdf_cleaner_engine


def test_web_cleaner_example_domain():
    res = web_cleaner_engine.fetch_and_clean("https://example.com")
    assert res["url"].startswith("https://")
    assert "Example Domain" in res["title"]
    assert len(res["markdown_content"]) > 20
    assert res["word_count"] > 0


def test_youtube_cleaner_video_id():
    v_id = youtube_cleaner_engine.extract_video_id("https://www.youtube.com/watch?v=aircAruvnKk")
    assert v_id == "aircAruvnKk"
    
    v_id_short = youtube_cleaner_engine.extract_video_id("https://youtu.be/aircAruvnKk")
    assert v_id_short == "aircAruvnKk"


def test_youtube_cleaner_execution():
    res = youtube_cleaner_engine.clean_youtube("https://www.youtube.com/watch?v=aircAruvnKk")
    assert res["video_id"] == "aircAruvnKk"
    assert res["title"] is not None
    assert len(res["transcript"]) > 0


def test_batch_clean_concurrent():
    urls = ["https://example.com", "https://httpbin.org/html"]
    results = web_cleaner_engine.batch_clean(urls)
    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)
