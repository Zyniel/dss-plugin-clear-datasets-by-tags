# Changelog

The changes of each version of the plugin, the most recent first. The changes not released yet are under **Unreleased**.

## Unreleased

### Clear Datasets by Tags

- With "All datasets", an excluded tag that no dataset has now stops a real run, before anything is cleared, and a simulation shows it in a red banner. The excluded tags are then the only protection: a typo such as `kep` for `keep` used to clear every dataset, with only a yellow notice. Fix the tag, or remove it to clear every dataset. **A scenario that runs the macro with such a tag now ends in error.** "All datasets" with no excluded tag still clears every dataset, and with "Datasets with the included tags", a tag on no dataset is still only a notice.

### For developers

- `GLOSSARY.md` gives the words of the plugin, such as tag rules, protection, foreign dataset and blocked run. `docs/adr/` records the decisions that are hard to reverse, starting with why "Clear shared datasets" is checked by default. The docs and the code use these words: `RunStopped` is now `RunBlocked`, `TagSelection` is `TagRules`, `recap_columns` is `summary_columns`, and `cleanup.py` is `clearing.py`. The parameters of the forms, the JSON recap and the summary dataset do not change.

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
- Banners: how many datasets to clear carry a risk (shared, partitioned, with no recipe), no dataset selected, tags on no dataset, and sharing not checked when the user cannot read it. The summary dataset and the JSON recap give "Sharing not checked" for each dataset.
- The log gives the tags read, the options, the decision for each dataset with its reason, the result of each clear, then the totals.
- Project editors can run it (`WRITE_CONF`).

### Report Dataset Tags

- Reports how the datasets of a project use tags, and changes nothing: each tag with its category and its datasets, the datasets with no tag, unused tags of the project tag list, and unknown category tags (only checked for DSS administrators).
- "Show unused tags" and "Aggregate by tag" (one row per tag, or one row per tag and dataset) are checked by default.
- Project readers can run it (`READ_CONF`).

### Every macro

- An HTML recap: banners, figures, options, and an interactive table in DSS (sort, filters, search, CSV export, status icons). Downloaded and opened alone, it loads AG Grid Community to show the same table.
- Each run has an outcome, `SUCCESS`, `WARNING` or `FAILED`, shown in a banner at the top of the recap. DSS cannot show a macro run as a warning.
- Every banner has the same format: a short title in bold, then what it means and what to do. A banner gives counts for what the summary dataset holds, and details only for what it cannot give, such as an error of DSS or a tag of the form. An error of DSS is cut after 200 characters; the log has the whole error.
- Banners are in the same order, by colour: blue (a simulation), red (data failed, or a real run would stop), yellow (what to check), grey (for information).
- The message of a failed run says where the details are: the summary dataset if it was written, else the run log.
- The recap as JSON, in a hidden block of the HTML and on the `RECAP_JSON` line of the log, with the fields `notices`, `blockers` and `problems`.
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
