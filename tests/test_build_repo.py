import json
from urllib.error import HTTPError

import pytest

from scripts import github
from scripts.build_repo import main, summarize


def plugin(name, version):
    return {
        "Name": name,
        "InternalName": name,
        "AssemblyVersion": version,
        "DalamudApiLevel": 15,
        "DownloadLinkInstall": f"https://example.com/{name}.zip",
    }


REPOS = [
    {"name": "beta-plugin", "topics": ["dalamud-plugin"]},
    {"name": "alpha-plugin", "topics": ["dalamud-plugin"]},
    {"name": "no-json-plugin", "topics": ["dalamud-plugin"]},
    {"name": "website", "topics": []},
]


@pytest.fixture
def files(monkeypatch):
    """Fake GitHub: REPOS for discovery, and repo.json files keyed by repo name."""
    files = {
        "alpha-plugin": [plugin("Alpha", "1.0.0.0")],
        "beta-plugin": [plugin("Beta", "2.0.0.0")],
    }

    def request(url, accept):
        repo = url.split("/repos/me/")[1].split("/")[0]
        if repo not in files:
            raise HTTPError(url, 404, "Not Found", {}, None)
        return json.dumps(files[repo]).encode(), ""

    monkeypatch.setattr(github, "get_all", lambda path: REPOS)
    monkeypatch.setattr(github, "request", request)
    return files


@pytest.fixture
def paths(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"owner": "me"}), encoding="utf-8")
    return ["--config", str(config), "--output", str(tmp_path / "out.json")]


def test_end_to_end(files, paths, tmp_path, capsys):
    output = tmp_path / "out.json"

    assert main(paths) == 0
    assert [e["InternalName"] for e in json.loads(output.read_bytes())] == ["Alpha", "Beta"]
    assert "+ Alpha 1.0.0.0" in capsys.readouterr().out

    assert main(paths) == 0
    assert "No changes." in capsys.readouterr().out

    files["beta-plugin"] = [plugin("Beta", "2.1.0.0")]
    assert main(paths) == 0
    assert "~ Beta 2.0.0.0 -> 2.1.0.0" in capsys.readouterr().out
    assert json.loads(output.read_bytes())[1]["AssemblyVersion"] == "2.1.0.0"


def test_dry_run_does_not_write(files, paths, tmp_path, capsys):
    assert main([*paths, "--dry-run"]) == 0
    assert not (tmp_path / "out.json").exists()
    assert "Dry run" in capsys.readouterr().out


def test_summarize():
    old = [plugin("Kept", "1"), plugin("Gone", "1"), plugin("Bumped", "1")]
    new = [plugin("Kept", "1"), plugin("Bumped", "2"), plugin("Added", "1")]
    assert summarize(old, new) == ["+ Added 1", "~ Bumped 1 -> 2", "- Gone 1"]
