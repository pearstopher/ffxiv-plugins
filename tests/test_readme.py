import json

import pytest

from scripts.config import load_config
from scripts.readme import END, README_PATH, START, cell, main, plugin_table, render

PLUGIN = {
    "Name": "Remove Duplicate PF",
    "AssemblyVersion": "1.1.2.0",
    "RepoUrl": "https://github.com/me/plugin",
    "Punchline": "Collapses duplicates.",
    "Description": "Long description.",
}
README = f"# Title\n\nIntro.\n\n{START}\nold table\n{END}\n\nFooter.\n"


def test_cell_escapes_pipes_and_newlines():
    assert cell("a | b\n\nc") == "a \\| b c"


def test_table_row_uses_link_punchline_and_version():
    assert plugin_table([PLUGIN]).splitlines()[2] == (
        "| [Remove Duplicate PF](https://github.com/me/plugin) | Collapses duplicates. | 1.1.2.0 |"
    )


def test_table_falls_back_without_repo_url_or_punchline():
    plugin = {"Name": "Plain", "AssemblyVersion": "1", "Description": "Desc."}
    assert plugin_table([plugin]).splitlines()[2] == "| Plain | Desc. | 1 |"


def test_empty_table():
    assert plugin_table([]) == "_No plugins yet._"


def test_render_only_changes_between_markers():
    result = render(README, [PLUGIN])
    assert result.startswith("# Title\n\nIntro.\n\n" + START + "\n| Plugin |")
    assert result.endswith(END + "\n\nFooter.\n")
    assert "old table" not in result


def test_render_is_deterministic():
    once = render(README, [PLUGIN])
    assert render(once, [PLUGIN]) == once


def test_render_requires_markers():
    with pytest.raises(ValueError, match="markers"):
        render("# No markers\n", [PLUGIN])


def test_repo_readme_has_markers_and_correct_link():
    readme = README_PATH.read_text(encoding="utf-8")
    owner = load_config().owner
    render(readme, [])  # raises if the markers are missing
    link = f"https://raw.githubusercontent.com/{owner}/ffxiv-plugins/main/pluginmaster.json"
    assert link in readme


def test_main_updates_then_reports_unchanged(tmp_path, capsys):
    readme, plugins = tmp_path / "README.md", tmp_path / "pluginmaster.json"
    readme.write_bytes(README.encode())
    plugins.write_text(json.dumps([PLUGIN]), encoding="utf-8")

    main(readme, plugins)
    assert "updated" in capsys.readouterr().out
    assert b"Remove Duplicate PF" in readme.read_bytes()
    assert b"\r" not in readme.read_bytes()

    main(readme, plugins)
    assert "unchanged" in capsys.readouterr().out
