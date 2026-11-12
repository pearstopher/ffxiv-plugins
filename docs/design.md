# Design

This repo publishes one `pluginmaster.json` that combines the `repo.json` files of all of
pearstopher's Dalamud plugins, so players add a single custom repo URL in game.

## Survey of existing repos (2026-11-11)

| Repo | Dalamud plugin? | Plugin JSON | Shape | Notes |
|---|---|---|---|---|
| [FFXIV-Remove-Duplicate-PF](https://github.com/pearstopher/FFXIV-Remove-Duplicate-PF) | Yes | `repo.json` (root of `main`) | List with one entry | Rewritten by its `release.yml` after each `v*.*.*` tag |
| [ffxiv-hide-housing-items](https://github.com/pearstopher/ffxiv-hide-housing-items) | No | none | n/a | Python tool that builds a Penumbra mod (`.pmp`), not a Dalamud plugin. Excluded |

Neither repo has GitHub topics yet.

### How a plugin publishes its `repo.json`

`FFXIV-Remove-Duplicate-PF` shows the expected pattern. Pushing a tag `vX.Y.Z` builds the plugin
and publishes `latest.zip` as a GitHub Release. `.github/scripts/make_repo_json.py` then copies
the DalamudPackager manifest fields, adds the download links and `LastUpdate`, and commits
`repo.json` to `main`. The aggregator only needs to read that file from each plugin's default
branch.

## Manifest format

Each plugin JSON is a list of manifest objects; a single bare object is also accepted. Fields
seen in practice:

`Author`, `Name`, `InternalName`, `AssemblyVersion`, `Description`, `Punchline`,
`ApplicableVersion`, `RepoUrl`, `IconUrl`, `Tags`, `DalamudApiLevel`, `LoadRequiredState`,
`LoadSync`, `CanUnloadAsync`, `LoadPriority`, `AcceptsFeedback`, `DownloadLinkInstall`,
`DownloadLinkUpdate`, `DownloadLinkTesting`, `LastUpdate`.

**Required** (an entry is skipped with a warning if any are missing):

- `Name`
- `InternalName`
- `AssemblyVersion`
- `DalamudApiLevel`
- `DownloadLinkInstall`

All other fields are copied through unchanged.

## Decisions

### Discovery
- A repo is included if it is owned by `pearstopher`, has the topic **`dalamud-plugin`**, and is
  not archived. Repos are listed through the GitHub API.
- `config.json` has `include` and `exclude` lists to add or drop repos by name, whatever their
  topics.
- **Action needed:** add the `dalamud-plugin` topic to `FFXIV-Remove-Duplicate-PF`.

### Fetching
- For each repo, try the candidate filenames from `config.json` (default `["repo.json"]`) on its
  default branch, using the GitHub contents API with the raw media type. This uses the
  authenticated rate limit and avoids the raw CDN cache.
- A failed fetch keeps that plugin's previous entry (#8). A repo that no longer matches discovery
  is dropped.

### Output
- `pluginmaster.json` at the root of this repo, served at
  `https://raw.githubusercontent.com/pearstopher/ffxiv-plugins/main/pluginmaster.json`.
- Duplicates are merged by `InternalName`, keeping the highest `AssemblyVersion` (compared as
  integers per dotted part).
- Deterministic bytes: entries sorted by `InternalName`, `indent=2`, `ensure_ascii=False`, LF line
  endings and a trailing newline. Rebuilding unchanged input produces no diff.

### Updates
- **Scheduled run** (#9): an hourly cron. The first step reads `auto_update.enabled` and
  `auto_update.interval_hours` from `config.json` and exits early unless the run is enabled and
  the hour lines up with the interval. Ships with `enabled: false` and `interval_hours: 1`.
- **Manual run:** `workflow_dispatch` always builds.
- **Instant run** (#10): a plugin's release workflow can send a `repository_dispatch` event
  (`plugin-updated`) to this repo after it commits `repo.json`. It needs a fine-grained PAT with
  Contents read/write on `ffxiv-plugins`, stored as a secret in the plugin repo. This trigger
  also follows `auto_update.enabled`.
- The workflow commits only when `pluginmaster.json` or the README plugin list changed, using
  `GITHUB_TOKEN` with `contents: write`.
