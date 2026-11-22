<!-- What the pull request changes, and why. Link its issue, such as "Closes #12". -->

## Checklist

- [ ] **The notes of the next release:** each change that users can notice is described for them under `## Unreleased` in `CHANGELOG.md`. The CI fails when the pull request changes the plugin (`plugin.json`, `python-lib/`, `python-runnables/` or `resource/`) and not these notes. For a change that users cannot notice, the maintainer adds the label `no-changelog` instead.
- [ ] **The screenshots,** when the recap or a form of a macro changes: refreshed on the test DSS and committed in this pull request, as `docs/screenshots.md` says. A release no longer refreshes them.
- [ ] **The integration tests,** when the code DSS runs changes: they pass on the test DSS, as `docs/integration-tests.md` says. Write the result below.
- [ ] **The checks:** `uv run python check.py` passes.
