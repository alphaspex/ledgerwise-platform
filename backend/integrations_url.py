# Inputs: provider configuration and operation payloads for Meta Muse, Resend, Apollo, Cal.com, and URL checks.
# Outputs: normalized provider responses, model usage, delivery identifiers, contact matches, bookings, and URL results.
# Explanation: Exposes provider integrations through focused I/O-bound modules.
from __future__ import annotations

import asyncio
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


def check_url(url: str, timeout: int = 5, max_redirects: int = 5) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return {"result": "unverified", "status": None, "error": "invalid_url"}
    try:
        socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        session = requests.Session()
        session.max_redirects = max_redirects
        response = session.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; LedgerwiseBot/1.0)"},
            timeout=timeout,
            stream=True,
            allow_redirects=True,
        )
        status = int(response.status_code)
        response_url = response.url
        response.close()
        session.close()
        if status == 200:
            return {"result": "live", "status": status, "final_url": response_url}
        if status in {404, 410}:
            return {"result": "dead", "status": status, "final_url": response_url}
        return {"result": "unverified", "status": status, "final_url": response_url}
    except requests.exceptions.HTTPError as exc:
        return {"result": "unverified", "status": getattr(exc.response, "status_code", None), "error": "http_error"}
    except requests.exceptions.TooManyRedirects:
        return {"result": "unverified", "status": None, "error": "too_many_redirects"}
    except requests.exceptions.RequestException as exc:
        return {"result": "unverified", "status": None, "error": type(exc).__name__}
    except socket.gaierror as exc:
        if getattr(exc, "errno", None) == socket.EAI_NONAME:
            return {"result": "dead", "status": None, "error": "nxdomain"}
        return {"result": "unverified", "status": None, "error": "dns_error"}
