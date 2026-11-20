# Integration tests

Tests that run the macros on a real DSS, in `tests/integration`. The other tests use fake DSS objects: only a real DSS shows how DSS really answers.

## What they check

| File | Tests | Rows of [verification](verification.md) |
|---|---|---|
| `test_clear_datasets_by_tags.py` | A simulation clears nothing. A real run clears only the datasets that match the tag rules. An uploaded dataset is never cleared. "All datasets" clears every managed dataset except the excluded ones. Excluded tags alone are refused. | 9, 10, 11, 28 |
| `test_summary_dataset.py` | "Append mode" keeps the earlier runs. "Fail the run" fails the step of a scenario, "Continue" does not. | 15, 25 |
| `test_permissions.py` | An editor sees both macros, clears without reading the sharing, and cannot skip shared datasets. A reader sees only the Report Dataset Tags macro, cannot clear data, and runs it without the tag categories of the instance. | 8, 13, 22, 24 |

## What you need

- **A test DSS 13**, never a production DSS: the tests create and delete projects, and can replace the plugin.
- **A DSS license.** Without one, the API still runs the macros as an administrator, but the tests of the editor, of the reader and of scenarios fail: users have no profile, and scenarios cannot run a macro.
- **The API key of a DSS administrator:** a global API key with the admin right, or the personal API key of an administrator.
- **For `test_permissions.py`:** the personal API keys of two users who are not DSS administrators, an editor and a reader. Without them, these tests are skipped. Prefer existing users: a test user can take a licence seat.

## The config file

It holds API keys: never commit it. Put it outside the repository, or at its root as `dss-integration.json`, which git ignores.

```json
{
  "url": "http://127.0.0.1:10000",
  "project_owner": "admin",
  "install_plugin": true,
  "api_keys": {
    "admin": "<API key of a DSS administrator>",
    "editor": "<personal API key of the editor>",
    "reader": "<personal API key of the reader>"
  }
}
```

| Field | Use |
|---|---|
| `url` | The DSS. |
| `project_owner` | The login of the owner of the test projects, such as `admin`. A global API key is not a user, so the tests need it. |
| `install_plugin` | `true`: the tests build the zip of your folder and install it on the DSS first. It replaces the plugin for every user of this DSS. `false` (default): the tests only check that the DSS has the version of `plugin.json`. |
| `api_keys` | `admin` is required. `editor` and `reader` are optional. |
| `managed_connection` | Optional: the connection of the managed datasets of the tests. Default: `filesystem_managed`. |

## Run them

In bash:

```bash
DSS_INTEGRATION_CONFIG=~/dss-integration.json uv run --group integration pytest tests/integration
```

In PowerShell:

```powershell
$env:DSS_INTEGRATION_CONFIG = "$HOME\dss-integration.json"; uv run --group integration pytest tests/integration
```

Without `DSS_INTEGRATION_CONFIG`, the tests are skipped: `uv run pytest` and the CI never need a DSS.

## What they do on the DSS

- Each test creates its own project, `DSSPM_IT_<random>`, and deletes it at the end, also when the test fails. They never touch another project.
- They give the editor and the reader access to these projects only.
- They create no user and no API key. Delete the API keys you created for the tests when you are done.

## Fixtures and helpers

The fixtures are in `tests/integration/fixtures.py`. `tests/conftest.py` registers them for every test folder: the screenshot tests of `tests/screenshots` use them too, and only run when pytest gets `--screenshots`.

| Fixture | Gives |
|---|---|
| `config` | The config file. Skips the test without `DSS_INTEGRATION_CONFIG`, or without the `integration` group. |
| `admin` | The client of the DSS administrator. Skips the test without its API key. Once a session, it installs the zip of your folder when `install_plugin` is `true`, then checks that the DSS has the version of `plugin.json`. |
| `editor`, `reader` | The clients of the editor and the reader. Skip the test without their API key, and stop it with an error when the user is a DSS administrator. |
| `connection` | The connection of the managed datasets: `managed_connection`, or `filesystem_managed`. |
| `scratch_project` | A new, empty project, `DSSPM_IT_<random>`, owned by `project_owner`. Deleted at the end of the test, also when it fails. The delete refuses any key without the `DSSPM_IT_` prefix. |

The helpers are in `tests/integration/dss.py`. They fill a scratch project (`add_built_dataset`, `add_uploaded_dataset`, `add_empty_dataset`, `set_tags`, `add_macro_scenario`), run a macro and read its JSON recap (`run_macro`, `row_of`), and check what the run did (`count_rows`, `list_macro_ids`, `dss_error`). `give_access` gives the editor or the reader access to a scratch project. `CLEAR` and `REPORT` are the ids of the macros, `ROW_COUNT` the rows of each test dataset, and `PROJECT_PREFIX` the prefix of the scratch projects.

## Add a test

1. Pick a row of [verification](verification.md) that is still to do.
2. Write the test in `tests/integration`, with the [fixtures and helpers](#fixtures-and-helpers).
3. Run it on a test DSS, then write the result and the date in the row.
