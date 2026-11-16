"""Build pluginmaster.json from all plugin repos.

Usage: python -m scripts.build_repo [--config config.json] [--output pluginmaster.json] [--dry-run]
"""

import argparse
import logging
import sys
from pathlib import Path

from scripts.config import CONFIG_PATH, load_config
from scripts.discover import discover
from scripts.downloads import count_downloads, fetch_releases
from scripts.fetch import fetch_plugins
from scripts.merge import OUTPUT_PATH, merge, needs_write, read_json, write_json

log = logging.getLogger(__name__)


def from_repo(entries: list[dict], owner: str, repo: str) -> list[dict]:
    """Entries whose RepoUrl or DownloadLinkInstall points into github.com/<owner>/<repo>."""
    prefix = f"https://github.com/{owner}/{repo}/".lower()

    def matches(entry: dict) -> bool:
        links = (entry.get("RepoUrl", ""), entry.get("DownloadLinkInstall", ""))
        return any((str(link).rstrip("/") + "/").lower().startswith(prefix) for link in links)

    return [entry for entry in entries if matches(entry)]


def add_download_counts(plugins: list[dict], releases: list[dict] | None, previous: list[dict]):
    """Set each plugin's DownloadCount from releases, or keep its previous count if releases
    is None."""
    old_counts = {e["InternalName"]: e["DownloadCount"] for e in previous if "DownloadCount" in e}
    for plugin in plugins:
        if releases is not None:
            plugin["DownloadCount"] = count_downloads(releases, plugin)
        elif plugin["InternalName"] in old_counts:
            plugin["DownloadCount"] = old_counts[plugin["InternalName"]]


def build(config_path: Path, previous: list[dict]) -> list[dict]:
    """Discover, fetch and merge all plugin entries, with download counts.

    If a repo's fetch fails, its entries from `previous` are kept. Repos that are no longer
    discovered are dropped.
    """
    config = load_config(config_path)
    entries = []
    for repo in discover(config):
        plugins = fetch_plugins(repo, config)
        if plugins is None:
            plugins = from_repo(previous, config.owner, repo)
            log.warning("%s: fetch failed, keeping %d previous entries", repo, len(plugins))
        else:
            add_download_counts(plugins, fetch_releases(config.owner, repo), previous)
        entries += plugins
    return merge(entries)


def only_small_count_changes(old: list[dict], new: list[dict], threshold: int) -> bool:
    """True if old and new differ only in DownloadCounts that each moved by less than threshold."""

    def without_counts(entries: list[dict]) -> list[dict]:
        return [{k: v for k, v in e.items() if k != "DownloadCount"} for e in entries]

    if without_counts(old) != without_counts(new):
        return False
    return all(
        abs(n.get("DownloadCount", 0) - o.get("DownloadCount", 0)) < threshold
        for o, n in zip(old, new, strict=True)
    )


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
    parser.add_argument(
        "--min-download-change", type=int, default=0, metavar="N",
        help="skip writing if the only changes are download counts that each moved by less than N",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    old = read_json(args.output)
    new = build(args.config, old)
    if not needs_write(new, args.output):
        print("No changes.")
        return 0
    if only_small_count_changes(old, new, args.min_download_change):
        print(f"Only download count changes under {args.min_download_change}; not written.")
        return 0

    print("\n".join(summarize(old, new)) or "Plugin details changed.")
    if args.dry_run:
        print(f"Dry run: {args.output} not written.")
    else:
        write_json(new, args.output)
        print(f"Wrote {len(new)} plugin(s) to {args.output}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
