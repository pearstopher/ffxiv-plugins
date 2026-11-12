# FFXIV Plugins

One Dalamud custom repository for all of pearstopher's FFXIV plugins. Add this single link and
every plugin below shows up in the in-game plugin installer.

## Repository link

```
https://raw.githubusercontent.com/pearstopher/ffxiv-plugins/main/pluginmaster.json
```

## Installing

1. In game, type `/xlsettings` in chat to open the Dalamud settings.
2. Go to the **Experimental** tab and find **Custom Plugin Repositories**.
3. Paste the repository link above into the empty box, click **+**, and make sure its checkbox
   is ticked.
4. Click **Save and Close**.
5. Type `/xlplugins`, search for the plugin you want, and click **Install**.

Updates to installed plugins arrive through Dalamud as usual.

## Plugins

<!-- plugins:start -->
| Plugin | Description | Version |
| --- | --- | --- |
| [Remove Duplicate PF](https://github.com/pearstopher/FFXIV-Remove-Duplicate-PF) | Collapses duplicate Party Finder listings into one. | 1.1.2.0 |
<!-- plugins:end -->

## How updates work

`pluginmaster.json` and the table above are rebuilt by the
[Update plugin list](.github/workflows/update.yml) workflow, which finds every
pearstopher repo with the `dalamud-plugin` topic and combines their `repo.json` files. It runs:

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

Design notes are in [docs/design.md](docs/design.md).
