# Verification

What the tests prove, and what to check on a real DSS.

## What is proven

| What | How |
|---|---|
| The shared code and each macro | 395 tests with fake DSS objects, on Python 3.9 and 3.13. |
| The forms match the code, `runnable.py` loads, the import rules are respected | Tests of `tests/plugin`, for each macro. |
| The DSS API calls exist, with the expected shape | Read in the code of the public API client, `dataiku-api-client` 15.2.1. |
| The plugin works on a real DSS | Run on a local DSS 13.4.4 container: see the checks below. Some checks are also [integration tests](integration-tests.md), which a test DSS can run again. |

The fake objects copy what the code expects from DSS. Only a real DSS shows if it really answers that way.

## What the Dataiku docs say

What the plugin relies on, as the Dataiku docs say it, read on 2026-11-20. The "latest" pages are DSS 15. On these points, the [DSS 13 macro page](https://doc.dataiku.com/dss/13/plugins/reference/macros.html) says the same. Read this before searching the docs, and add what you look up, with its link.

| Fact | Source |
|---|---|
| A macro gives an HTML, URL or RESULT_TABLE result. An HTML result shows inline in DSS, and its CSS must be scoped. | [Result of a macro](https://doc.dataiku.com/dss/latest/plugins/reference/macros.html#result-of-a-macro) |
| `run()` "can return a string or raise an exception". Nothing else is documented: no warning, no partial success, no outcome for a macro run. The WARNING outcome of the plugin and its banners are the plugin's own. | [Macro execution](https://developer.dataiku.com/latest/tutorials/plugins/macros/generality/index.html#macro-execution) |
| `get_progress_target()` returns `(target, unit)`, with the unit `NONE` for a percentage, then `run()` calls `progress_callback(current)`. `"impersonate": true` is recommended. | [Progress reporting](https://doc.dataiku.com/dss/latest/plugins/reference/macros.html#progress-reporting) |
| The steps of a scenario run in order, "until one fails". Some steps can treat errors as warnings: the page does not say whether the "Run a macro" step is one of them. A step ends in SUCCESS, WARNING, FAILED or ABORTED. | [Step flow control](https://doc.dataiku.com/dss/latest/scenarios/step_flow_control.html) |
| `DSSMacro.run()` returns a run id. `get_result()` raises while the macro runs, and the run "ceases to exist" after it. The docs say `as_type="string"` returns a `str`: it returns bytes (row 17). | [DSSMacro](https://developer.dataiku.com/latest/api-reference/python/macros.html) |
| `run_and_wait()` raises when a scenario run does not end in SUCCESS: a WARNING run raises too. | [DSSStepRunDetails](https://developer.dataiku.com/latest/api-reference/python/scenarios.html#dataikuapi.dss.scenario.DSSStepRunDetails) |
| A plugin validates its parameters, and keeps its logic in its libraries, without importing `dataiku`. | [Best practices](https://developer.dataiku.com/latest/tutorials/plugins/setup-a-dev-env/index.html#best-practices) |
| The version of a plugin, in its `plugin.json`: semantic versioning is "highly recommended", in a comment of the example `plugin.json`. Nothing else is said of its form. The release process accepts semantic versions with one pre-release form: `X.Y.Z` or `X.Y.Z-beta`. Read on 2026-11-22: the DSS 13 page says the same. | [Structure of a plugin](https://doc.dataiku.com/dss/latest/plugins/reference/plugins-components.html#structure-of-a-plugin) |
| An administrator installs a plugin from the store, from its zip (**Add plugin > Upload**), or from a Git repository (**Add plugin > Fetch from Git repository**). The page lets you choose only the branch for Git. The API checks out a branch, a tag or a commit: its `checkout` is a "branch/tag/SHA1", in the API reference of DSS 15 and in the code of `dataiku-api-client` 13.5.6. Read on 2026-11-22: the DSS 13 page says the same. | [Installing plugins](https://doc.dataiku.com/dss/latest/plugins/installing.html#installing-plugins), [`install_plugin_from_git()`](https://developer.dataiku.com/latest/api-reference/python/client.html#dataikuapi.DSSClient.install_plugin_from_git) |

Not documented, so only the checks below show it: what DSS shows when `run()` raises, and how it turns a "Run a macro" step red (rows 18 and 25); whether the scripts of an HTML result run, and whether DSS filters it (rows 4 and 6); the log of a macro, and when DSS stops reading it (row 7). The [logging page](https://doc.dataiku.com/dss/latest/operations/logging.html) lists no macro log.

## Check on DSS 13

Use an instance with a license, for example a local DSS 13.4.4 container, and follow these rules:

- **Test projects only:** create test projects, never touch existing projects.
- **Licenses:** a test user can take a license seat. Prefer existing users.
- **Clean up:** at the end, delete the test projects, the test users and the API keys.

Without a license, DSS 13.4.4 runs the macros from the API with the key of an administrator, but its UI, the users who are not administrators and the scenario steps that run a macro do not work (2026-11-06).

For each check, write the result and the date. If DSS answers in another way, fix the code and the fake objects of `tests/support/fakes.py` together.

### The plugin

| # | Check | What the code expects | Result |
|---|---|---|---|
| 1 | Python version of the built-in environment | 3.9 | OK: 3.9.20, with pandas 2.2.3. |
| 2 | Install the zip of `uv run python build_plugin_zip.py` | The plugin installs with its default settings. | OK, 13.4.4, 2026-11-03. |
| 3 | The Macros page of a project | The macros are in the "Project maintenance" section (`meta.category`). | OK, 13.4.4, 2026-11-03. Without `meta.category`, DSS uses the plugin id as the section name. |
| 4 | The interactive table of the recap in DSS | `window.agGrid` exists in the page, and the scripts of the HTML of a macro run. | OK, 13.4.4, 2026-11-03: the grid replaces the simple table, with columns, icons and chips. "Duration (s)" is aligned on the right. No message in the console. |
| 5 | A recap opened alone, outside DSS | It loads AG Grid Community 29.2.0 from the URL of the settings, with the hash, and never inside DSS. | OK, 2026-11-03: a recap served as a page alone loads AG Grid from jsDelivr with its hash, and shows the interactive table. |
| 6 | The HTML of the recap in DSS | DSS shows the HTML without filtering it: a `{{...}}` or `<b>` in a tag must stay text. | OK, 13.4.4, 2026-11-03: the tag `<b>bold</b>{{7*7}}` shows as text. |
| 7 | The `RECAP_JSON` line of the log, for a run from the UI | It is the last line of the macro. | Lost once: DSS stops reading the log as soon as the macro returns. OK since the macro waits half a second. |
| 8 | `"permissions": ["WRITE_CONF"]` | Users who can write in the project see the macro. Other users do not. | OK, 13.4.4, 2026-11-20, integration tests: an editor sees both macros, a reader sees only Report Dataset Tags and cannot clear data. |

### Clear Datasets by Tags

| # | Check | What the code expects | Result |
|---|---|---|---|
| 9 | A simulation, then a real run, from the API | The figures, the JSON block and the summary dataset are correct. | OK, 13.4.4, 2026-11-03: 2 cleared, 1 excluded, 3 rows in the summary dataset. |
| 10 | The fields of `list_datasets()` for a managed, editable, uploaded, external and partitioned dataset | `managed`, `partitioning.dimensions`, `tags` and `params.connection` are present. | Managed dataset built by a recipe: OK. Uploaded dataset: `managed` is false, so the macro skips it as external and never clears it (OK, 13.4.4, 2026-11-05, integration test). Editable, external and partitioned: to do. |
| 11 | The answer of `clear()` after a success, then after a failure | A failure sets `error` or `fatal`. `success` can be false after a success. | Success: OK, also an integration test (2026-11-05): after a clear, the dataset has no data. Failure: to do. |
| 12 | `get_flow().get_graph().get_source_computables()` | Datasets with no recipe are `COMPUTABLE_DATASET` nodes, with their name in `ref`. | OK. |
| 13 | Who can read `get_settings()`, which contains the sharing | Project admin and instance admin: yes. Simple editor: no. | Instance admin: OK. Simple editor: OK, 13.4.4, 2026-11-20, integration tests: the run clears with "Sharing not checked", and a run that skips shared datasets is refused. |
| 14 | The value of a `DATASET` parameter | The dataset name, or `PROJECTKEY.name`. | OK. |
| 15 | Write the summary dataset from a macro | `dataiku.Dataset(name, project_key=..., ignore_flow=True)` supports `read_schema`, `write_schema` and `get_writer`, and `spec_item["appendMode"] = True` makes the writer append. | Written with its schema, from the API and the UI. Append mode OK, 13.4.4, 2026-11-04: two runs gave 7 then 14 rows from two runs, and a run with "Append mode" unchecked replaced them with 7 rows. Also an integration test, OK 2026-11-05. Two runs at the same time: not checked. |
| 16 | "Write to a dataset" checked, a dataset picked, then unchecked | "Summary dataset" and "Append mode" are hidden, and nothing is written. | OK. |
| 17 | `macro.get_result(run_id, as_type="string")` | It can return bytes. The JSON of `<script id="dtp-recap-data">` can be read. | OK: bytes, and the JSON can be read. |
| 18 | "If an error occurs" set to "Continue, run ends in error" or "Raise exception", in a scenario | DSS shows the error message, and the scenario step turns red. "Raise exception" stops at the first dataset that cannot be cleared. | To do. |
| 19 | The "Cat. Tags" lists | `resource/tag_choices.py` imports from `python-lib`, and `dataiku.default_project_key()` gives the project of the form. | OK as instance admin. DSS shows them as a tag input, without the groups. Simple editor: to do. |
| 20 | A category tag picked only in "Included Cat. Tags" | The form sends nothing in "Excluded Cat. Tags". | OK. |
| 28 | "Include" set to "All datasets" | The three included fields are hidden, and their values are still sent. A remembered form with no value for "Include" gets "Datasets with the included tags". A run clears every managed dataset except the excluded ones. Excluded tags alone are refused. | Run from the API: OK, 13.4.4, 2026-11-06, integration tests. Form: read in the DSS 13.4.4 frontend, 2026-11-06: `visibilityCondition` works the same for every parameter type and hides with `ng-show`, so the value stays in the sent config; a parameter missing from the remembered values gets its `defaultValue`. The expression, run with the AngularJS 1.9.1 of DSS: shown with `TAGS` or no value, hidden with `ALL_DATASETS`. Seen in the UI: to do, on a DSS with a license. |
| 29 | A run with no selected dataset, "Append mode" unchecked | The writer is opened and closed with no row: DSS replaces the data with nothing, and the summary dataset is empty. The Dataiku docs say a write without `appendMode` empties the dataset and fills it again, not what a write with no row does. | To do. |
| 30 | A real run that a check blocks, in a scenario | The step turns red with the message of the run, and the "Last runs" of the scenario keep it. No row is written, and the log has no `RECAP_JSON` line. | To do: needs a DSS with a license, and a user who is not a project administrator. |

### Report Dataset Tags

| # | Check | What the code expects | Result |
|---|---|---|---|
| 21 | `project.get_tags()` | `{"tags": {<tag>: {...}}}`. DSS adds a tag to the list when an object gets it, and keeps it after. | OK, 13.4.4, 2026-11-03. |
| 22 | The global tag categories | In the general settings, `globalTagsCategories`: a list of `{"name", "globalTags": [{"name", "color"}], "appliesTo"}`. Only DSS administrators can read them. | Shape OK, 13.4.4, 2026-11-03. A user who is not a DSS administrator: OK, 13.4.4, 2026-11-20, integration test: a reader runs Report Dataset Tags without them. |
| 23 | A run from the API and from the UI | The figures, the table (problems first), the figure filters and the summary dataset are correct, with "Aggregate by tag" checked and unchecked. | OK, 13.4.4, 2026-11-03: 2 unknown tags, 1 unused tag, 3 datasets with no tag, 8 rows in the summary dataset. Checked: 6 rows, dataset names as text. Unchecked: 8 rows, one per tag and dataset. No message in the console. |
| 24 | `"permissions": ["READ_CONF"]` | A user who can only read the project sees and runs the macro. | OK, 13.4.4, 2026-11-20, integration tests. |
| 25 | "If the summary is not written" with a summary dataset that cannot be written | "Continue": the run succeeds, with the outcome WARNING and a yellow banner. "Fail the run": the run fails with the message. "If an error occurs" does not cover it. | OK, 13.4.4, 2026-11-04, from the API, with Report Dataset Tags and Clear Datasets by Tags. Both select lists show in the forms with "Continue" and "Fail the run". In a scenario, OK 2026-11-05 (integration test): "Fail the run" fails the step, "Continue" does not. |
| 26 | The form after a plugin update | It shows the defaults of `runnable.json`. | DSS remembers the values of the last run in the local storage of the browser, under the key `<project key>.<macro id>`: one entry per project and per browser. "Clear shared datasets" stayed unchecked after a plugin update that checked it by default, in a test project recreated with the same key. "Reset to default" shows the new defaults. Read in the DSS 13.4.4 frontend (`runnables.js`), 2026-11-04. |
| 27 | The plugin setting "Tag categories" | Set to `Stage`, the "Cat. Tags" lists offer only the tags of that category. Empty: all categories. | OK, 13.4.4, 2026-11-04: the setting shows under "Tag lists" in the plugin settings, and the lists offered only the tags of the chosen category, not those of the other categories. |

## Not covered yet

These datasets are cleared like the others. They could get their own option, once checked on a real DSS:

- **Write-protected datasets:** the rebuild behavior of a dataset can be "write-protected".
- **Append outputs:** outputs of recipes that append instead of overwrite. Clearing them loses their history, even if a recipe builds them.
