"""Build pluginmaster.json from all plugin repos.

Usage: python -m scripts.build_repo [--config config.json] [--output pluginmaster.json] [--dry-run]
"""

import argparse
import logging
import sys
from pathlib import Path

from scripts.config import CONFIG_PATH, load_config
from scripts.discover import discover
from scripts.fetch import fetch_plugins
from scripts.merge import OUTPUT_PATH, merge, needs_write, read_json, write_json


def build(config_path: Path) -> list[dict]:
    """Discover, fetch and merge all plugin entries."""
    config = load_config(config_path)
    entries = []
    for repo in discover(config):
        entries += fetch_plugins(repo, config) or []
    return merge(entries)


def summarize(old: list[dict], new: list[dict]) -> list[str]:
    """One line per plugin that was added (+), removed (-) or changed version (~)."""
    before = {e["InternalName"]: e["AssemblyVersion"] for e in old}
    after = {e["InternalName"]: e["AssemblyVersion"] for e in new}
    lines = []
    for name in sorted(before | after, key=str.lower):
        if name not in before:
            lines.append(f"+ {name} {after[name]}")
        elif name not in after:
            lines.append(f"- {name} {before[name]}")
        elif before[name] != after[name]:
            lines.append(f"~ {name} {before[name]} -> {after[name]}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the combined Dalamud plugin repo.")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true", help="show changes without writing")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    new = build(args.config)
    if not needs_write(new, args.output):
        print("No changes.")
        return 0

    print("\n".join(summarize(read_json(args.output), new)) or "Plugin details changed.")
    if args.dry_run:
        print(f"Dry run: {args.output} not written.")
    else:
        write_json(new, args.output)
        print(f"Wrote {len(new)} plugin(s) to {args.output}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
