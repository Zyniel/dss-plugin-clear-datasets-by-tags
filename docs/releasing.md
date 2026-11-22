# Releasing

How a version goes from the CHANGELOG to a GitHub release with the plugin zip. Workflows do the mechanical work. You write the CHANGELOG, test the zip on a DSS, and merge.

## What a release contains

| Asset | Made by |
|---|---|
| `dss-plugin-clear-datasets-by-tags-<version>.zip`: the plugin, to upload in DSS | The Release workflow |
| **Source code (zip)** and **Source code (tar.gz)**: the whole repository at the tag | GitHub, for every release |
| The notes | The Release workflow, from the section of the version in the CHANGELOG |

## The process

```
You                                   Workflows
───                                   ─────────
Write the changes under
"## Unreleased" in the CHANGELOG
        │
Run "Prepare release"  ─────────────▶ Prepare release: sets the version, dates the
with the version                      CHANGELOG, runs the checks, opens the pull
                                      request release/<version>, starts the CI on it
        │
Test the zip on a DSS  ◀───────────── CI: checks, tests, and the plugin zip
                                      (artifact "plugin-zip")
        │
Merge the pull request ─────────────▶ Tag release: tags the merge commit with the
                                      version, starts Release on the tag
                                              │
                                      Release: checks, zip, notes, GitHub release
```

| Workflow | Starts | Does |
|---|---|---|
| `ci.yml` | On each push and pull request, when a label of a pull request is added or removed, and when Prepare release starts it | Writes the notes of the next release on the summary page of the run. On a release branch, fails when they are not empty. On a pull request that changes the plugin, fails when they do not change, unless it comes from a release branch or has the label `no-changelog`. Runs the checks of `check.py`, and keeps the zip as the artifact `plugin-zip`. |
| `prepare-release.yml` | By hand, in the Actions tab | Runs `release.py prepare`, which checks that it can prepare the version, and `uv lock`, runs the checks, pushes `release/<version>`, opens its pull request and starts the CI on it. |
| `tag-release.yml` | When a pull request from a `release/` branch is merged | Checks that the branch is named after the version of `plugin.json`, tags the merge commit, and starts Release on the tag. |
| `release.yml` | On a version tag, and when Tag release starts it on the tag | Checks that the tag is the version of `plugin.json`, runs the checks, builds the zip, writes the notes, and publishes the release. |

A pull request or a tag that a workflow makes starts no workflow by itself: this is a rule of GitHub. This is why Prepare release starts the CI, and Tag release starts Release.

## Set up once

These settings are in GitHub, not in the repository. Only an administrator of the repository can change them.

1. **Settings > Actions > General > Workflow permissions:** check **Allow GitHub Actions to create and approve pull requests**. Without it, Prepare release cannot open the pull request.
2. **Settings > Rules > Rulesets**, recommended:
   - On `main`: require a pull request, and the three checks of the CI: "Lint, types and plugin zip", "Tests on Python 3.9" and "Tests on Python 3.13". The CI that Prepare release starts gives these checks to the release pull request. If the ruleset requires an approval, you can approve a release pull request: the workflow opened it, not you.
   - On tags (all tags): restrict updates and deletions, so that a released version never moves. Do not restrict creations: Tag release creates the tags.
3. **Settings > Code security:** turn on private vulnerability reporting. The [security policy](../.github/SECURITY.md) relies on it.

## While you develop

Each change that users can notice goes into the CHANGELOG, under `## Unreleased` at the top: the notes of the next release. Create this section with the first change after a release. Write for users: what changes for them, and what they must do. Prepare release refuses to run when the section is missing or empty.

A pull request that changes the plugin, `plugin.json`, `python-lib/`, `python-runnables/` or `resource/`, adds to these notes: its required check "Lint, types and plugin zip" fails when it does not, at the step "Check that a pull request that changes the plugin adds to the notes of the next release", and names the files it changes. The README and the license are not checked. When users cannot notice the change, such as a refactoring, add the label `no-changelog` to the pull request instead: the CI runs again, without this step. Removing the label runs it again too. On your machine, `uv run python release.py check-pull-request origin/main HEAD` gives the same verdict for your commits.

The [pull request template](../.github/pull_request_template.md) lists what each pull request needs: these notes, the screenshots when the recap or a form changes, the integration tests when the code DSS runs changes, and the checks. The screenshots are refreshed in the pull request that changes what they show, not at release time.

Every run of the CI shows the notes of the next release, with links that work: open the run in **Actions > CI**, and read "Notes of the next release" on its **Summary** page. When they are empty, it says so.

## Release a version

1. **Choose the version**, `X.Y.Z`:
   - `Z` for fixes only;
   - `Y` for new features;
   - `X` for a change that can break a scenario or a script.

   `X.Y.Z-beta`, such as `1.1.0-beta`, is published as a pre-release. It comes before `X.Y.Z`: `1.1.0` can follow `1.1.0-beta`, and `1.1.0-beta` cannot follow `1.1.0`. No other form is a version.
2. **Read the notes of the next release:** on the **Summary** page of the last CI run on `main`, in **Actions > CI**. They are the notes that the version will publish. To change them, change `## Unreleased` on `main`, as for any change.
3. **Prepare:** in **Actions > Prepare release > Run workflow**, give the version and run it. A few minutes later, the pull request "Release `<version>`" is open, and its CI is running.

   Prepare release refuses a version it cannot prepare, at its step "Set the version and date the CHANGELOG", and the message of its log says what to do. It refuses a version that is not `X.Y.Z` or `X.Y.Z-beta`, such as `v1.1.0` or `1.1.0beta`; that does not come after the version of `plugin.json`; whose tag exists, since a released or abandoned version is never prepared again; whose branch `release/<version>` exists; or that has a section in the CHANGELOG already. It also refuses to run when the notes of the next release are empty. A refusal changes no file, and pushes nothing.
4. **Check the pull request:**
   - The CI passes.
   - The zip works: download the artifact `plugin-zip` of its CI run (**Actions > CI**, the run on `release/<version>`), install it on a test DSS, and do the checks of [verification](verification.md) that the release touches.
   - The notes read well. To change them, edit `CHANGELOG.md` on the branch: the CI runs again.
5. **Merge the pull request.** Tag release tags the version, and Release publishes it. The release is under **Releases** a few minutes later, and the release badge of the README follows.

Never publish with the **Draft a new release** form of GitHub: the release would exist already, and the Release workflow would fail.

## If something fails

| Failed | What to do |
|---|---|
| Prepare release | Read the log of its run. If it refused the version, its message says why and what to do. If the checks failed, nothing was pushed: fix `main`, and run it again. If the branch `release/<version>` exists from an earlier run, close its pull request and delete the branch first. |
| The CI of the release pull request | Fix it on the branch, as on any pull request. If the fix needs an entry in the CHANGELOG, write it in the section of the version: a release branch has no `## Unreleased`. When its step "Check that a release branch has no notes of the next release" fails, changes reached the branch after Prepare release dated the notes: they would ship untested, and missing from the notes of the version. Close the release pull request, delete its branch, and prepare the version again. |
| Tag release | Tag the merge commit by hand, as in [Without the workflows](#without-the-workflows). A tag you push starts Release. |
| Release, because of a cause outside the repository (GitHub down, for example) | Run it again on the tag: **Actions > Release > Run workflow**, choose the tag in "Use workflow from", and run it. |
| Release, because of the code or the workflow | Fix it on `main`. Then delete the tag, and the release if it exists, and tag the fixed commit. A released version must never change once people may have downloaded it: if they may have, release a new version instead. |

## Without the workflows

Every step can also be done by hand:

```bash
uv run python release.py prepare 1.1.0   # The version in every file, and the CHANGELOG dated. Reads origin.
uv lock
# Commit, open a pull request, check it as above, and merge it. From a branch release/1.1.0,
# Tag release does the rest. From any other branch, tag the merge commit:
git tag 1.1.0
git push origin 1.1.0                    # Starts the Release workflow
```

`release.py` is tested by `tests/plugin/test_release.py`.
