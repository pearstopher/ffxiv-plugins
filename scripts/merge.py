"""Combine plugin entries into one deterministic pluginmaster.json."""

import json
from pathlib import Path

OUTPUT_PATH = Path("pluginmaster.json")


def version_key(version: object) -> tuple[int, ...]:
    """"1.2.10.0" -> (1, 2, 10, 0). Non-numeric parts count as 0."""
    return tuple(int(part) if part.isdigit() else 0 for part in str(version).split("."))


def merge(entries: list[dict]) -> list[dict]:
    """One entry per InternalName (the highest AssemblyVersion wins), sorted by name."""
    best: dict[str, dict] = {}
    for entry in entries:
        name = entry["InternalName"]
        new_version = version_key(entry["AssemblyVersion"])
        if name not in best or new_version > version_key(best[name]["AssemblyVersion"]):
            best[name] = entry
    return [best[name] for name in sorted(best, key=lambda name: (name.lower(), name))]


def to_json(entries: list[dict]) -> bytes:
    """Stable bytes: 2-space indent, UTF-8, LF line endings, trailing newline."""
    return (json.dumps(entries, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def read_json(path: Path = OUTPUT_PATH) -> list[dict]:
    """Entries from an existing output file, or [] if there is none yet."""
    return json.loads(path.read_bytes()) if path.exists() else []


def needs_write(entries: list[dict], path: Path = OUTPUT_PATH) -> bool:
    """True if path is missing or its bytes differ from to_json(entries)."""
    return not path.exists() or path.read_bytes() != to_json(entries)


def write_json(entries: list[dict], path: Path = OUTPUT_PATH) -> None:
    path.write_bytes(to_json(entries))
