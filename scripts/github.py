"""Minimal GitHub REST API client using only the standard library."""

import json
import os
import re
from urllib.request import Request, urlopen

API_URL = "https://api.github.com"
_NEXT_LINK = re.compile(r'<([^>]+)>;\s*rel="next"')


def request(url: str, accept: str = "application/vnd.github+json") -> tuple[bytes, str]:
    """GET a URL. Returns the body and the Link header. Uses GITHUB_TOKEN if set."""
    headers = {
        "Accept": accept,
        "User-Agent": "ffxiv-plugins",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return response.read(), response.headers.get("Link", "")


def get_all(path: str) -> list:
    """GET a list endpoint (e.g. "/users/x/repos") and follow pagination."""
    url, items = API_URL + path, []
    while url:
        body, link = request(url)
        items += json.loads(body)
        next_link = _NEXT_LINK.search(link)
        url = next_link.group(1) if next_link else None
    return items
