"""
PDF Whitepaper and Academic Paper Parser Engine.
"""

import io
import requests
from typing import Dict, Any, Optional
from pypdf import PdfReader


class PDFCleanerEngine:
    """Parses and cleans online PDF research papers and technical whitepapers."""

    def __init__(self, timeout_sec: int = 25):
        self.timeout_sec = timeout_sec

    def clean_pdf(self, url: str, max_pages: int = 30) -> Dict[str, Any]:
        """Downloads and extracts text from a PDF URL."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=self.timeout_sec)
        resp.raise_for_status()

        pdf_file = io.BytesIO(resp.content)
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

        # Extract title from metadata if available
        meta = reader.metadata
        title = meta.title if meta and meta.title else url.split("/")[-1]

        return {
            "url": url,
            "total_pages": total_pages,
            "parsed_pages": pages_to_read,
            "title": title,
            "text_content": full_text,
            "word_count": word_count,
        }


pdf_cleaner_engine = PDFCleanerEngine()
