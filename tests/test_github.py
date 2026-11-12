import json
from urllib.error import HTTPError, URLError

import pytest

from scripts import github


class FakeResponse:
    def __init__(self, body, link=""):
        self.body = json.dumps(body).encode()
        self.headers = {"Link": link} if link else {}

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_urlopen(pages, requests):
    def urlopen(request, timeout):
        requests.append(request)
        return pages[request.full_url]

    return urlopen


def test_get_all_follows_pagination(monkeypatch):
    page2 = "https://api.github.com/x?page=2"
    link = f'<{page2}>; rel="next", <{page2}>; rel="last"'
    pages = {
        "https://api.github.com/x": FakeResponse([1, 2], link),
        page2: FakeResponse([3]),
    }
    requests = []
    monkeypatch.setattr(github, "urlopen", fake_urlopen(pages, requests))

    assert github.get_all("/x") == [1, 2, 3]
    assert [r.full_url for r in requests] == ["https://api.github.com/x", page2]


def test_token_is_sent_when_set(monkeypatch):
    requests = []
    pages = {"https://api.github.com/x": FakeResponse([])}
    monkeypatch.setattr(github, "urlopen", fake_urlopen(pages, requests))
    monkeypatch.setenv("GITHUB_TOKEN", "secret")

    github.get_all("/x")
    assert requests[0].get_header("Authorization") == "Bearer secret"


def flaky_urlopen(outcomes, calls):
    """Each call pops the next outcome: raise it if it's an exception, else return it."""

    def urlopen(request, timeout):
        calls.append(request.full_url)
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return urlopen


@pytest.mark.parametrize(
    "error",
    [HTTPError("u", 502, "Bad Gateway", {}, None), HTTPError("u", 429, "Too Many", {}, None),
     URLError("reset"), TimeoutError("slow")],
)
def test_transient_errors_are_retried(monkeypatch, error):
    calls, sleeps = [], []
    monkeypatch.setattr(github, "urlopen", flaky_urlopen([error, FakeResponse([1])], calls))
    monkeypatch.setattr(github.time, "sleep", sleeps.append)

    assert github.request("https://x")[0] == b"[1]"
    assert len(calls) == 2
    assert sleeps == [2]


def test_gives_up_after_all_attempts(monkeypatch):
    calls = []
    outcomes = [URLError("down")] * github.ATTEMPTS
    monkeypatch.setattr(github, "urlopen", flaky_urlopen(outcomes, calls))
    monkeypatch.setattr(github.time, "sleep", lambda seconds: None)

    with pytest.raises(URLError):
        github.request("https://x")
    assert len(calls) == github.ATTEMPTS


def test_404_is_not_retried(monkeypatch):
    calls = []
    not_found = HTTPError("u", 404, "Not Found", {}, None)
    monkeypatch.setattr(github, "urlopen", flaky_urlopen([not_found], calls))

    with pytest.raises(HTTPError):
        github.request("https://x")
    assert len(calls) == 1


def test_no_auth_header_without_token(monkeypatch):
    requests = []
    pages = {"https://api.github.com/x": FakeResponse([])}
    monkeypatch.setattr(github, "urlopen", fake_urlopen(pages, requests))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    github.get_all("/x")
    assert requests[0].get_header("Authorization") is None
