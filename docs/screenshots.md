# Screenshots

The README shows each macro with two screenshots taken in DSS: its form, and the recap of a run. The tests of `tests/screenshots` take all four again on the test DSS of the [integration tests](integration-tests.md), on demo projects they create from code, so that they show the plugin of your folder. A run of these tests is a refresh.

## What you need

- **The test DSS and the config file of the [integration tests](integration-tests.md)**, with the API key of a DSS administrator.
- **The tag categories of the README on the DSS:** a tag category `Stage`, with the tags `Raw`, `Prepared` and `Output`, and no tag category `Owner`. They apply to the whole DSS, and only a DSS administrator changes them, in **Administration > Settings > Global tag categories** ([tags](https://doc.dataiku.com/dss/13/collaboration/tags.html)). A refresh never changes them: it stops, and says what to change.
- **No project `SALES` or `FINANCE` of your own on the DSS:** a refresh stops rather than touch it.
- **The UI login in the config file:** `ui_login` and `ui_password`, the login and the password of the owner of the test projects, `project_owner`, such as `admin`. API keys cannot open a session in the DSS UI, so a refresh logs in through the `/login/` form, as a user does. It also works when DSS uses SSO, for a user with a password. The macros run in the UI as this user: with `admin`, the recaps say "Run by admin".
- **The `screenshots` dependency group:** Playwright and Pillow. `uv run --group screenshots` installs them.
- **The Chromium of Playwright**, downloaded once, in the cache of Playwright:

```bash
uv run --group screenshots playwright install chromium
```

## Run a refresh

In bash:

```bash
DSS_INTEGRATION_CONFIG=~/dss-integration.json uv run --group integration --group screenshots pytest tests/screenshots --screenshots
```

In PowerShell:

```powershell
$env:DSS_INTEGRATION_CONFIG = "$HOME\dss-integration.json"; uv run --group integration --group screenshots pytest tests/screenshots --screenshots
```

Without `--screenshots`, the tests are skipped, even when `DSS_INTEGRATION_CONFIG` is set: running the tests never rewrites the README images. With it, they are skipped without a config file or without the dependency groups: add `-rs` to see why.

A config file with no UI login, or a login that DSS refuses, stops the refresh with the field to add or to fix.

## What a refresh does on the DSS

1. Read the tag categories of DSS. When they do not give the recap of the README, stop, with the changes a DSS administrator must make.
2. Read the keys of the projects. A project `SALES` or `FINANCE` that a refresh did not make stops it: a refresh never touches it.
3. Start Chromium, and install the zip of your folder, or check the version of the plugin on the DSS, as the integration tests do.
4. Delete the demo projects left by a refresh that crashed, then create `SALES` and `FINANCE`. Each one is marked at once with the project variable `readme_demo_project`: a refresh only deletes a project with this mark.
5. Run the Clear Datasets by Tags macro, a simulation that clears nothing, and the Report Dataset Tags macro on `SALES`, through the API. When a result differs from the README, stop, with the expected and the actual values: no browser step runs, and no image changes.
6. Log in to the DSS UI. For each macro: open it on the Macros page of `SALES`, reset its form to its default values, fill it with the values of the API run, take a screenshot of the form, run the macro, and take a screenshot of the recap of that run.
7. Check the runs in the UI: their recaps give the results the README states, and say "Run by" the UI login. Check each image: it shows only the dialog, with no line of the page behind it inside the frame.
8. Write the four images in place of the old ones, once all four are taken and checked. A failure before leaves the old images as they were.
9. Delete `FINANCE`, then `SALES`, also when a step fails.

The first two steps stop all the screenshot tests, before any change. A refresh changes no instance-wide setting, and creates no user and no API key. It also checks its guard on scratch projects, `DSSPM_IT_<random>`, which stand for a project with a demo key.

## The demo projects

`tests/screenshots/demo_projects.py` describes them. It also holds the forms of the runs, as the README describes them, and the results the README states, in `EXPECTED_CLEAR` and `EXPECTED_REPORT`:

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

The forms: the Clear Datasets by Tags macro with the included tag `temporary`, the excluded tag `keep`, and "Simulate" checked. The Report Dataset Tags macro with its default values. The run in the UI resets the form to its default values, then fills it with the same values as the API run.

### Change the expected results

When a change of the plugin changes a recap on purpose:

1. Run a refresh: it stops, and lists each result that differs, expected and actual.
2. In the same commit, change `EXPECTED_CLEAR` or `EXPECTED_REPORT`, and the README captions and alt texts that state these results.
3. Run a refresh again, and commit the four images with them.

To show a new case in the recaps, add a dataset to `SALES_DATASETS`, and a row to the table above. A shared dataset or a tag on a recipe needs more: see `SHARED_DATASET` and `UNUSED_TAG` in the same module. Then change the expected results and the README captions in the same way. To add a macro, see [adding a macro](adding-a-macro.md).

## The images

- **The whole dialog, and only the dialog**, at scale 2 (the device scale factor), in English and in the light theme of the browser. DSS caps the body of a dialog at 500 pixels and scrolls the rest, whatever the size of the window: a refresh lifts this cap, so that the whole form and the whole recap show. Inside the recap, a table keeps its own scroll.
- **The width DSS gives the dialog:** 900 pixels, as a DSS user sees it. A table of a recap that is wider scrolls sideways in DSS, and is cut on the right in the image.
- **The real start time, duration and "Run by"** of each run in the UI: every refresh changes both recap images.
- **A frame of one pixel** in the colour of the borders of GitHub, `#d0d7de`, so that the white dialog stands out on the white page of the README. The images taken by hand had the same frame.
- **A palette of 256 colours**, so that each refresh adds small files to the history of the repository.

Look at the new images before you commit them: `git diff` only says that they changed. Then check that the README captions and alt texts still say what they show.

## When the DSS UI changes

Every detail of the DSS UI that the Dataiku docs do not give is in `tests/screenshots/dss_ui.py`: the labels of the login form, the link to the Macros page, the dialog of a macro (its place, its buttons, its list fields, its body that scrolls, its width), the time a run takes, the size of the window. It fills only the fields of type `STRINGS` and `BOOLEAN`: the forms of the README need no other. They were read on DSS 13.4.4. A refresh finds fields and buttons by their visible English labels and their roles, never by CSS classes. When a DSS upgrade breaks a refresh, fix that module.

The Python of the repository is 3.9, the version of DSS 13. Playwright 1.61 and Pillow 12 need Python 3.10, and greenlet 3.2.5, which Playwright needs, has no wheel for Python 3.9 on Windows: `pyproject.toml` keeps the versions before them. The lock file then has one version of Playwright, and so one Chromium, until someone changes it.
