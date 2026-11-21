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

### Spec of a review

What a run shows (the recap, the log, the JSON recap, the summary dataset) is specified by the user guides and automation guides in `docs/macros/`, as well as by the issue: a Spec review checks the diff against both. The commits that fix review findings get a review of their own.
