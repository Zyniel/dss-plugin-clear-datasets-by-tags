# AGENTS.md

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues for `Zyniel/dss-plugin-clear-datasets-by-tags`, using the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default triage labels are used as-is: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.

### Domain docs

Single-context: one `GLOSSARY.md` and one `docs/adr/` at the repo root. See `docs/agents/domain.md`.

### Coding standards

Python conventions that ruff cannot check, for writing or reviewing code: `CODING_STANDARDS.md`.

### Checks

`uv run python check.py` runs the checks of the CI and prints the output of those that fail. Run it before each commit. Before a pull request that changes the code DSS runs, also run the integration tests on the test DSS: see `docs/integration-tests.md`, "When to run them".

### Dataiku behaviour

What the Dataiku docs say about macros, scenarios and the API, with links, and what only a real DSS showed: `docs/verification.md`. Read it before searching the Dataiku docs, and add what you look up.

### Agents in a release

A release follows the runbook, `docs/releasing.md`. An agent may run the release review, start Prepare release, read the CI, run the integration tests on the release branch, and comment on the release pull request. The maintainer alone approves a run or a pull request, merges, and re-runs Release; the Release workflow alone tags and publishes. An agent never does any of these.

- **The release review** runs the skill `mattpocock-skills:code-review`, with the tag of the last release as its fixed point: `gh release list --exclude-drafts --limit 1 --json tagName --jq '.[0].tagName'`. Its spec is the notes of the next release, `## Unreleased` in `CHANGELOG.md`: each change that users can notice has an entry, and each entry matches the code.
- **Prepare release** runs with the version the maintainer gives: `gh workflow run prepare-release.yml --ref main -f version=<version>`.
- **The integration tests** run on the release branch with `install_plugin: true`, as `docs/integration-tests.md` says. Their result goes in a comment on the release pull request.

### Spec of a review

What a run shows (the recap, the log, the JSON recap, the summary dataset) is specified by the user guides and automation guides in `docs/macros/`, as well as by the issue: a Spec review checks the diff against both. It also checks that the notes of the next release stay true of the whole release, as `docs/releasing.md` says under "While you develop". The commits that fix review findings get a review of their own, by the reviewer that found the findings: send it the fix commit, which it checks alone. The review ends when it finds nothing to fix.
