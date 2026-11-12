import json

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


def test_no_auth_header_without_token(monkeypatch):
    requests = []
    pages = {"https://api.github.com/x": FakeResponse([])}
    monkeypatch.setattr(github, "urlopen", fake_urlopen(pages, requests))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    github.get_all("/x")
    assert requests[0].get_header("Authorization") is None
