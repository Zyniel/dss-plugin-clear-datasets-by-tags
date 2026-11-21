# Issue tracker: GitHub

Issues and specs are GitHub issues. Use the `gh` CLI from the clone, which gives it the repo.

- **Read an issue**: `gh issue view <number> --json number,title,body,labels,comments`. Issues and PRs share one number sequence: when `#42` is no issue, it is `gh pr view 42`.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`, with `--label` and `--state` filters.
- **Sub-issue**: `gh issue create --parent <parent>`, or `gh issue edit <parent> --add-sub-issue <child>` afterwards.
- **Blocking**: GitHub's native issue dependencies, which its UI shows: `gh issue create --blocked-by <blocker>`, or `gh issue edit <child> --add-blocked-by <blocker>` afterwards. `gh issue view <n> --json blockedBy` lists the blockers.

When a skill says "publish to the issue tracker", create a GitHub issue. "Fetch the ticket" is **Read an issue** above.

**PRs as a request surface: no.** `/triage` reads this flag: it triages issues only, not external PRs.

## Wayfinding

The map of `/wayfinder` is one issue labelled `wayfinder:map`. Its tickets are its sub-issues, blocked by each other through native dependencies.

- **Frontier**: the open sub-issues of the map (`gh issue view <map> --json subIssues`) with no assignee and no open issue in their `blockedBy`. The first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`, the first write of the session.
