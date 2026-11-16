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


def releases(*counts):
    """One release per count, each with a latest.zip downloaded that many times."""
    return [{"assets": [{"name": "latest.zip", "download_count": n}]} for n in counts]


@pytest.fixture
def github_api(monkeypatch):
    """Fake GitHub. Tests change api["repos"] (discovery), api["files"] (repo.json per repo) and
    api["releases"] (per repo). An exception value makes that fetch fail."""
    api = {
        "repos": REPOS,
        "files": {
            "alpha-plugin": [plugin("Alpha", "1.0.0.0", "alpha-plugin")],
            "beta-plugin": [plugin("Beta", "2.0.0.0", "beta-plugin")],
        },
        "releases": {"alpha-plugin": releases(10, 5), "beta-plugin": releases(1)},
    }

    def respond(response):
        if isinstance(response, Exception):
            raise response
        return response

    def get_all(path):
        if "/releases" not in path:
            return api["repos"]
        return respond(api["releases"].get(path.split("/")[3], []))

    def request(url, accept):
        repo = url.split("/repos/me/")[1].split("/")[0]
        response = api["files"].get(repo, HTTPError(url, 404, "Not Found", {}, None))
        return json.dumps(respond(response)).encode(), ""

    monkeypatch.setattr(github, "get_all", get_all)
    monkeypatch.setattr(github, "request", request)
    return api


@pytest.fixture
def output(tmp_path):
    return tmp_path / "out.json"


@pytest.fixture
def run(tmp_path, output, capsys):
    """Run the CLI against a temp config/output. Returns (printed output, written entry names)."""
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"owner": "me"}), encoding="utf-8")

    def run(*extra):
        assert main(["--config", str(config), "--output", str(output), *extra]) == 0
        if not output.exists():
            return capsys.readouterr().out, None
        return capsys.readouterr().out, [e["InternalName"] for e in json.loads(output.read_bytes())]

    return run


def counts(output):
    return {e["InternalName"]: e.get("DownloadCount") for e in json.loads(output.read_bytes())}


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


def test_download_counts_are_added(github_api, run, output):
    run()
    assert counts(output) == {"Alpha": 15, "Beta": 1}


def test_failed_releases_fetch_keeps_previous_count(github_api, run, output, caplog):
    run()
    github_api["releases"]["alpha-plugin"] = HTTPError("u", 500, "Server Error", {}, None)

    assert run()[0] == "No changes.\n"
    assert counts(output) == {"Alpha": 15, "Beta": 1}
    assert "me/alpha-plugin: could not fetch releases" in caplog.text


def test_small_count_changes_are_skipped_with_threshold(github_api, run, output):
    run()
    github_api["releases"]["alpha-plugin"] = releases(10, 5, 99)

    out, _ = run("--min-download-change", "100")
    assert "not written" in out
    assert counts(output) == {"Alpha": 15, "Beta": 1}


def test_crossing_threshold_writes_every_exact_count(github_api, run, output):
    run()
    github_api["releases"]["alpha-plugin"] = releases(10, 5, 100)
    github_api["releases"]["beta-plugin"] = releases(1, 2)

    run("--min-download-change", "100")
    assert counts(output) == {"Alpha": 115, "Beta": 3}


def test_other_changes_write_despite_threshold(github_api, run, output):
    run()
    github_api["files"]["beta-plugin"] = [plugin("Beta", "2.1.0.0", "beta-plugin")]
    github_api["releases"]["alpha-plugin"] = releases(10, 5, 1)

    assert "~ Beta 2.0.0.0 -> 2.1.0.0" in run("--min-download-change", "100")[0]
    assert counts(output) == {"Alpha": 16, "Beta": 1}


def test_summarize():
    old = [plugin("Kept", "1"), plugin("Gone", "1"), plugin("Bumped", "1")]
    new = [plugin("Kept", "1"), plugin("Bumped", "2"), plugin("Added", "1")]
    assert summarize(old, new) == ["+ Added 1", "~ Bumped 1 -> 2", "- Gone 1"]
