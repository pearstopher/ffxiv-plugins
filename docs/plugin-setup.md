# Plugin repo setup

How to connect a plugin repo so each release updates the combined list automatically. Do the
one-time setup once, then the per-plugin checklist for every plugin.

## One-time setup: the token

A plugin repo needs permission to tell `ffxiv-plugins` that something changed. That permission
is a fine-grained personal access token, which you create once and reuse in every plugin repo.

1. Open <https://github.com/settings/personal-access-tokens/new> (**Settings → Developer settings
   → Personal access tokens → Fine-grained tokens → Generate new token**).
2. **Token name:** `ffxiv-plugins notify`.
3. **Expiration:** pick the longest you're comfortable with and set a reminder before it ends.
   An expired token doesn't break releases, but the list silently stops updating.
4. **Repository access:** *Only select repositories* → `pearstopher/ffxiv-plugins`. Nothing else.
5. **Permissions → Repository permissions → Contents:** *Read and write*. (Metadata: read-only
   is added automatically.)
6. Click **Generate token** and copy it. You only need it for the `gh secret set` step below, so
   there is no need to save it anywhere else.

### Repos using the token

When the token is renewed, run step 3 of the checklist again for each of these:

- _None yet._

## Per-plugin checklist

Replace `<repo>` with the plugin repo's name.

1. **Topic.** Add the `dalamud-plugin` topic so the update workflow finds the repo:
   ```
   gh repo edit pearstopher/<repo> --add-topic dalamud-plugin
   ```
2. **`repo.json`.** The release workflow must commit a `repo.json` to the default branch: a list
   of Dalamud manifests (a single object also works). Each entry needs `Name`, `InternalName`,
   `AssemblyVersion`, `DalamudApiLevel` and `DownloadLinkInstall`. Its `RepoUrl` or
   `DownloadLinkInstall` must start with `https://github.com/pearstopher/<repo>/`, so that if a
   fetch fails, the previous entry can be kept.
   [FFXIV-Remove-Duplicate-PF](https://github.com/pearstopher/FFXIV-Remove-Duplicate-PF) is a
   working example (`.github/workflows/release.yml` and `.github/scripts/make_repo_json.py`).
3. **Secret.** Save the token in the plugin repo. The command asks for the value; paste the
   token there:
   ```
   gh secret set PLUGIN_REPO_TOKEN --repo pearstopher/<repo>
   ```
   Then add the repo to [Repos using the token](#repos-using-the-token).
4. **Notify step.** Add this to the release workflow **after** the step that pushes `repo.json`,
   so the update reads the new file:
   ```yaml
   - name: Notify ffxiv-plugins
     env:
       GH_TOKEN: ${{ secrets.PLUGIN_REPO_TOKEN }}
     run: gh api repos/pearstopher/ffxiv-plugins/dispatches -f event_type=plugin-updated
   ```
5. **Verify.** After the next release, open
   [ffxiv-plugins Actions](https://github.com/pearstopher/ffxiv-plugins/actions/workflows/update.yml):
   a **Update plugin list** run triggered by `repository_dispatch` should appear within a minute
   or two and commit the new version to `pluginmaster.json` and the README. For a first check
   without a release, run `gh workflow run update.yml --repo pearstopher/ffxiv-plugins`.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Notify step fails with 401 or 403 | Token expired, or it lacks access to `ffxiv-plugins` or Contents write. Create a new token and repeat step 3 for every repo in the list. |
| Notify step fails with 404 | Wrong repo name in the step, or the token can't see `ffxiv-plugins`. |
| Notify succeeds, but no update run appears | `event_type` isn't exactly `plugin-updated`. |
| Update runs, but the plugin is missing | Topic missing, `repo.json` missing on the default branch, or a required field missing. The run log shows a warning naming the problem. |
| Plugin shows an old version | The notify step ran before `repo.json` was pushed, or the fetch failed and the previous entry was kept (see the run log). Fix it, then run the workflow manually. |
