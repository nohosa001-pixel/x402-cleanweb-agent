"""
High-Performance Web Scraping and Readability Markdown Cleaner Engine.
"""

import re
import requests
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup, Comment


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


class WebCleanerEngine:
    """Extracts high-density LLM-ready markdown from any raw website URL."""

    def __init__(self, timeout_sec: int = 15):
        self.timeout_sec = timeout_sec

    def fetch_and_clean(self, url: str) -> Dict[str, Any]:
        """Fetches a URL and parses it into clean Markdown."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=self.timeout_sec)
        resp.raise_for_status()

        # Handle encoding
        if resp.encoding is None or resp.encoding == "ISO-8859-1":
            resp.encoding = resp.apparent_encoding or "utf-8"

        html_text = resp.text
        soup = BeautifulSoup(html_text, "html.parser")

        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else url

        # Remove noisy tags
        unwanted_tags = [
            "script", "style", "noscript", "iframe", "svg", "canvas", "header",
            "footer", "nav", "aside", "form", "button", "input", "select", "option"
        ]
        for tag in soup(unwanted_tags):
            tag.decompose()

        # Remove HTML comments
        for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
            comment.extract()

        # Target main content container if present
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", {"id": re.compile(r"content|main|article|body", re.I)})
            or soup.find("div", {"class": re.compile(r"content|main|article|post|body", re.I)})
            or soup.body
            or soup
        )

        # Convert to Markdown
        markdown_lines = []
        if title:
            markdown_lines.append(f"# {title}\n")

        for elem in main_content.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "pre", "blockquote", "table"]):
            tag_name = elem.name.lower()
            text = elem.get_text(separator=" ", strip=True)
            if not text or len(text) < 2:
                continue

            if tag_name == "h1":
                markdown_lines.append(f"\n# {text}\n")
            elif tag_name == "h2":
                markdown_lines.append(f"\n## {text}\n")
            elif tag_name == "h3":
                markdown_lines.append(f"\n### {text}\n")
            elif tag_name == "h4":
                markdown_lines.append(f"\n#### {text}\n")
            elif tag_name == "p":
                markdown_lines.append(f"\n{text}\n")
            elif tag_name in ("ul", "ol"):
                items = elem.find_all("li")
                for li in items:
                    li_text = li.get_text(strip=True)
                    if li_text:
                        markdown_lines.append(f"- {li_text}")
                markdown_lines.append("")
            elif tag_name == "blockquote":
                markdown_lines.append(f"\n> {text}\n")
            elif tag_name == "pre":
                markdown_lines.append(f"\n```\n{text}\n```\n")

        markdown_body = "\n".join(markdown_lines).strip()
        if not markdown_body or len(markdown_body) < 50:
            # Fallback to plain text
            markdown_body = f"# {title}\n\n" + soup.get_text(separator="\n", strip=True)

        # Normalize multiple newlines
        markdown_body = re.sub(r"\n{3,}", "\n\n", markdown_body)

        words = markdown_body.split()
        word_count = len(words)
        reading_time_sec = max(1, int(word_count / 3.5))  # ~210 wpm

        return {
            "url": url,
            "title": title,
            "markdown_content": markdown_body,
            "word_count": word_count,
            "estimated_reading_time_sec": reading_time_sec,
        }

    def batch_clean(self, urls: List[str], max_workers: int = 5) -> List[Dict[str, Any]]:
        """Concurrently cleans up to 10 URLs."""
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.fetch_and_clean, u): u for u in urls[:10]}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    res = future.result()
                    results.append({
                        "url": url,
                        "status": "success",
                        "title": res.get("title"),
                        "markdown_content": res.get("markdown_content"),
                    })
                except Exception as e:
                    results.append({
                        "url": url,
                        "status": "error",
                        "error": str(e),
                    })
        return results


web_cleaner_engine = WebCleanerEngine()
