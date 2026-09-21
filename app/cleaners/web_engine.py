"""
High-Performance Web Scraping and Readability Markdown Cleaner Engine.
Features WAF Bypass Smart Headers, Jina Reader Fallback Pipeline, and Deep Token Reduction Analytics.
"""

import re
import time
import threading
import requests
from urllib.parse import urlparse, urljoin
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup, Comment
from app.cleaners.security import is_safe_url


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


def normalize_url(url: str) -> str:
    """Robustly normalizes raw URLs, fixing collapsed slashes from reverse proxies and missing protocols."""
    cleaned = url.strip()
    cleaned = re.sub(r'^(https?):/+', r'\1://', cleaned, flags=re.IGNORECASE)
    if not re.match(r'^https?://', cleaned, re.IGNORECASE):
        cleaned = 'https://' + cleaned
    return cleaned


class WebCleanerEngine:
    """Extracts high-density LLM-ready markdown from any raw website URL with resilient fallbacks and connection pooling."""

    def __init__(self, timeout_sec: int = 15):
        self.timeout_sec = timeout_sec
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=100)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._cache_ttl = 60.0  # 60s in-memory TTL for agent performance
        self._cache_lock = threading.Lock()

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        with self._cache_lock:
            if key in self._cache:
                ts, val = self._cache[key]
                if time.time() - ts < self._cache_ttl:
                    return val.copy()
                del self._cache[key]
        return None

    def _set_cache(self, key: str, val: Dict[str, Any]):
        with self._cache_lock:
            if len(self._cache) > 500:
                oldest = min(self._cache.keys(), key=lambda k: self._cache[k][0])
                del self._cache[oldest]
            self._cache[key] = (time.time(), val.copy())

    def check_robots_allowed(self, target_url: str) -> bool:
        """Lightweight robots.txt Disallow rule check."""
        try:
            parsed = urlparse(target_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            r = self.session.get(robots_url, timeout=3)
            if r.status_code == 200:
                path = parsed.path or "/"
                for line in r.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith("disallow:"):
                        dis_path = line.split(":", 1)[1].strip()
                        if dis_path == "/" or (dis_path and path.startswith(dis_path)):
                            return False
        except Exception:
            pass
        return True

    def _fetch_jina_fallback(self, url: str) -> Optional[Dict[str, Any]]:
        """Fallback to Jina Reader (r.jina.ai) when direct scraping faces strict Cloudflare/WAF."""
        try:
            jina_url = f"https://r.jina.ai/{url}"
            headers = {"Accept": "text/markdown", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = self.session.get(jina_url, headers=headers, timeout=12)
            if r.status_code == 200 and len(r.text) > 100:
                md_content = r.text.strip()
                title_match = re.search(r"^Title:\s*(.+)$", md_content, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else url
                
                words = md_content.split()
                word_count = len(words)
                clean_tokens = max(1, len(md_content) // 4)
                raw_tokens = clean_tokens * 8  # estimated typical raw html ratio
                saved = raw_tokens - clean_tokens
                pct = round((saved / raw_tokens) * 100, 1)

                return {
                    "url": url,
                    "title": title,
                    "markdown_content": md_content,
                    "word_count": word_count,
                    "estimated_reading_time_sec": max(1, int(word_count / 3.5)),
                    "engine": "jina_reader_waf_bypass",
                    "token_analytics": {
                        "raw_html_estimated_tokens": raw_tokens,
                        "clean_markdown_estimated_tokens": clean_tokens,
                        "token_reduction_percent": pct,
                        "saved_tokens": saved
                    }
                }
        except Exception:
            pass
        return None

    def fetch_and_clean(self, url: str, respect_robots_txt: bool = False, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Fetches a URL and parses it into clean Markdown with automatic WAF fallback, connection pooling, and token metrics."""
        url = normalize_url(url)

        if not is_safe_url(url):
            raise ValueError(f"Blocked URL ({url}): Access to local/private network or cloud metadata services is prohibited for security.")

        cache_key = f"{url}_robots_{respect_robots_txt}_max_{max_tokens}"
        cached = self._get_from_cache(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        if respect_robots_txt and not self.check_robots_allowed(url):
            blocked_res = {
                "url": url,
                "title": "Access Blocked by Robots.txt",
                "markdown_content": f"# Notice: Scraping disallowed by {urlparse(url).netloc} robots.txt policy.",
                "word_count": 8,
                "estimated_reading_time_sec": 1,
                "engine": "robots_txt_enforcement",
                "latency_ms": 1.0,
                "token_analytics": {
                    "raw_html_estimated_tokens": 8,
                    "clean_markdown_estimated_tokens": 8,
                    "token_reduction_percent": 0.0,
                    "saved_tokens": 0
                }
            }
            self._set_cache(cache_key, blocked_res)
            return blocked_res

        start_time = time.time()
        resp = None
        try:
            resp = self.session.get(url, timeout=self.timeout_sec)
            resp.raise_for_status()
        except Exception as primary_err:
            # Try Jina Reader Fallback
            jina_res = self._fetch_jina_fallback(url)
            if jina_res:
                jina_res["latency_ms"] = round((time.time() - start_time) * 1000, 2)
                self._set_cache(cache_key, jina_res)
                return jina_res
            raise primary_err

        # Safeguard: Protect against memory bombs and runaway payloads
        content_length = resp.headers.get("Content-Length")
        if content_length:
            try:
                if int(content_length) > 10 * 1024 * 1024:
                    raise ValueError(f"Target webpage exceeds maximum allowed size of 10MB (got {int(content_length)/(1024*1024):.1f}MB).")
            except ValueError as ve:
                if "exceeds maximum" in str(ve):
                    raise ve

        html_text = resp.text[:2_000_000]
        raw_tokens = max(1, len(html_text) // 4)
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

        # If still too short, try Jina fallback
        if len(markdown_body) < 100:
            jina_res = self._fetch_jina_fallback(url)
            if jina_res:
                jina_res["latency_ms"] = round((time.time() - start_time) * 1000, 2)
                return jina_res

        # Normalize multiple newlines
        markdown_body = re.sub(r"\n{3,}", "\n\n", markdown_body)

        # Apply agent-specified max_tokens limit if requested
        if max_tokens and max_tokens > 0:
            char_limit = max_tokens * 4
            if len(markdown_body) > char_limit:
                markdown_body = markdown_body[:char_limit].rstrip() + "\n\n... [Content Truncated by max_tokens limit] ..."

        words = markdown_body.split()
        word_count = len(words)
        reading_time_sec = max(1, int(word_count / 3.5))  # ~210 wpm

        clean_tokens = max(1, len(markdown_body) // 4)
        saved_tokens = max(0, raw_tokens - clean_tokens)
        reduction_pct = round((saved_tokens / raw_tokens) * 100, 1) if raw_tokens > 0 else 0.0

        latency_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "url": url,
            "title": title,
            "markdown_content": markdown_body,
            "word_count": word_count,
            "estimated_reading_time_sec": reading_time_sec,
            "engine": "cleanweb_fast_parser",
            "latency_ms": latency_ms,
            "token_analytics": {
                "raw_html_estimated_tokens": raw_tokens,
                "clean_markdown_estimated_tokens": clean_tokens,
                "token_reduction_percent": reduction_pct,
                "saved_tokens": saved_tokens
            }
        }
        self._set_cache(cache_key, result)
        return result

    def batch_clean(self, urls: List[str], max_workers: int = 5) -> List[Dict[str, Any]]:
        """Concurrently cleans up to 10 URLs with token reduction analytics."""
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
                        "word_count": res.get("word_count"),
                        "token_analytics": res.get("token_analytics")
                    })
                except Exception as e:
                    results.append({
                        "url": url,
                        "status": "error",
                        "error": str(e),
                    })
        return results

    def fetch_plain_text(self, url: str) -> Dict[str, Any]:
        """
        Fetches and extracts raw plain text stripped of HTML tags for RAG vector embeddings.
        """
        clean_res = self.fetch_and_clean(url)
        # Strip markdown syntax for pure embedding text
        raw_text = clean_res.get("markdown_content", "")
        # Remove headers markdown, backticks, links
        text_only = re.sub(r"#+\s*", "", raw_text)
        text_only = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text_only)
        text_only = re.sub(r"`{1,3}.*?`{1,3}", "", text_only, flags=re.DOTALL)
        text_only = re.sub(r"\n{2,}", "\n", text_only).strip()

        words = text_only.split()
        return {
            "url": clean_res.get("url", url),
            "title": clean_res.get("title", ""),
            "plain_text": text_only,
            "word_count": len(words),
            "token_analytics": clean_res.get("token_analytics")
        }

    def map_website(self, domain_or_url: str, max_links: int = 50) -> Dict[str, Any]:
        """
        Autonomous Agent Site Mapper (Firecrawl /map equivalent).
        Discovers domain sitemap or traverses internal anchor links to return a canonical URL tree.
        """
        target_url = normalize_url(domain_or_url)

        if not is_safe_url(target_url):
            raise ValueError(f"Security Alert: Target URL blocked: {target_url}")

        parsed = urlparse(target_url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        base_origin = f"{parsed.scheme}://{domain}"

        cache_key = f"map_{domain}_{max_links}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        found_urls = set()
        sitemap_detected = False

        # 1. Try standard sitemap.xml endpoints
        sitemap_candidates = [
            f"{base_origin}/sitemap.xml",
            f"{base_origin}/sitemap_index.xml",
        ]
        for s_url in sitemap_candidates:
            try:
                resp = self.session.get(s_url, timeout=6)
                if resp.status_code == 200 and ("<loc>" in resp.text or "<?xml" in resp.text):
                    sitemap_detected = True
                    loc_matches = re.findall(r"<loc>\s*(https?://[^\s<]+)\s*</loc>", resp.text, re.IGNORECASE)
                    for m in loc_matches:
                        p = urlparse(m)
                        if p.netloc == domain or p.netloc.endswith("." + domain):
                            found_urls.add(m.split("#")[0].rstrip("/"))
                            if len(found_urls) >= max_links:
                                break
                    if found_urls:
                        break
            except Exception:
                pass

        # 2. If no sitemap or too few URLs, crawl homepage anchor tags
        if len(found_urls) < max_links:
            try:
                resp = self.session.get(target_url, timeout=self.timeout_sec)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for a in soup.find_all("a", href=True):
                        href = a["href"].strip()
                        if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                            continue
                        full_link = urljoin(target_url, href).split("#")[0].rstrip("/")
                        p = urlparse(full_link)
                        # Check same domain
                        if (p.netloc == domain or p.netloc.endswith("." + domain)) and p.scheme in ("http", "https"):
                            found_urls.add(full_link)
                            if len(found_urls) >= max_links:
                                break
            except Exception:
                pass

        # Always include target_url if empty
        if not found_urls:
            found_urls.add(target_url.rstrip("/"))

        url_list = sorted(list(found_urls))[:max_links]
        res = {
            "url": target_url,
            "domain": domain,
            "total_urls": len(url_list),
            "urls": url_list,
            "sitemap_detected": sitemap_detected,
        }
        self._set_cache(cache_key, res)
        return res


web_cleaner_engine = WebCleanerEngine()


