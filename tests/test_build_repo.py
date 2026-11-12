import json
from urllib.error import HTTPError

import pytest

from scripts import github
from scripts.build_repo import from_repo, main, summarize


def plugin(name, version, repo="repo"):
    return {
        "Name": name,
        "InternalName": name,
        "AssemblyVersion": version,
        "DalamudApiLevel": 15,
        "DownloadLinkInstall": f"https://github.com/me/{repo}/releases/download/v{version}/latest.zip",
    }


REPOS = [
    {"name": "beta-plugin", "topics": ["dalamud-plugin"]},
    {"name": "alpha-plugin", "topics": ["dalamud-plugin"]},
    {"name": "no-json-plugin", "topics": ["dalamud-plugin"]},
    {"name": "website", "topics": []},
]


@pytest.fixture
def github_api(monkeypatch):
    """Fake GitHub. Tests change api["repos"] (discovery) and api["files"] (repo.json per repo;
    an exception value makes that fetch fail)."""
    api = {
        "repos": REPOS,
        "files": {
            "alpha-plugin": [plugin("Alpha", "1.0.0.0", "alpha-plugin")],
            "beta-plugin": [plugin("Beta", "2.0.0.0", "beta-plugin")],
        },
    }

    def request(url, accept):
        repo = url.split("/repos/me/")[1].split("/")[0]
        response = api["files"].get(repo, HTTPError(url, 404, "Not Found", {}, None))
        if isinstance(response, Exception):
            raise response
        return json.dumps(response).encode(), ""

    monkeypatch.setattr(github, "get_all", lambda path: api["repos"])
    monkeypatch.setattr(github, "request", request)
    return api


@pytest.fixture
def run(tmp_path, capsys):
    """Run the CLI against a temp config/output. Returns (printed output, written entry names)."""
    config, output = tmp_path / "config.json", tmp_path / "out.json"
    config.write_text(json.dumps({"owner": "me"}), encoding="utf-8")

    def run(*extra):
        assert main(["--config", str(config), "--output", str(output), *extra]) == 0
        if not output.exists():
            return capsys.readouterr().out, None
        return capsys.readouterr().out, [e["InternalName"] for e in json.loads(output.read_bytes())]

    return run


def test_end_to_end(github_api, run):
    out, names = run()
    assert names == ["Alpha", "Beta"]
    assert "+ Alpha 1.0.0.0" in out

    assert run()[0] == "No changes.\n"

    github_api["files"]["beta-plugin"] = [plugin("Beta", "2.1.0.0", "beta-plugin")]
    assert "~ Beta 2.0.0.0 -> 2.1.0.0" in run()[0]


def test_dry_run_does_not_write(github_api, run):
    out, names = run("--dry-run")
    assert names is None
    assert "Dry run" in out


def test_failed_fetch_keeps_previous_entry(github_api, run, caplog):
    run()
    github_api["files"]["beta-plugin"] = HTTPError("u", 500, "Server Error", {}, None)

    out, names = run()
    assert names == ["Alpha", "Beta"]
    assert out == "No changes.\n"
    assert "beta-plugin: fetch failed, keeping 1 previous entries" in caplog.text


def test_repo_no_longer_discovered_is_removed(github_api, run):
    run()
    github_api["repos"] = [r for r in REPOS if r["name"] != "beta-plugin"]

    out, names = run()
    assert names == ["Alpha"]
    assert "- Beta 2.0.0.0" in out


def test_from_repo_matches_repo_url_or_download_link():
    by_link = plugin("A", "1", "My-Plugin")
    by_repo_url = {**plugin("B", "1", "elsewhere"), "RepoUrl": "https://github.com/ME/my-plugin"}
    similar_name = plugin("C", "1", "my-plugin-two")
    entries = [by_link, by_repo_url, similar_name]

    assert from_repo(entries, "me", "my-plugin") == [by_link, by_repo_url]


def test_summarize():
    old = [plugin("Kept", "1"), plugin("Gone", "1"), plugin("Bumped", "1")]
    new = [plugin("Kept", "1"), plugin("Bumped", "2"), plugin("Added", "1")]
    assert summarize(old, new) == ["+ Added 1", "~ Bumped 1 -> 2", "- Gone 1"]
