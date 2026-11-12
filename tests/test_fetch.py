import json
from urllib.error import HTTPError, URLError

import pytest

from scripts import fetch
from scripts.config import Config
from scripts.fetch import fetch_plugins, validate

CONFIG = Config(owner="me", filenames=("repo.json", "pluginmaster.json"))
ENTRY = {
    "Name": "Plugin",
    "InternalName": "Plugin",
    "AssemblyVersion": "1.0.0.0",
    "DalamudApiLevel": 15,
    "DownloadLinkInstall": "https://example.com/latest.zip",
    "Punchline": "Extra fields are kept",
}


def serve(monkeypatch, responses):
    """Patch github.request to answer by filename: bytes are returned, exceptions raised."""
    requested = []

    def request(url, accept):
        filename = url.rsplit("/", 1)[1]
        requested.append(filename)
        response = responses.get(filename, HTTPError(url, 404, "Not Found", {}, None))
        if isinstance(response, Exception):
            raise response
        return response, ""

    monkeypatch.setattr(fetch.github, "request", request)
    return requested


def test_validate_accepts_list_and_single_object():
    assert validate([ENTRY], "src") == [ENTRY]
    assert validate(ENTRY, "src") == [ENTRY]


def test_validate_skips_entries_missing_required_fields(caplog):
    broken = {k: v for k, v in ENTRY.items() if k != "DownloadLinkInstall"}
    assert validate([broken, ENTRY], "src") == [ENTRY]
    assert "missing DownloadLinkInstall" in caplog.text


def test_validate_skips_non_objects(caplog):
    assert validate([42, ENTRY], "src") == [ENTRY]
    assert "not an object" in caplog.text


def test_fetches_first_candidate_file(monkeypatch):
    requested = serve(monkeypatch, {"repo.json": json.dumps([ENTRY]).encode()})
    assert fetch_plugins("plugin", CONFIG) == [ENTRY]
    assert requested == ["repo.json"]


def test_falls_back_to_next_candidate_on_404(monkeypatch):
    requested = serve(monkeypatch, {"pluginmaster.json": json.dumps(ENTRY).encode()})
    assert fetch_plugins("plugin", CONFIG) == [ENTRY]
    assert requested == ["repo.json", "pluginmaster.json"]


def test_utf8_bom_is_accepted(monkeypatch):
    serve(monkeypatch, {"repo.json": b"\xef\xbb\xbf" + json.dumps([ENTRY]).encode()})
    assert fetch_plugins("plugin", CONFIG) == [ENTRY]


def test_missing_file_returns_empty_list(monkeypatch, caplog):
    serve(monkeypatch, {})
    assert fetch_plugins("plugin", CONFIG) == []
    assert "no plugin JSON found" in caplog.text


@pytest.mark.parametrize(
    "response",
    [
        b"{not json",
        HTTPError("url", 500, "Server Error", {}, None),
        URLError("connection refused"),
        TimeoutError("timed out"),
    ],
)
def test_failed_fetch_returns_none(monkeypatch, caplog, response):
    serve(monkeypatch, {"repo.json": response})
    assert fetch_plugins("plugin", CONFIG) is None
    assert "me/plugin/repo.json" in caplog.text
