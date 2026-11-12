# Maintaining

How the combined plugin list stays up to date, how to add a plugin, and how to work on this
repo. Design decisions are in [design.md](design.md).

## How updates work

`pluginmaster.json` and the plugin table in the [README](../README.md) are rebuilt by the
[Update plugin list](../.github/workflows/update.yml) workflow. It finds every pearstopher repo
with the `dalamud-plugin` topic and combines their `repo.json` files. It runs:

- **When a plugin is released.** The plugin's release workflow sends a `plugin-updated` event
  to this repo after publishing its new `repo.json`, so the list updates within a minute or two.
- **Manually.** Open **Actions → Update plugin list → Run workflow**, or run
  `gh workflow run update.yml`. Use this after adding a new plugin, or to refresh after an error.

It commits only when something changed. If a plugin's `repo.json` can't be fetched, its
previous entry is kept, so a temporary GitHub problem never removes a plugin from the list.

## Adding a new plugin

1. Give the plugin repo the `dalamud-plugin` topic.
2. Make sure its release workflow commits a `repo.json` to the default branch.
3. Add the release trigger so this list updates on every release.

## Development

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt   # macOS/Linux: .venv/bin/python
.venv/Scripts/python -m pytest
.venv/Scripts/python -m scripts.build_repo --dry-run
```

`python -m scripts.readme` regenerates the README plugin table from `pluginmaster.json`. It
only rewrites the text between the `<!-- plugins:start -->` and `<!-- plugins:end -->` markers.
