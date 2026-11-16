# Inputs: provider configuration plus raw webhook bodies, signature headers, URLs, and provider request data.
# Outputs: normalized provider helpers and verified webhook authenticity results.
# Explanation: Provides shared parsing, domain, signature, and I/O-bound integration helpers.
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import re
import socket
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
from typing import Any
from urllib.parse import urlparse

import httpx
import requests
import tldextract


from .config import Settings


GENERIC_INBOX_PREFIXES = {
    "info", "hello", "support", "orders", "service", "customercare", "team", "contact"
}

ROLE_TITLES = {
    "founder": ["Founder", "Co-Founder", "CEO", "Chief Executive Officer"],
    "coo": ["COO", "Chief Operating Officer"],
    "finance": ["CFO", "Chief Financial Officer", "Finance Director", "Controller"],
}


def normalize_domain(value: str) -> str:
    raw = value.strip().lower()
    if not raw:
        raise ValueError("domain is required")
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = (parsed.hostname or "").strip(".").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host or any(ch.isspace() for ch in host):
        raise ValueError("invalid domain")
    return host


def registrable_domain(value: str) -> str:
    extracted = tldextract.TLDExtract(suffix_list_urls=())(normalize_domain(value))
    return extracted.top_domain_under_public_suffix or normalize_domain(value)


def is_generic_email(email: str) -> bool:
    normalized = parseaddr(email)[1].strip().lower()
    if "@" not in normalized:
        return True
    return normalized.split("@", 1)[0].split("+", 1)[0] in GENERIC_INBOX_PREFIXES


def verify_hmac_signature(raw_body: bytes, signature: str, secret: str, prefix: str = "") -> bool:
    if not signature or not secret:
        return False
    supplied = signature.removeprefix(prefix).strip()
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(supplied, expected)


def verify_svix_signature(raw_body: bytes, webhook_id: str | None, webhook_timestamp: str | None, webhook_signature: str | None, secret: str, tolerance_seconds: int = 300) -> bool:
    if not raw_body or not webhook_id or not webhook_timestamp or not webhook_signature or not secret:
        return False
    try:
        timestamp_value = int(webhook_timestamp)
        if abs(time.time() - timestamp_value) > tolerance_seconds or not secret.startswith("whsec_"):
            return False
        encoded_secret = secret.removeprefix("whsec_")
        key = base64.b64decode(encoded_secret + "=" * (-len(encoded_secret) % 4), validate=True)
    except (ValueError, TypeError):
        return False
    signed_content = webhook_id.encode("utf-8") + b"." + webhook_timestamp.encode("utf-8") + b"." + raw_body
    expected = base64.b64encode(hmac.new(key, signed_content, hashlib.sha256).digest()).decode("ascii")
    for item in webhook_signature.split():
        version, separator, supplied = item.partition(",")
        if separator and version == "v1" and hmac.compare_digest(supplied, expected):
            return True
    return False
