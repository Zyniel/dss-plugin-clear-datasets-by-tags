# Changelog

The changes of each version of the plugin, the most recent first. The changes not released yet are under **Unreleased**.

## Unreleased

### For developers

- The runbook and the release pull request say where to approve the CI of the release pull request, in its merge box, and how to check that the run started. The runbook names the skill that runs the release review, `mattpocock-skills:code-review`, as `AGENTS.md` does.

## 1.0.3-beta - 2026-11-22

### Plugin

- The install steps of the README link to the releases of the repository, where the latest release is at the top, pre-releases included. They linked to the latest release of GitHub, which excludes pre-releases, and every release so far is a pre-release. The README has one release badge, which includes pre-releases, instead of "Latest release" and "Pre-release", and it links to the releases too: "Latest release" showed nothing, for the same reason.

### For developers

- The workflows set themselves up with one shared step, the composite action `.github/actions/setup`: it checks out the commit of the run, or the ref it is given, with the history it is given, installs uv, and syncs the locked environment on the Python of `.python-version`. They call it with `uses: $/.github/actions/setup`, which GitHub takes from the commit of the run, before any checkout. Their GitHub Actions run on Node.js 24, so GitHub no longer warns that Node.js 20 is deprecated: `actions/checkout@v7`, `actions/upload-artifact@v7` and `astral-sh/setup-uv@v7`. Dependabot keeps them current, those of the setup step included: one pull request a month, with every update. See `.github/dependabot.yml`.
- `GLOSSARY.md` gives the words of releases, such as pre-release, notes of the next release, release pull request, release review and abandoned version. Two ADRs record the decisions of the release process: a release is published when its release pull request is merged (ADR-0003), and a released version never changes, since nobody moves or deletes its tag (ADR-0004).
- `docs/agents/` keeps only what the agent skills read in this repository. `issue-tracker.md` gives the `gh` commands to read and list issues, to add a sub-issue, and to mark an issue as blocked by another, with the `--blocked-by` flags of `gh` instead of its API. It says how `/wayfinder` finds and claims its next ticket, with `--json subIssues` and `--json blockedBy`. It no longer gives the commands every agent knows, such as creating, commenting on or closing an issue, the API calls for an older `gh`, or the triage of pull requests, which this repository turns off. `domain.md` says to read `GLOSSARY.md` and the ADRs of `docs/adr/`, to use the words of the glossary and to flag a conflict with an ADR, without the layouts of the docs, which `AGENTS.md` gives for this repository. `triage-labels.md` is gone, since `AGENTS.md` names the labels.
- The release code follows `CODING_STANDARDS.md`. In `release.py`, the line that holds the version in each file is a `VersionLine`, the repository and the ref that make the links of the notes absolute are one `LinkTarget`, the order of versions is a `VersionOrder`, each parameter is documented, and one table gives what each command runs. The release tests run `release.py` at its command line, most of them on a copy of its files in a git repository with a remote `origin`, and import it with its types: pytest and ruff see the scripts at the root of the repository. `read_json()` is in `tests/support/files.py`. mypy checks the Claude Code hook, and the repository layout of the development doc lists `AGENTS.md`, `.claude/` and `docs/agents/`.
- The tests jobs of the CI run their tests through `check.py`, as you do on your machine: `check.py --tests-on 3.13` runs only the tests, on Python 3.13. `check.py` gives the checks and the Python versions of the tests, and `--help` lists the versions. The matrix of the CI repeats them, one required check each: given a version it does not test, `check.py` fails, and lists the versions it tests. The full run names each test check after its Python, such as "pytest on Python 3.9". The development doc and the releasing doc point to `check.py` instead of listing its checks, and the contributing guide gives its command. The required checks keep their names.
- Prepare release refuses a version it cannot prepare, at its step "Set the version and date the CHANGELOG", with a message that says what to do: a version that is not `X.Y.Z` or `X.Y.Z-beta`, such as `v1.1.0`, `1.1.0beta` or `1.1.0-rc.1`; a version that does not come after the version of `plugin.json`, the same version included, as `-beta` comes before the same version without it; a version whose tag exists, released or abandoned; a version whose release branch exists; a version that has a section in the CHANGELOG already; and empty notes of the next release. A refusal changes no file and pushes nothing. These rules are in `release.py prepare`, which reads the tags and branches of the remote `origin`, and its tests run it on a git repository with a remote. The workflow has no bash check of its own any more. `docs/verification.md` gives what the Dataiku docs say of the version of a plugin, and of installing a plugin from a zip or from Git.
- Every CI run writes the notes of the next release on its summary page, with links to the files of its commit, or says that they are empty. On a release branch of this repository, the required check "Lint, types and plugin zip" fails when the notes of the next release are not empty: changes that reached the branch after Prepare release would ship untested, and missing from the notes of the version. Its message says to close the release pull request, delete its branch, and prepare the version again. A `release/` branch of a fork is not a release branch. `release.py next-release-notes` prints the notes of the next release, and `release.py check-branch` checks a branch, both tested at the command line of `release.py`. The Release workflow has no dry run any more, and `release.py notes` no `--unreleased-first`: read the notes of the next release in the CI, as [releasing](docs/releasing.md) says. The required checks keep their names.
- A pull request that changes the plugin adds to the notes of the next release. When it changes `plugin.json`, `python-lib/`, `python-runnables/` or `resource/`, and not `## Unreleased`, the required check "Lint, types and plugin zip" fails, names the files, and says to add the notes, or the label `no-changelog` for a change that users cannot notice. The label skips the check, and adding or removing it runs the CI again. `release.py check-pull-request` checks the changes of a pull request, tested at its command line on a temporary git repository. The CI runs it on each pull request but a release pull request, and not on a push. The zip builder and the check share the list of the folders of the plugin zip, `PLUGIN_FOLDERS`, and a test checks it against the zip. A pull request template gives the checklist of each pull request: the notes of the next release, the screenshots when the recap or a form changes, the integration tests when the code DSS runs changes, and the checks. The screenshots are refreshed in the pull request that changes what they show, no longer at release time. The contributing guide points to the template. The required checks keep their names.
- A release is published when its release pull request is merged: the Release workflow runs on that merge, reads the version of the plugin with `release.py version` and checks that the branch is named after it, runs the checks, tags the merge commit, and publishes the release with the plugin zip and the notes, as a pre-release when `release.py is-pre-release` says so. Both commands are tested at the command line of `release.py`. A re-run goes on past a tag on the merge commit and a published release, and fails on a tag of the version on another commit: "Re-run failed jobs" finishes a run of Release that failed for a cause outside the repository. Release only needs to write the contents of the repository, and has no manual start and no trigger on tags. The Tag release workflow is gone, and no workflow starts another: Prepare release no longer starts the CI, which loses its manual start. GitHub holds the CI run of the release pull request until the maintainer approves it, and the pull request lists the checklist of a release and shows its notes. Prepare release only writes the contents and the pull requests. [Releasing](docs/releasing.md) is a runbook: release a version, the three cases of a failure, and the settings of GitHub with the commands that apply and check them, whose rulesets are in `.github/rulesets/`. "Without the workflows" is gone. `AGENTS.md` says what an agent may do in a release.
- The settings of GitHub that the runbook lists are applied. `main` accepts only merge commits, and a branch must be up to date with `main` to be merged: **Update branch** on the pull request, which runs its CI again. Nobody deletes or moves a tag, the administrator included. Creating a tag stays open: GitHub refuses GitHub Actions as a bypass actor of a ruleset, so a rule that only lets Release create tags is not possible. The runbook says what was tried, and never to push a tag.

## 1.0.2-beta - 2026-11-21

### Plugin

- The notes of 1.0.0-beta below are corrected, where they said more than the plugin does. No banner shows the outcome of a run itself: the banners show its problems. Only Clear Datasets by Tags has `blockers` in its JSON recap. "Sharing not checked" is on each dataset to clear, not on every dataset. The GitHub release of 1.0.0-beta keeps its first notes.

### Clear Datasets by Tags

- When datasets fail and the run goes on, the red banner gives all the counts in bold, then how to list the failed datasets: **2 of 4 datasets failed, 2 cleared.** Click "Failed" to list them. The log, the JSON recap and the message of a failed run do not change.
- The messages put the labels of the form between double quotes, as the banners do. The detail of a skipped dataset reads `Has no recipe; "Clear datasets with no recipe" is unchecked`, in the recap, the JSON recap and the summary dataset. The error of a form with no included tag reads `Give at least one included tag, or choose "All datasets" in "Include".`
- In the log, the decision for a dataset to clear gives each of its risks after "risk:", no longer after "warning:".
- The form says "clear", not "purge": the included tags are "Tags of the datasets to clear.", and the excluded tags "Datasets with these tags are never cleared." "Included tags match" and "Excluded tags match" offer "Any" and "All", as the user guide and the recap say. The parameters and their values do not change.
- The docs say what the macro does in three more cases. With "Append mode" unchecked, the summary dataset holds the last run only, so a run with no selected dataset empties it. A real run that a check blocks writes no row to the summary dataset and no `RECAP_JSON` line: its message is in the "Last runs" of the scenario. "Sharing not checked" is on each dataset to clear: a skipped or excluded dataset is not cleared.

### Report Dataset Tags

- The user guide lists the yellow banners in the order the recap shows them: the notices, then a summary dataset that was not written.

### Every macro

- The error of a "Summary" section with no dataset picked puts the label between double quotes: `Pick a summary dataset, or uncheck "Write to a dataset".`
- An "AG Grid URL" or an "AG Grid integrity hash" that the macros ignore gets its WARNING line at the start of the log, no longer after the `RECAP_JSON` line, where DSS could miss it. The admin guide says which values the macros accept: with any other, downloaded recaps show the simple table.
- The automation guides list the `Problem:` and `Outcome:` lines of the log, and the fields of the JSON recap in their order: `outcome` and `problems` come last. They also say that a run whose form is not valid writes no recap.

### For developers

- `GLOSSARY.md` gives the words of the plugin, such as tag rules, protection, foreign dataset and blocked run. `docs/adr/` records the decisions that are hard to reverse, such as why "Clear shared datasets" is checked by default, and why an excluded tag on no dataset is only a notice. The docs and the code use these words: `RunStopped` is now `RunBlockedError`, `TagSelection` is `TagRules`, `recap_columns` is `summary_columns`, and `cleanup.py` is `clearing.py`. The parameters of the forms, the JSON recap and the summary dataset do not change.
- The problems of a run are handled in one module, `core/problems.py`. It gives each problem its banner, its log line and its part of the message of a failed run, and it sets the outcome. A macro only says what failed in its work, once: `describe_failures()` returns a `WorkFailure`, with the message and a hint for the banner, or `None`. A macro no longer draws the banner of its failures: the runner always does.
- `CODING_STANDARDS.md` gives the Python conventions that ruff cannot check, and ruff checks more: docstrings (`D`), names (`N`), and the rules `C4`, `PERF`, `PIE`, `PT`, `RET`, `RUF` and `SIM`. The code follows them. The functions that return HTML are `render_*`, the ones that return data `build_*`. The text helpers are `format_*` or `describe_*`, in the new `recap/text.py`: `count_of()` is now `format_count()`, `dss_said()` is `describe_dss_error()`, and `text()` is `escape_text()`. `RunFailed` is now `RunFailedError`. The dataset row, the tag row, the summary dataset result and the AG Grid of the plugin settings are `TypedDict`s. The words of the glossary replace scope (`INCLUDE_*`, `read_include()`) and warning (`RISK_SHARING_NOT_CHECKED`). The test helpers that two files need are in `tests/support`. The parameters of the forms, the fields of the JSON recap and the columns of the summary dataset do not change.
- The fixtures of the integration tests are in `tests/integration/fixtures.py`, and `tests/conftest.py` shares them with every test folder. The new `tests/screenshots` folder, for the screenshot tests of the README, can use them. Its tests run only when pytest gets `--screenshots`, even when `DSS_INTEGRATION_CONFIG` is set: running the tests never rewrites the README images. The integration tests do not change.
- The screenshot tests drive the DSS UI in Chromium. They need the new `screenshots` dependency group (Playwright and Pillow) and a UI login in the config file of the integration tests: see `docs/screenshots.md`.
- The screenshot tests create the demo projects of the README, `SALES` and `FINANCE`, from code, run both macros on `SALES` through the API, and check the results the README states. They all stop before any change when the tag categories of DSS do not give the recap of the README, or when a project `SALES` or `FINANCE` exists that they did not make. They mark the projects they make, delete only those, and delete them at the end, also when a step fails. The integration tests gain helpers for them: a dataset built from a dataset you give, a partitioned dataset, the tags of a recipe, and sharing a dataset.
- One refresh takes the four README screenshots again on the demo projects: for each macro, it fills the form as the README describes it, takes a screenshot of the form, runs the macro in the UI as the UI login of the config file, and takes a screenshot of its recap. Its browser steps start only once the API runs give the results the README states, and it writes the four images only once all four are taken and checked. The README images are taken again. The guide to adding a macro and the release guide say when to run it: see `docs/screenshots.md`.
- `check.py` runs the checks of the CI, one after the other, and prints the output of those that fail: `uv run python check.py`. The CI, Prepare release and Release call it, so the checks are the same everywhere. Prepare release and Release now also run the tests on Python 3.13, and Prepare release builds the zip, as the CI does.
- A test checks the order of the banners that the user guide gives, through the runner: by colour, then in each colour the banners of the macro, the notices, then the problems.
- `docs/verification.md` says what the Dataiku docs say about macros, scenarios and the API, with links, and what they leave out.
- For Claude Code, a hook of `.claude/settings.json` runs ruff on each Python file Claude edits, and `AGENTS.md` points to `check.py`, to the Dataiku docs of `docs/verification.md`, and to the user guides as part of the spec of a review.
- The guide to the integration tests says when to run them: before a pull request that changes the code DSS runs. Coding agents run them too, on the test DSS of the config file. Run with an editor and a reader on DSS 13.4.4, they confirm rows 8, 13, 22 and 24 of the verification: an editor who is not a project administrator cannot read the sharing, as ADR-0001 assumes.
- A dry run of the Release workflow on `main` writes the notes of the next release, from `## Unreleased`, as the release guide says. It wrote those of the last version released, which `plugin.json` still gives until the version is prepared.

## 1.0.1-beta - 2026-11-18

### Plugin

- The README shows each macro with a screenshot of its recap, taken in DSS, and of its form, in a folded block.

## 1.0.0-beta - 2026-11-18

First version of the Dataiku plugin **Clear Datasets by Tags**.

### Plugin

- Id `clear-datasets-by-tags`, name "Clear Datasets by Tags". Works with DSS 13 and later, in the built-in Python 3.9 environment.
- Released under the [MIT License](LICENSE). The zip contains the `LICENSE` file.
- The macros are in the **Project maintenance** section of the Macros page of a project.
- Plugin settings:
  - **AG Grid URL** and **AG Grid integrity hash**: the AG Grid that downloaded recaps load. Several hashes, separated by spaces, are accepted.
  - **Tag categories**: the "Cat. Tags" lists of the forms offer only the tags of these categories. An entry such as `Stage:` or `Stage:Raw` means `Stage`. Empty: all categories.
- A guide for DSS administrators: [admin guide](docs/admin-guide.md).

### Clear Datasets by Tags

- **Include**: "Datasets with the included tags" (default) or "All datasets". "All datasets" selects every dataset of the project, except the excluded ones: the form hides the included tags, and a notice names any value they still have. See the table of the [user guide](docs/macros/clear-datasets-by-tags/user-guide.md#select-the-datasets).
- Included tags and excluded tags: each list takes tags typed by hand and category tags picked from a list, and matches "Any" (at least one tag) or "All" (every tag). A run with excluded tags only is refused, and clears nothing.
- "Simulate" is checked by default: nothing is cleared until it is unchecked. A simulation marks a dataset to clear "Cleared (Simulate)", with the code `WOULD_BE_CLEARED` in the JSON recap and the summary dataset.
- Advanced options: "Clear shared datasets" (checked), "Clear partitioned datasets" and "Clear datasets with no recipe" (unchecked).
- External datasets and the summary dataset are never cleared.
- "If an error occurs", in the "Run" section: "Continue, run ends in error" (default), "Continue, run ends as success", or "Raise exception", which stops at the first dataset that cannot be cleared. A run that ends in error turns a scenario step red. The count of a stopped run gives the datasets not tried: "1 of 250 datasets failed, 249 not tried".
- Banners: how many datasets to clear carry a risk (shared, partitioned, with no recipe), no dataset selected, tags on no dataset, and sharing not checked when the user cannot read it. The summary dataset and the JSON recap give "Sharing not checked" for each dataset to clear.
- The log gives the tags read, the options, the decision for each dataset with its reason, the result of each clear, then the totals.
- Project editors can run it (`WRITE_CONF`).

### Report Dataset Tags

- Reports how the datasets of a project use tags, and changes nothing: each tag with its category and its datasets, the datasets with no tag, unused tags of the project tag list, and unknown category tags (only checked for DSS administrators).
- "Show unused tags" and "Aggregate by tag" (one row per tag, or one row per tag and dataset) are checked by default.
- Project readers can run it (`READ_CONF`).

### Every macro

- An HTML recap: banners, figures, options, and an interactive table in DSS (sort, filters, search, CSV export, status icons). Downloaded and opened alone, it loads AG Grid Community to show the same table.
- Each run has an outcome, `SUCCESS`, `WARNING` or `FAILED`, in the log and the JSON recap. DSS cannot show a macro run as a warning: when a run goes on after a problem, a banner of the recap shows the problem.
- Every banner has the same format: a short title in bold, then what it means and what to do. A banner gives counts for what the summary dataset holds, and details only for what it cannot give, such as an error of DSS or a tag of the form. An error of DSS is cut after 200 characters; the log has the whole error.
- Banners are in the same order, by colour: blue (a simulation), red (data failed, or a real run would stop), yellow (what to check), grey (for information).
- The message of a failed run says where the details are: the summary dataset if it was written, else the run log.
- The recap as JSON, in a hidden block of the HTML and on the `RECAP_JSON` line of the log, with the fields `notices` and `problems`, and `blockers` for Clear Datasets by Tags.
- The "Summary" section: "Write to a dataset", "Summary dataset", "Append mode" (with the append mode of DSS), and "If the summary is not written": "Continue" or "Fail the run".

### For developers

- The code is in `python-lib`. The shared code (`core`, `recap`) is separate from the code of each macro (`macros/<macro>`). A test checks the import rules.
- Each macro describes its recap (`RecapPage`), and shows its own failures in a banner (`Banner`): the shared code lays it out. See [adding a macro](docs/adding-a-macro.md).
- A visibility condition of a form is `model.<checkbox>` or `model.<select list> != '<choice>'`. A test checks that the parameter and the choice exist.
- The tests are in folders: `tests/core`, `tests/recap`, `tests/macros/<macro>`, `tests/plugin`. The tests of `tests/plugin` run on each macro.
- Integration tests run the macros on a real DSS, in `tests/integration`. They are skipped without a config file: see [integration tests](docs/integration-tests.md).
- `uv build` stops with a message that gives the command that builds the plugin zip, instead of making a Python wheel that DSS cannot install.
- Checked on DSS 13.4.4: see [verification](docs/verification.md).
- Releases: the Prepare release workflow opens the pull request of a version. Merging it tags the version and publishes its GitHub release, with the plugin zip and the notes of this CHANGELOG. A dry run builds them without publishing. See [releasing](docs/releasing.md).
- A contributing guide, a security policy and a bug report form, in `.github/`.
- Commits use the GitHub noreply address of each developer: see [development](docs/development.md). `.claude/settings.json` stops Claude Code from adding attribution lines to commits and pull requests.
