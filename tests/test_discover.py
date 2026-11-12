from scripts import discover as discover_module
from scripts.config import Config
from scripts.discover import discover, select_repos

REPOS = [
    {"name": "plugin-b", "topics": ["dalamud-plugin"]},
    {"name": "plugin-a", "topics": ["dalamud-plugin", "ffxiv"]},
    {"name": "website", "topics": []},
    {"name": "old-plugin", "topics": ["dalamud-plugin"], "archived": True},
    {"name": "untagged-plugin"},
]


def test_selects_topic_repos_sorted():
    assert select_repos(REPOS, Config(owner="me")) == ["plugin-a", "plugin-b"]


def test_include_adds_repo_without_topic():
    config = Config(owner="me", include=("untagged-plugin",))
    assert select_repos(REPOS, config) == ["plugin-a", "plugin-b", "untagged-plugin"]


def test_exclude_wins_over_topic_and_include():
    config = Config(owner="me", include=("plugin-a",), exclude=("plugin-a",))
    assert select_repos(REPOS, config) == ["plugin-b"]


def test_archived_repos_are_skipped_even_if_included():
    config = Config(owner="me", include=("old-plugin",))
    assert "old-plugin" not in select_repos(REPOS, config)


def test_discover_lists_owner_repos(monkeypatch):
    calls = []

    def fake_get_all(path):
        calls.append(path)
        return REPOS

    monkeypatch.setattr(discover_module.github, "get_all", fake_get_all)
    assert discover(Config(owner="me")) == ["plugin-a", "plugin-b"]
    assert calls == ["/users/me/repos?type=owner&per_page=100"]
