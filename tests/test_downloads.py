from urllib.error import URLError

from scripts import downloads, github

ENTRY = {"DownloadLinkInstall": "https://github.com/me/p/releases/download/v2/latest.zip"}


def test_count_sums_matching_file_across_releases():
    releases = [
        {"assets": [{"name": "latest.zip", "download_count": 7},
                    {"name": "other.zip", "download_count": 100}]},
        {"assets": [{"name": "latest.zip", "download_count": 3}]},
        {"assets": []},
    ]
    assert downloads.count_downloads(releases, ENTRY) == 10


def test_count_is_zero_without_releases():
    assert downloads.count_downloads([], ENTRY) == 0


def test_fetch_releases_uses_paginated_endpoint(monkeypatch):
    paths = []
    monkeypatch.setattr(github, "get_all", lambda path: paths.append(path) or ["r"])

    assert downloads.fetch_releases("me", "p") == ["r"]
    assert paths == ["/repos/me/p/releases?per_page=100"]


def test_fetch_releases_returns_none_on_error(monkeypatch):
    def fail(path):
        raise URLError("down")

    monkeypatch.setattr(github, "get_all", fail)
    assert downloads.fetch_releases("me", "p") is None
