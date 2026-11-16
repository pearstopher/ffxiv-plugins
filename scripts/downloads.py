"""Count plugin downloads from GitHub releases, for the DownloadCount field."""

import logging

from scripts import github

log = logging.getLogger(__name__)


def fetch_releases(owner: str, repo: str) -> list[dict] | None:
    """All releases of a repo, or None if they couldn't be fetched."""
    try:
        return github.get_all(f"/repos/{owner}/{repo}/releases?per_page=100")
    except (OSError, ValueError) as error:  # HTTP/network error or invalid JSON
        log.warning("%s/%s: could not fetch releases: %s", owner, repo, error)
        return None


def count_downloads(releases: list[dict], entry: dict) -> int:
    """Downloads of the entry's download file (e.g. latest.zip), summed across all releases."""
    filename = str(entry["DownloadLinkInstall"]).rsplit("/", 1)[-1]
    return sum(
        asset["download_count"]
        for release in releases
        for asset in release.get("assets", [])
        if asset["name"] == filename
    )
