"""Rewrite the plugin table in README.md from pluginmaster.json.

Usage: python -m scripts.readme
"""

import sys
from pathlib import Path

from scripts.merge import OUTPUT_PATH, read_json

README_PATH = Path("README.md")
START, END = "<!-- plugins:start -->", "<!-- plugins:end -->"


def cell(text: object) -> str:
    """Make text safe for one Markdown table cell."""
    return " ".join(str(text).split()).replace("|", "\\|")


def plugin_table(entries: list[dict]) -> str:
    if not entries:
        return "_No plugins yet._"
    rows = ["| Plugin | Description | Version |", "| --- | --- | --- |"]
    for entry in entries:
        name = cell(entry["Name"])
        if url := entry.get("RepoUrl"):
            name = f"[{name}]({url})"
        description = cell(entry.get("Punchline") or entry.get("Description", ""))
        rows.append(f"| {name} | {description} | {cell(entry['AssemblyVersion'])} |")
    return "\n".join(rows)


def render(readme: str, entries: list[dict]) -> str:
    """Replace everything between the START and END markers with the plugin table."""
    head, found_start, rest = readme.partition(START)
    _, found_end, tail = rest.partition(END)
    if not (found_start and found_end):
        raise ValueError(f"README is missing the {START} / {END} markers")
    return f"{head}{START}\n{plugin_table(entries)}\n{END}{tail}"


def main(readme_path: Path = README_PATH, plugins_path: Path = OUTPUT_PATH) -> int:
    old = readme_path.read_bytes().decode("utf-8")
    new = render(old, read_json(plugins_path))
    if new == old:
        print("README unchanged.")
    else:
        readme_path.write_bytes(new.encode("utf-8"))
        print("README plugin list updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
