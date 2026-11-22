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
| `ci.yml` | On each push and pull request, and when Prepare release starts it | The checks of `check.py`, the tests included, and the zip, kept as the artifact `plugin-zip`. |
| `prepare-release.yml` | By hand, in the Actions tab | Checks that the version is new, runs `release.py prepare` and `uv lock`, runs the checks, pushes `release/<version>`, opens its pull request and starts the CI on it. |
| `tag-release.yml` | When a pull request from a `release/` branch is merged | Checks that the branch is named after the version of `plugin.json`, tags the merge commit, and starts Release on the tag. |
| `release.yml` | On a version tag, and by hand for a dry run | Checks that the tag is the version of `plugin.json`, runs the checks, builds the zip, writes the notes, and publishes the release. A dry run publishes nothing. |

A pull request or a tag that a workflow makes starts no workflow by itself: this is a rule of GitHub. This is why Prepare release starts the CI, and Tag release starts Release.

## Set up once

These settings are in GitHub, not in the repository. Only an administrator of the repository can change them.

1. **Settings > Actions > General > Workflow permissions:** check **Allow GitHub Actions to create and approve pull requests**. Without it, Prepare release cannot open the pull request.
2. **Settings > Rules > Rulesets**, recommended:
   - On `main`: require a pull request, and the three checks of the CI: "Lint, types and plugin zip", "Tests on Python 3.9" and "Tests on Python 3.13". The CI that Prepare release starts gives these checks to the release pull request. If the ruleset requires an approval, you can approve a release pull request: the workflow opened it, not you.
   - On tags (all tags): restrict updates and deletions, so that a released version never moves. Do not restrict creations: Tag release creates the tags.
3. **Settings > Code security:** turn on private vulnerability reporting. The [security policy](../.github/SECURITY.md) relies on it.

## While you develop

Each change that users can notice goes into the CHANGELOG, under `## Unreleased` at the top. Create this section with the first change after a release. Write for users: what changes for them, and what they must do. Prepare release refuses to run when the section is missing or empty.

## Release a version

1. **Choose the version**, `X.Y.Z`:
   - `Z` for fixes only;
   - `Y` for new features;
   - `X` for a change that can break a scenario or a script.

   A version with a suffix, such as `1.1.0-beta`, is published as a pre-release.
2. **Dry run, if you want:** in **Actions > Release > Run workflow**, keep "Dry run" checked and run it on `main`. It runs the checks, builds the zip and writes the notes of the next release: on `main`, the `## Unreleased` section. They are on the summary page of the run, and in its artifact `release-dry-run`. Nothing is published. Until the version is prepared, `plugin.json` gives the last version released: the zip has its name, and the run warns that it is released already.
3. **Prepare:** in **Actions > Prepare release > Run workflow**, give the version and run it. A few minutes later, the pull request "Release `<version>`" is open, and its CI is running.
4. **Check the pull request:**
   - The CI passes.
   - The zip works: download the artifact `plugin-zip` of its CI run (**Actions > CI**, the run on `release/<version>`), install it on a test DSS, and do the checks of [verification](verification.md) that the release touches.
   - The screenshots of the README show this version: on the branch `release/<version>`, run the refresh of the [screenshots](screenshots.md) on the test DSS, with `"install_plugin": true`. When a result differs from the README, fix the code or the README first. Then look at the four images, and commit them on the branch.
   - The notes read well. To change them, edit `CHANGELOG.md` on the branch: the CI runs again.
5. **Merge the pull request.** Tag release tags the version, and Release publishes it. The release is under **Releases** a few minutes later, and the release badge of the README follows.

Never publish with the **Draft a new release** form of GitHub: the release would exist already, and the Release workflow would fail.

## If something fails

| Failed | What to do |
|---|---|
| Prepare release | Read the log of its run. If the checks failed, nothing was pushed: fix `main`, and run it again. If the branch `release/<version>` exists from an earlier run, close its pull request and delete the branch first. |
| The CI of the release pull request | Fix it on the branch, as on any pull request. |
| Tag release | Tag the merge commit by hand, as in [Without the workflows](#without-the-workflows). A tag you push starts Release. |
| Release, because of a cause outside the repository (GitHub down, for example) | Run it again on the tag: **Actions > Release > Run workflow**, choose the tag, uncheck "Dry run". |
| Release, because of the code or the workflow | Fix it on `main`. Then delete the tag, and the release if it exists, and tag the fixed commit. A released version must never change once people may have downloaded it: if they may have, release a new version instead. |

## Without the workflows

Every step can also be done by hand:

```bash
uv run python release.py prepare 1.1.0   # The version in every file, and the CHANGELOG dated
uv lock
# Commit, open a pull request, check it as above, and merge it. From a branch release/1.1.0,
# Tag release does the rest. From any other branch, tag the merge commit:
git tag 1.1.0
git push origin 1.1.0                    # Starts the Release workflow
```

`release.py` is tested by `tests/plugin/test_release.py`.
