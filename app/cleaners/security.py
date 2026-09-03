"""
Security validation utilities for Web & Document Scrapers.
Protects against SSRF (Server-Side Request Forgery) targeting GCP metadata and private networks.
"""

import socket
import ipaddress
from urllib.parse import urlparse


FORBIDDEN_HOSTS = {
    "localhost",
    "metadata.google.internal",
    "metadata",
    "169.254.169.254",
    "instance-data",
}


def is_safe_url(url: str) -> bool:
    """
    Validates whether a URL is safe to fetch from server-side.
    Rejects non-HTTP(S) schemes, localhost, private IP ranges, and cloud metadata services.
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        hostname = hostname.lower()

        # Check explicit forbidden hosts
        if hostname in FORBIDDEN_HOSTS or hostname.endswith(".internal"):
            return False

        # Attempt to parse hostname directly as IP
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        except ValueError:
            # Hostname is a domain name, resolve DNS
            try:
                addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
                for family, _, _, _, sockaddr in addr_info:
                    ip_str = sockaddr[0]
                    resolved_ip = ipaddress.ip_address(ip_str)
                    if (
                        resolved_ip.is_private
                        or resolved_ip.is_loopback
                        or resolved_ip.is_link_local
                        or resolved_ip.is_reserved
                        or resolved_ip.is_multicast
                    ):
                        return False
            except Exception:
                # If DNS resolution fails, reject to be safe
                return False

        return True
    except Exception:
        return False
