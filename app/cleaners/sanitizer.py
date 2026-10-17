"""
Cleanweb Multi-Vector Sanitizer & Indirect Prompt Injection Scrubber.
=====================================================================
Enterprise-grade web content purification engine for LLMs and autonomous agents:
1. CSS-based Hidden Injection Neutralization:
   - Font-size: 0px / 0pt / 0em
   - Color transparent / matching background camouflage
   - Display: none / visibility: hidden / opacity: 0
   - Off-screen absolute positioning (-9999px)
   - Text-indent -9999px / zero-dimension overflow hidden
2. Unicode Steganography & Zero-Width Evasion Stripping:
   - Zero-width spaces (\u200B, \u200C, \u200D, \uFEFF, \u2060, \u00AD, \u200E, \u200F)
   - BiDirectional (BiDi) overrides (\u202A-\u202E, \u2066-\u2069)
   - Homoglyph normalization for security-critical keywords
3. Covert-Channel & Data Exfiltration Neutralization:
   - Markdown image leaks: ![leak](https://attacker.com?token=...)
   - HTML <img> tracking pixels with exfil query parameters
   - Secret redaction (EVM private keys, API keys, credentials)
4. Prompt Injection & Jailbreak Scrubbing.
"""

from __future__ import annotations

import hashlib
import html
from html.parser import HTMLParser
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# 1. Unicode & Steganography Constants
# ============================================================================

ZERO_WIDTH_CHARS: Set[str] = {
    "\u200b",  # Zero-width space
    "\u200c",  # Zero-width non-joiner
    "\u200d",  # Zero-width joiner
    "\ufeff",  # Zero-width no-break space (BOM)
    "\u2060",  # Word joiner
    "\u00ad",  # Soft hyphen
    "\u200e",  # Left-to-right mark
    "\u200f",  # Right-to-left mark
}

BIDI_OVERRIDE_CHARS: Set[str] = {
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
    "\u2066", "\u2067", "\u2068", "\u2069"
}

# Cyrillic lookalikes mapping to Latin for obfuscated security evasion detection
HOMOGLYPH_MAP: Dict[str, str] = {
    "\u0430": "a", "\u0441": "c", "\u0435": "e", "\u043e": "o", "\u0440": "p",
    "\u0455": "s", "\u0445": "x", "\u0443": "y", "\u0456": "i", "\u0458": "j",
    "\u0410": "A", "\u0412": "B", "\u0421": "C", "\u0415": "E", "\u041d": "H",
    "\u0406": "I", "\u0408": "J", "\u041a": "K", "\u041c": "M", "\u041e": "O",
    "\u0420": "P", "\u0422": "T", "\u0425": "X", "\u04ae": "Y"
}

# ============================================================================
# 2. CSS Hidden Injection Signatures
# ============================================================================

CSS_HIDDEN_PATTERNS = [
    re.compile(r"display\s*:\s*none", re.IGNORECASE),
    re.compile(r"visibility\s*:\s*hidden", re.IGNORECASE),
    re.compile(r"opacity\s*:\s*0(?:\.0+)?(?!\d)", re.IGNORECASE),
    re.compile(r"font-size\s*:\s*0(?:px|pt|em|rem)?", re.IGNORECASE),
    re.compile(r"position\s*:\s*absolute.*?left\s*:\s*-(?:9999|10000|50000)px", re.IGNORECASE),
    re.compile(r"text-indent\s*:\s*-(?:9999|10000|50000)px", re.IGNORECASE),
    re.compile(r"color\s*:\s*(?:transparent|rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*0\s*\))", re.IGNORECASE),
    re.compile(r"width\s*:\s*0px.*?height\s*:\s*0px.*?overflow\s*:\s*hidden", re.IGNORECASE),
    re.compile(r"max-width\s*:\s*0px.*?max-height\s*:\s*0px", re.IGNORECASE),
]

DANGEROUS_HTML_TAGS = {
    "script", "style", "iframe", "object", "embed", "applet", "base", "link", "meta"
}

EXFIL_PARAM_PATTERN = re.compile(
    r"[?&](?:leak|token|key|secret|data|auth|wallet|exfil|cookie|pwd|session|seed)=",
    re.IGNORECASE
)

INJECTION_PATTERN_SPECS = [
    (r"ignore\s+(?:all\s+)?(?:previous|prior|above|current|system|core|\s+)*\s*(?:instructions?|rules|guidelines|constraints|prompts)", "PROMPT_INJECTION", "CRITICAL", "System instruction override attempt"),
    (r"disregard\s+(?:all\s+)?(?:previous|prior|above|current|system|core|\s+)*\s*(?:instructions?|rules|guidelines|constraints|prompts)", "PROMPT_INJECTION", "CRITICAL", "Prior instruction disregard attempt"),
    (r"system\s*:\s*override", "ROLEPLAY_OVERRIDE", "CRITICAL", "Roleplay/system directive override attempt ('system: override')"),
    (r"as\s+an\s+unfiltered\s+ai", "JAILBREAK_PERSONA", "HIGH", "Persona switch to bypass safety guidelines"),
    (r"base64\.b64decode\(", "OBFUSCATED_PAYLOAD", "HIGH", "Base64 payload decoding vector detected"),
    (r'__import__\([\'"]os[\'"]\)', "DYNAMIC_CODE_EXECUTION", "CRITICAL", "Dynamic OS module import vector"),
    (r"eval\(|exec\(|subprocess\.Popen", "DYNAMIC_CODE_EXECUTION", "CRITICAL", "Arbitrary dynamic code execution invocation"),
    (r"you\s+are\s+now\s+DAN", "JAILBREAK_ATTACK", "CRITICAL", "DAN jailbreak persona attack detected"),
    (r"jailbreak|DAN\s+mode", "JAILBREAK_ATTACK", "HIGH", "DAN jailbreak mode activation trigger"),
    (r"<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]", "PROMPT_BREAKOUT", "HIGH", "LLM chat template delimiter injection"),
    (r"<\/?(?:system|instruction|prompt)>", "PROMPT_BREAKOUT", "HIGH", "System tag breakout/spoofing attempt"),
    (r"\[\/?(?:SYSTEM|INSTRUCTION)\]", "PROMPT_BREAKOUT", "HIGH", "Instruction tag breakout/spoofing attempt"),
    (r"!\[.*?\]\(https?:\/\/[^\s\)]+[\?&](?:leak|token|key|secret|data|auth|wallet|exfil)=[^)\s]+\)", "DATA_EXFILTRATION", "HIGH", "Markdown covert image exfiltration vector"),
    (r"(?:이전|모든)\s*(?:지시|명령|규칙|프롬프트)(?:사항)?(?:을|를)?\s*(?:무시|폐기|취소|잊어)", "PROMPT_INJECTION_KO", "CRITICAL", "한국어 시스템 프롬프트 무시 시도"),
    (r"시스템\s*(?:프롬프트|지침|가이드라인|규칙)(?:을|를)?\s*(?:출력|알려|공개|유출)", "PROMPT_INJECTION_KO", "CRITICAL", "한국어 시스템 프롬프트 유출 시도"),
    (r"탈옥\s*모드|제한\s*해제|검열\s*해제", "JAILBREAK_KO", "CRITICAL", "한국어 LLM 탈옥 시도"),
    (r"(?:비밀번호|개인키|프라이빗\s*키|API\s*키)(?:를|을)?\s*(?:유출|전송|알려|출력)", "SECRET_LEAK_KO", "CRITICAL", "한국어 비밀키 유출 시도")
]

SECRET_PATTERNS = [
    r"0x[a-fA-F0-9]{64}",                                      # EVM 32-Byte Private Key
    r"sk-[a-zA-Z0-9]{32,}",                                    # OpenAI / LLM API Key
    r"sk-proj-[a-zA-Z0-9_-]{40,}",                             # OpenAI Project Key
    r"sk-ant-[a-zA-Z0-9_-]{32,}",                              # Anthropic API Key
    r"AIzaSy[a-zA-Z0-9_-]{30,40}",                             # Google Gemini / Cloud API Key
    r"hf_[a-zA-Z0-9]{30,}",                                    # HuggingFace Access Token
    r"ghp_[a-zA-Z0-9]{36}",                                    # GitHub Personal Access Token
    r"github_pat_[a-zA-Z0-9_]{82}",                            # GitHub Fine-grained PAT
    r"AKIA[0-9A-Z]{16}",                                       # AWS Access Key ID
    r"gsk_[a-zA-Z0-9]{30,}",                                   # Groq API Key
    r"ds-[a-zA-Z0-9]{30,}",                                    # DeepSeek API Key
    r"pplx-[a-zA-Z0-9]{48}",                                   # Perplexity API Key
    r"mis_[a-zA-Z0-9]{32,}",                                   # Mistral API Key
    r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", # JWT Secret Token
    r"-----BEGIN (?:RSA|EC|DSA|OPENSSH|PGP|PRIVATE) KEY-----"  # Private Key Block
]


class CleanwebHTMLParser(HTMLParser):
    """Parses HTML, detects hidden text containers, strips scripts and dangerous tags."""

    def __init__(self):
        super().__init__()
        self.output_pieces: List[str] = []
        self.hidden_injections: List[str] = []
        self.dangerous_tags_removed: int = 0
        self.hidden_containers_removed: int = 0
        self._tag_stack: List[str] = []
        self._current_hidden_level: int = 0
        self._hidden_buffer: List[str] = []
        self._in_dangerous_tag: bool = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        tag_lower = tag.lower()
        self._tag_stack.append(tag_lower)

        if tag_lower in DANGEROUS_HTML_TAGS:
            self._in_dangerous_tag = True
            self.dangerous_tags_removed += 1
            return

        is_hidden = False
        for attr_name, attr_val in attrs:
            if not attr_val:
                continue
            name_lower = attr_name.lower()
            val_lower = attr_val.lower()

            if name_lower == "style":
                for pat in CSS_HIDDEN_PATTERNS:
                    if pat.search(val_lower):
                        is_hidden = True
                        break

            if name_lower == "hidden" or (name_lower == "aria-hidden" and val_lower == "true"):
                is_hidden = True

            if name_lower == "class":
                if any(cls_name in val_lower for cls_name in ["sr-only", "hidden", "visually-hidden", "invisible", "d-none"]):
                    is_hidden = True

            if is_hidden:
                break

        if is_hidden:
            self._current_hidden_level += 1
            self.hidden_containers_removed += 1
        elif self._current_hidden_level > 0:
            self._current_hidden_level += 1

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if self._tag_stack and self._tag_stack[-1] == tag_lower:
            self._tag_stack.pop()

        if tag_lower in DANGEROUS_HTML_TAGS:
            self._in_dangerous_tag = False
            return

        if self._current_hidden_level > 0:
            self._current_hidden_level -= 1
            if self._current_hidden_level == 0 and self._hidden_buffer:
                extracted = " ".join(self._hidden_buffer).strip()
                if extracted:
                    self.hidden_injections.append(extracted)
                self._hidden_buffer.clear()
        else:
            if tag_lower in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "br"):
                self.output_pieces.append("\n")

    def handle_data(self, data: str):
        if self._in_dangerous_tag:
            return

        clean_piece = data.strip()
        if not clean_piece:
            return

        if self._current_hidden_level > 0:
            self._hidden_buffer.append(clean_piece)
        else:
            self.output_pieces.append(clean_piece + " ")


class CleanwebResult:
    """Enterprise-grade sanitization report for web content."""

    def __init__(
        self,
        sanitized_content: str,
        risk_score: float,
        is_safe: bool,
        threats_detected: List[str],
        zero_width_chars_removed: int,
        hidden_css_blocks_removed: int,
        dangerous_tags_removed: int,
        exfiltration_links_neutralized: int,
        processing_time_ms: float,
        content_hash: str
    ):
        self.sanitized_content = sanitized_content
        self.risk_score = risk_score
        self.is_safe = is_safe
        self.threats_detected = threats_detected
        self.zero_width_chars_removed = zero_width_chars_removed
        self.hidden_css_blocks_removed = hidden_css_blocks_removed
        self.dangerous_tags_removed = dangerous_tags_removed
        self.exfiltration_links_neutralized = exfiltration_links_neutralized
        self.processing_time_ms = processing_time_ms
        self.content_hash = content_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "risk_score": round(self.risk_score, 1),
            "threats_detected": self.threats_detected,
            "metrics": {
                "zero_width_chars_removed": self.zero_width_chars_removed,
                "hidden_css_blocks_removed": self.hidden_css_blocks_removed,
                "dangerous_tags_removed": self.dangerous_tags_removed,
                "exfiltration_links_neutralized": self.exfiltration_links_neutralized,
                "processing_time_ms": round(self.processing_time_ms, 2)
            },
            "content_hash": self.content_hash,
            "sanitized_output": self.sanitized_content
        }


class CleanwebSanitizer:
    """Multi-vector content sanitizer preventing indirect prompt injection, hidden text, and data leakage."""

    @classmethod
    def strip_unicode_steganography(cls, text: str) -> Tuple[str, int]:
        """Strips zero-width spaces, joiners, and BiDi override characters."""
        stripped_count = 0
        cleaned_chars = []
        for ch in text:
            if ch in ZERO_WIDTH_CHARS or ch in BIDI_OVERRIDE_CHARS:
                stripped_count += 1
            else:
                cleaned_chars.append(ch)
        return "".join(cleaned_chars), stripped_count

    @classmethod
    def normalize_homoglyphs(cls, text: str) -> str:
        """Normalizes Cyrillic lookalike characters back to Latin characters."""
        normalized = []
        for ch in text:
            normalized.append(HOMOGLYPH_MAP.get(ch, ch))
        return "".join(normalized)

    @classmethod
    def sanitize_html_content(cls, raw_html: str) -> Tuple[str, int, int, List[str]]:
        """Parses HTML, removes hidden CSS containers, strips dangerous tags."""
        parser = CleanwebHTMLParser()
        try:
            parser.feed(raw_html)
            parser.close()
        except Exception:
            text_fallback = re.sub(r"<[^>]+>", " ", raw_html)
            return text_fallback, 0, 0, []

        sanitized_text = "".join(parser.output_pieces)
        sanitized_text = re.sub(r"[ \t]+", " ", sanitized_text)
        sanitized_text = re.sub(r"\n\s*\n", "\n\n", sanitized_text).strip()

        return (
            sanitized_text,
            parser.hidden_containers_removed,
            parser.dangerous_tags_removed,
            parser.hidden_injections
        )

    @classmethod
    def neutralize_covert_channels(cls, text: str) -> Tuple[str, int]:
        """Neutralizes exfiltration markdown images and tracking pixels with query leaks."""
        neutralized_count = 0

        def md_sub(m):
            nonlocal neutralized_count
            url = m.group(1)
            if EXFIL_PARAM_PATTERN.search(url):
                neutralized_count += 1
                return "[EXFILTRATION_IMAGE_BLOCKED]"
            return m.group(0)

        clean_text = re.sub(r"!\[.*?\]\((https?:\/\/[^\s\)]+)\)", md_sub, text)

        def html_sub(m):
            nonlocal neutralized_count
            src = m.group(1)
            if EXFIL_PARAM_PATTERN.search(src):
                neutralized_count += 1
                return "<!-- EXFILTRATION_IMAGE_BLOCKED -->"
            return m.group(0)

        clean_text = re.sub(r"<img[^>]+src=['\"](https?:\/\/[^'\"]+)['\"][^>]*>", html_sub, clean_text, flags=re.IGNORECASE)

        # Redact known credential/secret patterns
        for pattern in SECRET_PATTERNS:
            clean_text, n = re.subn(pattern, "[REDACTED_SECRET]", clean_text)
            if n > 0:
                neutralized_count += n

        return clean_text, neutralized_count

    @classmethod
    def purify(cls, raw_content: str, is_html: Optional[bool] = None) -> CleanwebResult:
        """Main purification pipeline."""
        start_time = time.perf_counter()

        if not raw_content or not raw_content.strip():
            return CleanwebResult(
                sanitized_content="",
                risk_score=0.0,
                is_safe=True,
                threats_detected=[],
                zero_width_chars_removed=0,
                hidden_css_blocks_removed=0,
                dangerous_tags_removed=0,
                exfiltration_links_neutralized=0,
                processing_time_ms=0.0,
                content_hash="0x" + ("00" * 32)
            )

        threats_found: List[str] = []

        # Step 1: Strip zero-width & invisible Unicode
        text_no_zw, zw_removed = cls.strip_unicode_steganography(raw_content)

        # Step 2: Neutralize covert channels & exfiltration links
        neutralized_text, exfil_count = cls.neutralize_covert_channels(text_no_zw)
        if exfil_count > 0:
            threats_found.append(f"COVERT_CHANNEL_EXFILTRATION_NEUTRALIZED ({exfil_count} links)")

        # Step 3: Auto-detect HTML if not specified
        if is_html is None:
            is_html = bool(re.search(r"<\/?(?:html|body|div|p|span|script|style|a|img|h[1-6]|ul|table)[>\s]", neutralized_text, re.IGNORECASE))

        hidden_blocks_removed = 0
        dangerous_tags_removed = 0
        extracted_hidden_texts: List[str] = []

        if is_html:
            cleaned_text, hidden_blocks_removed, dangerous_tags_removed, extracted_hidden_texts = cls.sanitize_html_content(neutralized_text)
            if hidden_blocks_removed > 0:
                threats_found.append(f"HIDDEN_CSS_CONTAINER_INJECTION ({hidden_blocks_removed} blocks stripped)")
            if dangerous_tags_removed > 0:
                threats_found.append(f"DANGEROUS_HTML_TAGS_STRIPPED ({dangerous_tags_removed} tags)")
        else:
            cleaned_text = neutralized_text

        # Check extracted hidden texts for injected instructions
        for hidden_item in extracted_hidden_texts:
            hidden_norm = cls.normalize_homoglyphs(hidden_item)
            for pat, label, severity, desc in INJECTION_PATTERN_SPECS:
                if re.search(pat, hidden_norm, re.IGNORECASE):
                    threats_found.append(f"INDIRECT_INJECTION_IN_HIDDEN_CSS: {label}")

        # Step 4: Audit for direct & indirect prompt injection in main content
        normalized_for_audit = cls.normalize_homoglyphs(cleaned_text)
        final_text = cleaned_text

        for pat, label, severity, desc in INJECTION_PATTERN_SPECS:
            matches = list(re.finditer(pat, normalized_for_audit, re.IGNORECASE))
            if matches:
                threats_found.append(f"PROMPT_INJECTION_{label}")
                for m in matches:
                    matched_str = m.group(0)
                    final_text = re.sub(re.escape(matched_str), "[REDACTED_BY_CLEANWEB]", final_text, flags=re.IGNORECASE)

        # Clean excessive blank lines
        final_text = re.sub(r"\n{3,}", "\n\n", final_text).strip()

        # Step 5: Risk Scoring
        base_risk = 0.0
        if threats_found:
            base_risk = max(base_risk, 70.0)
        if hidden_blocks_removed > 0:
            base_risk = max(base_risk, 65.0)
        if dangerous_tags_removed > 0:
            base_risk = max(base_risk, 75.0)
        if exfil_count > 0:
            base_risk = max(base_risk, 85.0)

        is_safe = (base_risk < 50.0) and (len(threats_found) == 0)
        content_hash = "0x" + hashlib.sha256(final_text.encode("utf-8")).hexdigest()
        latency_ms = (time.perf_counter() - start_time) * 1000

        return CleanwebResult(
            sanitized_content=final_text,
            risk_score=min(100.0, base_risk),
            is_safe=is_safe,
            threats_detected=sorted(list(set(threats_found))),
            zero_width_chars_removed=zw_removed,
            hidden_css_blocks_removed=hidden_blocks_removed,
            dangerous_tags_removed=dangerous_tags_removed,
            exfiltration_links_neutralized=exfil_count,
            processing_time_ms=latency_ms,
            content_hash=content_hash
        )


# Singleton instance
cleanweb_sanitizer = CleanwebSanitizer()
