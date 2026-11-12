"""Find the owner's plugin repos."""

from scripts import github
from scripts.config import Config


def select_repos(repos: list[dict], config: Config) -> list[str]:
    """Names of non-archived repos that have the topic or are included, minus excluded ones."""
    return sorted(
        repo["name"]
        for repo in repos
        if not repo.get("archived")
        and repo["name"] not in config.exclude
        and (config.topic in repo.get("topics", []) or repo["name"] in config.include)
    )


def discover(config: Config) -> list[str]:
    repos = github.get_all(f"/users/{config.owner}/repos?type=owner&per_page=100")
    return select_repos(repos, config)
