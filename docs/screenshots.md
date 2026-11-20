# Screenshots

The README shows each macro with screenshots taken in DSS. The tests of `tests/screenshots` take them again on the test DSS of the [integration tests](integration-tests.md), so that they show the plugin of your folder. A run of these tests is a refresh.

Today they do two things:

- **The demo projects** (`test_demo_projects.py`): they create the projects `SALES` and `FINANCE` from code, run both macros on `SALES` through the API, and check that the recaps give the results the README states.
- **One image** (`test_report_dataset_tags.py`): the form of the Report Dataset Tags macro, with its default values, `docs/images/report-dataset-tags/form.png`. The other three images are still taken by hand.

## What you need

- **The test DSS and the config file of the [integration tests](integration-tests.md)**, with the API key of a DSS administrator.
- **The tag categories of the README on the DSS:** a tag category `Stage`, with the tags `Raw`, `Prepared` and `Output`, and no tag category `Owner`. They apply to the whole DSS, and only a DSS administrator changes them, in **Administration > Settings > Global tag categories** ([tags](https://doc.dataiku.com/dss/13/collaboration/tags.html)). The tests never change them: they stop, and say what to change.
- **No project `SALES` or `FINANCE` of your own on the DSS:** the tests stop rather than touch it.
- **The UI login in the config file:** `ui_login` and `ui_password`, the login and the password of the owner of the test projects, `project_owner`, such as `admin`. API keys cannot open a session in the DSS UI, so the tests log in through the `/login/` form, as a user does. It also works when DSS uses SSO, for a user with a password.
- **The `screenshots` dependency group:** Playwright and Pillow. `uv run --group screenshots` installs them.
- **The Chromium of Playwright**, downloaded once, in the cache of Playwright:

```bash
uv run --group screenshots playwright install chromium
```

## Run them

In bash:

```bash
DSS_INTEGRATION_CONFIG=~/dss-integration.json uv run --group integration --group screenshots pytest tests/screenshots --screenshots
```

In PowerShell:

```powershell
$env:DSS_INTEGRATION_CONFIG = "$HOME\dss-integration.json"; uv run --group integration --group screenshots pytest tests/screenshots --screenshots
```

Without `--screenshots`, the tests are skipped, even when `DSS_INTEGRATION_CONFIG` is set: running the tests never rewrites the README images. With it, they are skipped without a config file or without the dependency groups: add `-rs` to see why.

A config file with no UI login, or a login that DSS refuses, stops the tests with the field to add or to fix.

## What they do on the DSS

First, before any change:

1. Read the tag categories of DSS. When they do not give the recap of the README, stop all the tests, with the changes a DSS administrator must make.
2. Read the keys of the projects. A project `SALES` or `FINANCE` that a refresh did not make stops all the tests: a refresh never touches it.
3. Install the zip of your folder, or check the version of the plugin on the DSS, as the integration tests do.

The demo projects:

1. Delete the demo projects left by a refresh that crashed.
2. Create `SALES` and `FINANCE`, and mark each one with the project variable `readme_demo_project`, at once. A refresh only deletes a project with this mark.
3. Run the Clear Datasets by Tags macro, a simulation that clears nothing, and the Report Dataset Tags macro on `SALES`, through the API. When a result differs from the README, the test fails, with the expected and the actual values.
4. Delete `FINANCE`, then `SALES`, also when a step fails.

They also check the guard on scratch projects, `DSSPM_IT_<random>`, which stand for a project with a demo key.

The image:

1. Start Chromium and log in to the DSS UI with the UI login.
2. Create a scratch project, `DSSPM_IT_<random>`. It is deleted at the end, also when a test fails.
3. Open the Macros page of the scratch project, then the macro, and reset its form to its default values.
4. Take a screenshot of the dialog of the macro, and write it in place of the README image.

They change no instance-wide setting, and create no user and no API key.

## The demo projects

`tests/screenshots/demo_projects.py` describes them, with the results the README states, in `EXPECTED_CLEAR` and `EXPECTED_REPORT`:

| Dataset of `SALES` | Tags | What it shows |
|---|---|---|
| `country_lookup` | `temporary`, `Owner:Finance` | A dataset to clear, shared with `FINANCE`: a risk. An unknown tag: DSS has no tag category `Owner`. |
| `orders_prepared`, `raw_customers`, `raw_orders` | `temporary`, and `Stage:Prepared` or `Stage:Raw` | Datasets to clear. |
| `crm_extract` | `temporary`, `Stage:Raw` | A skipped dataset: external, an uploaded dataset. |
| `manual_targets` | `temporary` | A skipped dataset: with no recipe. |
| `web_logs` | `temporary` | A skipped dataset: partitioned by day and country. |
| `orders_by_month` | `temporary`, `keep`, `Stage:Ouput` | An excluded dataset. An unknown tag: a typo of `Output`. |
| `sales_report` | `Stage:Output` | Not selected. Its recipe has the tag `archive`, which is on no dataset: the unused tag. |
| `orders_upload` | `Stage:Raw` | Not selected. |
| `customers_upload` | none | The untagged dataset. |

`FINANCE` builds a dataset from the shared `country_lookup`.

### Change the expected results

When a change of the plugin changes a recap on purpose:

1. Run the tests: they stop, and list each result that differs, expected and actual.
2. In the same commit, change `EXPECTED_CLEAR` or `EXPECTED_REPORT`, and the README captions and alt texts that state these results.
3. Run the tests again.

To show a new case in the recaps, add a dataset to `SALES_DATASETS`, and a row to the table above. A shared dataset or a tag on a recipe needs more: see `SHARED_DATASET` and `UNUSED_TAG` in the same module. Then change the expected results and the README captions in the same way.

## The images

- **Only the dialog**, at scale 2 (the device scale factor), in English and in the light theme of the browser. The window is tall enough to show the whole dialog without scrolling.
- **A frame of one pixel** in the colour of the borders of GitHub, `#d0d7de`, so that the white dialog stands out on the white page of the README. The images taken by hand have the same frame.
- **A palette of 256 colours**, so that each refresh adds a small file to the history of the repository.

Look at the new image before you commit it: `git diff` only says that it changed.

## When the DSS UI changes

Every detail of the DSS UI that the Dataiku docs do not give is in `tests/screenshots/dss_ui.py`: the labels of the login form, the link to the Macros page, the buttons of the dialog of a macro, the size of the window. They were read on DSS 13.4.4. The tests find fields and buttons by their visible English labels and their roles, never by CSS classes. When a DSS upgrade breaks a screenshot test, fix that module.

The Python of the repository is 3.9, the version of DSS 13. Playwright 1.61 and Pillow 12 need Python 3.10, and greenlet 3.2.5, which Playwright needs, has no wheel for Python 3.9 on Windows: `pyproject.toml` keeps the versions before them. The lock file then has one version of Playwright, and so one Chromium, until someone changes it.
