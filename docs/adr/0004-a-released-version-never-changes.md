# A released version never changes

Once the tag of a version exists, nobody moves or deletes it, the administrator of the repository included: the tag ruleset has no bypass. Users may have installed its plugin zip, and a version must mean the same code for all of them. When the Release workflow fails, there are two ways out. When the cause is outside the repository, such as GitHub being down, "Re-run failed jobs" finishes it. When the cause is in the code or in a workflow, a re-run cannot fix it, since it runs the workflow of the original commit ([re-run](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)): the fix goes to `main`, and the next patch version is released. We rejected the earlier recovery, which deleted the tag and tagged the fixed commit: it needs the bypass of an administrator, and nothing would tell a user that the version they installed is not the one released.

## Consequences

- A run of Release that fails can cost a version number. The tag of the version stays with no release: it is an abandoned version. Its section of the CHANGELOG goes back under `## Unreleased` with the fix, and the next version publishes its changes.
- Each step of the Release workflow can run twice: it skips a tag or a release that exists, and never replaces them.
