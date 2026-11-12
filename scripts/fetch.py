"""Fetch and validate a plugin repo's plugin JSON."""

import json
import logging
from urllib.error import HTTPError

from scripts import github
from scripts.config import Config

log = logging.getLogger(__name__)

RAW = "application/vnd.github.raw+json"
REQUIRED_FIELDS = (
    "Name",
    "InternalName",
    "AssemblyVersion",
    "DalamudApiLevel",
    "DownloadLinkInstall",
)


def validate(data: object, source: str) -> list[dict]:
    """Return the valid manifest entries in data (a list of entries or a single entry)."""
    valid = []
    for entry in data if isinstance(data, list) else [data]:
        if not isinstance(entry, dict):
            log.warning("%s: skipping an entry that is not an object", source)
        elif missing := [field for field in REQUIRED_FIELDS if field not in entry]:
            name = entry.get("InternalName", "an entry")
            log.warning("%s: skipping %s, missing %s", source, name, ", ".join(missing))
        else:
            valid.append(entry)
    return valid


def fetch_plugins(repo: str, config: Config) -> list[dict] | None:
    """Valid entries from the repo's first plugin JSON file found on its default branch.

    Returns [] if the repo has none of the candidate files, or None if the fetch failed
    (network or server error, invalid JSON), so the caller can keep the previous entries.
    """
    for filename in config.filenames:
        source = f"{config.owner}/{repo}/{filename}"
        try:
            body, _ = github.request(
                f"{github.API_URL}/repos/{config.owner}/{repo}/contents/{filename}", accept=RAW
            )
            return validate(json.loads(body), source)
        except HTTPError as error:
            if error.code != 404:
                log.warning("%s: HTTP %s", source, error.code)
                return None
        except (OSError, ValueError) as error:  # network error or invalid JSON
            log.warning("%s: %s", source, error)
            return None
    log.warning("%s/%s: no plugin JSON found", config.owner, repo)
    return []
