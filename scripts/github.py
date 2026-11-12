"""Minimal GitHub REST API client using only the standard library."""

import json
import os
import re
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_URL = "https://api.github.com"
ATTEMPTS = 3  # retries cover network errors, 5xx and 429 (rate limited)
_NEXT_LINK = re.compile(r'<([^>]+)>;\s*rel="next"')


def request(url: str, accept: str = "application/vnd.github+json") -> tuple[bytes, str]:
    """GET a URL. Returns the body and the Link header. Uses GITHUB_TOKEN if set.

    Transient failures are retried with backoff; other HTTP errors (e.g. 404) raise at once.
    """
    headers = {
        "Accept": accept,
        "User-Agent": "ffxiv-plugins",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urlopen(Request(url, headers=headers), timeout=30) as response:
                return response.read(), response.headers.get("Link", "")
        except OSError as error:  # HTTPError, network errors and timeouts
            if attempt == ATTEMPTS or not is_transient(error):
                raise
            time.sleep(2**attempt)  # 2s, then 4s


def is_transient(error: OSError) -> bool:
    """Network errors, server errors and rate limits are worth retrying."""
    return not isinstance(error, HTTPError) or error.code == 429 or error.code >= 500


def get_all(path: str) -> list:
    """GET a list endpoint (e.g. "/users/x/repos") and follow pagination."""
    url, items = API_URL + path, []
    while url:
        body, link = request(url)
        items += json.loads(body)
        next_link = _NEXT_LINK.search(link)
        url = next_link.group(1) if next_link else None
    return items
