# Releasing

The runbook of a release: a version, published on GitHub with its tag, its plugin zip and its notes. A release takes one run of Prepare release and one merge: the merge of the release pull request tags the version and publishes its release, in one run of one workflow ([ADR-0003](adr/0003-a-release-is-published-when-its-release-pull-request-is-merged.md)). A released version never changes: nobody moves or deletes its tag ([ADR-0004](adr/0004-a-released-version-never-changes.md)). The words are those of the [glossary](../GLOSSARY.md#releases).

## Release a version

1. **While you develop,** the notes of the next release grow: each change that users can notice adds to `## Unreleased` in the CHANGELOG, as [While you develop](#while-you-develop) says. Every CI run shows them: in **Actions > CI**, open a run, and read "Notes of the next release" on its **Summary** page.
2. **Before a release, ask an agent to run the release review,** for example with "Run the release review": everything since the tag of the last release, with the notes of the next release as its spec, as `AGENTS.md` says. The agent runs the skill `mattpocock-skills:code-review`, two reviews side by side: the code against the coding standards, and the notes against the code. Fix what it finds on `main` in a pull request, with its notes: the agent reviews the fixes too. Go on when it has nothing open.
3. **Run Prepare release with the version.** Choose the version `X.Y.Z`: `Z` for fixes only, `Y` for new features, `X` for a change that can break a scenario or a script. `X.Y.Z-beta`, such as `1.1.0-beta`, is a pre-release: it comes before `X.Y.Z`, so `1.1.0` can follow `1.1.0-beta`, and `1.1.0-beta` cannot follow `1.1.0`. No other form is a version.

   In **Actions > Prepare release**, click **Run workflow**, keep the branch `main`, type the version in "The version to release", and click **Run workflow**. A minute later, the pull request "Release `<version>`" is open.

   Prepare release refuses a version it cannot prepare, at its step "Set the version and date the CHANGELOG", and the message of its log says what to do. It refuses a version that is not `X.Y.Z` or `X.Y.Z-beta`, such as `v1.1.0` or `1.1.0beta`; that does not come after the version of `plugin.json`; whose tag exists, since a released or abandoned version is never prepared again; whose branch `release/<version>` exists; or that has a section in the CHANGELOG already. It also refuses to run when the notes of the next release are empty. A refusal changes no file, and pushes nothing.
4. **On the release pull request, tick its checklist:**
   - **Approve its CI run, and the CI passes.** GitHub holds the CI of a pull request that a workflow opened until someone with write access approves it: the run waits for you, and this is not a fault ([GitHub docs](https://docs.github.com/en/actions/concepts/security/github_token)). In the merge box, at the bottom of the **Conversation** tab, click **Approve workflows to run**. Or, on the **Files changed** tab, click **Awaiting approval**, at the upper right, then **Approve workflows to run** ([GitHub docs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks)). Then check that the run started: the merge box shows the three required checks running, and they pass in about a minute. If they still wait for approval, GitHub did not get it: approve again. The required checks come from this run: the pull request cannot be merged without it.
   - **The release review has nothing open:** step 2.
   - **The integration tests pass on the branch, with `install_plugin: true`:** run `git fetch origin` and `git switch release/<version>`, set `"install_plugin": true` in your config file, and run them on the test DSS, as [integration tests](integration-tests.md#run-them) says. Or ask an agent to.
   - **The notes read well:** the pull request shows them. To change them, edit the section of the version in `CHANGELOG.md` on the branch: the CI runs again, with no approval since you pushed.

   While the release pull request is open, merge nothing else into `main`, not even a pull request of Dependabot. A change merged then would ship in the release untested, and its notes could land in the section of the version when the branch is updated, where the check of the release branch does not see them.
5. **Merge the pull request:** **Merge pull request**, then **Confirm merge**. The pull request then shows **Merged**. In **Actions > Release**, its run tags the merge commit and publishes the release. A minute later, the release is under **Releases**, and the release badge of the README follows. The **Summary** page of the run shows its notes.

Never push a tag, and never publish with the **Draft a new release** form of GitHub: Release tags the version, and publishes it.

## If something fails

There are three cases, and nothing else to do:

1. **Before the merge, while no tag exists, fix it and prepare again.** Prepare release refused the version or failed, or the CI of the release pull request, the release review or the integration tests found a problem: nothing is tagged. If a message says what to do, do it. Else close the release pull request, if it was opened, and delete its branch: **Delete branch** on the closed pull request, or the trash icon of `release/<version>` in **Code > Branches** ([GitHub docs](https://docs.github.com/en/pull-requests/how-tos/commit-changes/managing-branches-within-your-repository#deleting-a-branch)). Then fix the cause on `main`, and prepare the version again, from step 3.
2. **After the merge, "Re-run failed jobs".** Release failed for a cause outside the repository, such as GitHub down or a download that failed. In **Actions > Release**, open its run, choose **Re-run jobs > Re-run failed jobs**, then **Re-run jobs**. The re-run finds the tag on the merge commit and the release that exist, and does only the rest: it never replaces them. A run can be re-run for 30 days ([re-run](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)).
3. **When a re-run cannot fix it, release the next patch version.** A re-run runs the workflow and the code of the merge commit again: it cannot fix a cause in the code or in a workflow, a branch that is not named after the version, or a tag of the version on another commit. The log of the run shows which. Fix the cause on `main`, and release the next patch version: `1.0.4-beta` after `1.0.3-beta`. The version that failed is never released. With its tag, it is an abandoned version, and its tag stays. Without its tag, as when the run failed before the tag, it is not abandoned, but the next patch version is the way out all the same. In the pull request of the fix, its section of the CHANGELOG goes back under `## Unreleased`, with the fix: the next version publishes its changes.

## While you develop

Each change that users can notice goes into the CHANGELOG, under `## Unreleased` at the top: the notes of the next release. Create this section with the first change after a release. Write for users: what changes for them, and what they must do. Prepare release refuses to run when the section is missing or empty.

A pull request that changes the plugin, `plugin.json`, `python-lib/`, `python-runnables/` or `resource/`, adds to these notes: its required check "Lint, types and plugin zip" fails when it does not, at the step "Check that a pull request that changes the plugin adds to the notes of the next release", and names the files it changes. The README and the license are not checked. When users cannot notice the change, such as a refactoring, add the label `no-changelog` to the pull request instead: the CI runs again, without this step. Removing the label runs it again too. On your machine, `uv run python release.py check-pull-request origin/main HEAD` gives the same verdict for your commits.

The [pull request template](../.github/pull_request_template.md) lists what each pull request needs: these notes, the screenshots when the recap or a form changes, the integration tests when the code DSS runs changes, and the checks. The screenshots are refreshed in the pull request that changes what they show, not at release time.

## The workflows

| Workflow | Starts | Does |
|---|---|---|
| `ci.yml` | On each push and pull request, and when a label of a pull request is added or removed. On a release pull request, once you approve its run. | Writes the notes of the next release on the summary page of the run. On a release branch, fails when they are not empty. On a pull request that changes the plugin, fails when they do not change, unless it comes from a release branch or has the label `no-changelog`. Runs the checks of `check.py`, and keeps the plugin zip as the artifact `plugin-zip`. |
| `prepare-release.yml` | By hand: **Actions > Prepare release > Run workflow** | Runs `release.py prepare`, which checks that it can prepare the version, and `uv lock`, runs the checks, pushes `release/<version>`, and opens its release pull request, with its checklist and its notes. |
| `release.yml` | When a pull request from a `release/` branch of this repository is merged into `main` | Reads the version of the plugin with `release.py version`, and checks that the branch is named after it. Writes the notes of the version, runs the checks, tags the merge commit, and publishes the release with the plugin zip and the notes, as a pre-release when `release.py is-pre-release` says so. Goes on past a tag on the merge commit and a published release, which an earlier run made. |

No workflow starts another. The CI of a release pull request starts when you approve it, and the tag that Release pushes starts no run: a push with the token of a workflow starts none ([GitHub docs](https://docs.github.com/en/actions/concepts/security/github_token)), and Release has no trigger on tags. GitHub adds the source code of the tag to each release, as **Source code (zip)** and **Source code (tar.gz)**. `release.py` is tested by `tests/plugin/test_release.py`.

## Set up once

The release process relies on the first three of these settings of GitHub, item 4 says why creating a tag stays open, and the security policy relies on the last one. Only an administrator of the repository can change them. Each comes with the command that applies it and the command that checks it, from the root of the repository, the same in bash and PowerShell. The rulesets are in `.github/rulesets/`, as the API reads them. All are applied, and their checks gave the results below on 2026-11-22 (issue #44). `gh api repos/Zyniel/dss-plugin-clear-datasets-by-tags/rulesets --jq '.[] | {id, name}'` lists the rulesets of the repository, with their ids.

1. **GitHub Actions can create pull requests,** so that Prepare release opens the release pull request: **Settings > Actions > General > Workflow permissions**, "Allow GitHub Actions to create and approve pull requests". The token of a workflow can only read, unless the workflow asks for more.

   ```powershell
   gh api --method PUT repos/Zyniel/dss-plugin-clear-datasets-by-tags/actions/permissions/workflow -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true
   ```

   ```powershell
   gh api repos/Zyniel/dss-plugin-clear-datasets-by-tags/actions/permissions/workflow
   ```

   The check prints `{"default_workflow_permissions":"read","can_approve_pull_request_reviews":true}`.
2. **The ruleset "Protect main"**, id 27543242: a change reaches `main` through a pull request whose three required checks pass, "Lint, types and plugin zip", "Tests on Python 3.9" and "Tests on Python 3.13". A branch must be up to date to be merged, so the plugin zip you tested is the plugin zip of the release. `main` accepts only merge commits, so the commits that fix review findings stay as they are. Nobody deletes `main` or forces a push on it, and the ruleset has no bypass.

   ```powershell
   gh api --method PUT repos/Zyniel/dss-plugin-clear-datasets-by-tags/rulesets/27543242 --input .github/rulesets/protect-main.json
   ```

   ```powershell
   gh api repos/Zyniel/dss-plugin-clear-datasets-by-tags/rulesets/27543242 --jq '{bypass_actors, rules}'
   ```

   The check prints the bypass actors and the rules of `protect-main.json`: no bypass actor, `"allowed_merge_methods":["merge"]` and `"strict_required_status_checks_policy":true`.
3. **The ruleset "Protect release tags"**, id 27543928: nobody deletes, moves or forces a tag, the administrator included, since it has no bypass ([ADR-0004](adr/0004-a-released-version-never-changes.md)).

   ```powershell
   gh api --method PUT repos/Zyniel/dss-plugin-clear-datasets-by-tags/rulesets/27543928 --input .github/rulesets/protect-release-tags.json
   ```

   ```powershell
   gh api repos/Zyniel/dss-plugin-clear-datasets-by-tags/rulesets/27543928 --jq '{bypass_actors, rules}'
   ```

   The check prints `{"bypass_actors":[],"rules":[{"type":"deletion"},{"type":"non_fast_forward"},{"type":"update"}]}`.
4. **Creating a tag stays open:** GitHub does not accept GitHub Actions as a bypass actor of a ruleset of this repository. Issue #44 tried it on 2026-11-22: a ruleset "Create release tags", with the rule `{"type":"creation"}` on every tag and the bypass actor `{"actor_id":15368,"actor_type":"Integration","bypass_mode":"always"}` (GitHub Actions), sent with `gh api --method POST repos/Zyniel/dss-plugin-clear-datasets-by-tags/rulesets --input <the ruleset>`. GitHub answered `422 Validation Failed`, "Actor GitHub Actions integration must be part of the ruleset source or owner organization", and created nothing. A rule `creation` with any other bypass, such as the administrator, would stop Release too: the token of its workflow pushes the tag, and the rule would refuse it.

   So whoever can write to the repository, only you today, can create a tag. Never push one: Release creates the tag of each version. A tag pushed by hand cannot be deleted either (item 3): if it names a version, Prepare release refuses that version, and Release would refuse its tag, which is not on the merge commit of a release pull request. The version is abandoned.
5. **Private vulnerability reporting:** the [security policy](../.github/SECURITY.md) relies on it.

   ```powershell
   gh api --method PUT repos/Zyniel/dss-plugin-clear-datasets-by-tags/private-vulnerability-reporting
   ```

   ```powershell
   gh api repos/Zyniel/dss-plugin-clear-datasets-by-tags/private-vulnerability-reporting
   ```

   The check prints `{"enabled":true}`.
