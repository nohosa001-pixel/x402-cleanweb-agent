"""
Unit tests for Tolerant / Resilient URL Routing (Postel's Law compliance).
Directly tests clean_web and clean_web_post route handlers for parameter aliases.
"""
import unittest
from unittest.mock import patch, MagicMock
from starlette.requests import Request

from app.main import clean_web, clean_web_post
from app.schemas import CleanWebRequest


def create_mock_request(query_params=None, headers=None):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/clean-web",
        "headers": [(k.lower().encode("latin1"), v.encode("latin1")) for k, v in (headers or {}).items()],
        "query_string": "&".join(f"{k}={v}" for k, v in (query_params or {}).items()).encode("latin1"),
        "client": ("127.0.0.1", 12345),
    }
    return Request(scope)


class TestTolerantRouting(unittest.TestCase):
    @patch("app.main.web_cleaner_engine.fetch_and_clean")
    @patch("app.main.x402_verifier.verify_request")
    def test_get_clean_web_canonical_url(self, mock_verify, mock_clean):
        mock_verify.return_value = (True, None, None)
        mock_clean.return_value = {
            "markdown_content": "# Canonical\nTest content.",
            "title": "Canonical Page",
            "url": "https://example.com",
            "word_count": 50,
            "estimated_reading_time_sec": 10,
            "engine": "cleanweb_fast_parser"
        }

        req = create_mock_request(query_params={"url": "https://example.com"})
        res = clean_web(request=req, url="https://example.com")
        self.assertEqual(res.status, "success")
        self.assertEqual(res.url, "https://example.com")

    @patch("app.main.web_cleaner_engine.fetch_and_clean")
    @patch("app.main.x402_verifier.verify_request")
    def test_get_clean_web_target_url_alias(self, mock_verify, mock_clean):
        mock_verify.return_value = (True, None, None)
        mock_clean.return_value = {
            "markdown_content": "# Target URL Alias\nTest content.",
            "title": "Alias Page",
            "url": "https://example.com/target",
            "word_count": 50,
            "estimated_reading_time_sec": 10
        }

        # Passing target_url alias instead of url
        req = create_mock_request(query_params={"target_url": "https://example.com/target"})
        res = clean_web(request=req, target_url="https://example.com/target")
        self.assertEqual(res.status, "success")
        self.assertEqual(res.url, "https://example.com/target")
        mock_clean.assert_called_with(
            "https://example.com/target",
            respect_robots_txt=False,
            max_tokens=None,
            preserve_alt_text=True,
            dynamic_render=False,
            scroll_depth=0
        )

    @patch("app.main.web_cleaner_engine.fetch_and_clean")
    @patch("app.main.x402_verifier.verify_request")
    def test_get_clean_web_link_alias(self, mock_verify, mock_clean):
        mock_verify.return_value = (True, None, None)
        mock_clean.return_value = {
            "markdown_content": "# Link Alias\nTest content.",
            "title": "Link Page",
            "url": "https://example.com/link",
            "word_count": 50,
            "estimated_reading_time_sec": 10
        }

        req = create_mock_request(query_params={"link": "https://example.com/link"})
        res = clean_web(request=req, link="https://example.com/link")
        self.assertEqual(res.status, "success")
        self.assertEqual(res.url, "https://example.com/link")

    @patch("app.main.web_cleaner_engine.fetch_and_clean")
    @patch("app.main.x402_verifier.verify_request")
    def test_post_clean_web_target_url_alias(self, mock_verify, mock_clean):
        mock_verify.return_value = (True, None, None)
        mock_clean.return_value = {
            "markdown_content": "# POST Target URL\nTest content.",
            "title": "POST Alias Page",
            "url": "https://example.com/post-alias",
            "word_count": 50,
            "estimated_reading_time_sec": 10
        }

        # Pydantic CleanWebRequest auto-normalizes target_url -> url
        req = create_mock_request()
        body = CleanWebRequest(target_url="https://example.com/post-alias")
        self.assertEqual(body.url, "https://example.com/post-alias")

        res = clean_web_post(request=req, body=body)
        self.assertEqual(res.status, "success")
        self.assertEqual(res.url, "https://example.com/post-alias")

    @patch("app.main.web_cleaner_engine.fetch_and_clean")
    @patch("app.main.x402_verifier.verify_request")
    def test_post_clean_web_input_alias_sentence_extraction(self, mock_verify, mock_clean):
        mock_verify.return_value = (True, None, None)
        mock_clean.return_value = {
            "markdown_content": "# Extracted\nTest content.",
            "title": "Embedded URL Page",
            "url": "https://news.ycombinator.com",
            "word_count": 50,
            "estimated_reading_time_sec": 10
        }

        # Natural language query containing URL
        req = create_mock_request()
        body = CleanWebRequest(input="Please fetch https://news.ycombinator.com for my agent")
        self.assertEqual(body.url, "https://news.ycombinator.com")

        res = clean_web_post(request=req, body=body)
        self.assertEqual(res.status, "success")
        mock_clean.assert_called_with(
            "https://news.ycombinator.com",
            respect_robots_txt=False,
            max_tokens=None,
            preserve_alt_text=True,
            dynamic_render=False,
            scroll_depth=0
        )


if __name__ == "__main__":
    unittest.main()
