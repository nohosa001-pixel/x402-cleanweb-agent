"""
PDF Whitepaper and Academic Paper Parser Engine.
Extracts structured text from research papers with rich PDF and token reduction analytics.
"""

import io
import time
import requests
from typing import Dict, Any, Optional
from pypdf import PdfReader
from app.cleaners.security import is_safe_url

MAX_PDF_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit


class PDFCleanerEngine:
    """Parses and cleans online PDF research papers and technical whitepapers."""

    def __init__(self, timeout_sec: int = 25):
        self.timeout_sec = timeout_sec

    def clean_pdf(self, url: str, max_pages: int = 30) -> Dict[str, Any]:
        """Downloads and extracts text from a PDF URL."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        if not is_safe_url(url):
            raise ValueError(f"Blocked PDF URL ({url}): Access to local/private network or cloud metadata services is prohibited for security.")

        start_time = time.time()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
        
        # Stream response to prevent memory exhaustion
        resp = requests.get(url, headers=headers, timeout=self.timeout_sec, stream=True)
        resp.raise_for_status()

        content_length = resp.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_PDF_SIZE_BYTES:
            raise ValueError(f"PDF exceeds maximum allowed size of 15MB (got {int(content_length)/(1024*1024):.1f}MB).")

        chunks = []
        downloaded = 0
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                downloaded += len(chunk)
                if downloaded > MAX_PDF_SIZE_BYTES:
                    raise ValueError(f"PDF stream exceeded 15MB limit. Aborted download.")
                chunks.append(chunk)

        pdf_bytes = b"".join(chunks)
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)

        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)

        extracted_text_list = []
        for i in range(pages_to_read):
            page = reader.pages[i]
            t = page.extract_text()
            if t:
                extracted_text_list.append(f"--- [Page {i+1}] ---\n" + t.strip())

        full_text = "\n\n".join(extracted_text_list).strip()
        word_count = len(full_text.split())
        clean_tokens = max(1, len(full_text) // 4)
        raw_estimated_tokens = max(clean_tokens, len(pdf_bytes) // 6)
        saved_tokens = max(0, raw_estimated_tokens - clean_tokens)
        reduction_pct = round((saved_tokens / raw_estimated_tokens) * 100, 1) if raw_estimated_tokens > 0 else 0.0

        # Extract title from metadata if available
        meta = reader.metadata
        title = meta.title if meta and meta.title else url.split("/")[-1]

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "url": url,
            "total_pages": total_pages,
            "parsed_pages": pages_to_read,
            "title": title,
            "text_content": full_text,
            "word_count": word_count,
            "engine": "pypdf_stream_parser",
            "latency_ms": latency_ms,
            "pdf_analytics": {
                "total_pages": total_pages,
                "parsed_pages": pages_to_read,
                "word_count": word_count,
                "estimated_tokens": clean_tokens
            },
            "token_analytics": {
                "raw_html_estimated_tokens": raw_estimated_tokens,
                "clean_markdown_estimated_tokens": clean_tokens,
                "token_reduction_percent": reduction_pct,
                "saved_tokens": saved_tokens
            }
        }


pdf_cleaner_engine = PDFCleanerEngine()

