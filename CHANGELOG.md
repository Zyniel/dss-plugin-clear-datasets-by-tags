# Changelog

The changes of each version of the plugin, the most recent first. The changes not released yet are under **Unreleased**.

## Unreleased

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
- The guide to the integration tests says when to run them: before a pull request that changes the code DSS runs. Coding agents run them too, on the test DSS of the config file.

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
