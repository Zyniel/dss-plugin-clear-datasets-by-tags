# Screenshots

The README shows each macro with screenshots taken in DSS. The tests of `tests/screenshots` take them again on the test DSS of the [integration tests](integration-tests.md), so that they show the plugin of your folder.

Today they take one image: the form of the Report Dataset Tags macro, with its default values, `docs/images/report-dataset-tags/form.png`. The other three images are still taken by hand.

## What you need

- **The test DSS and the config file of the [integration tests](integration-tests.md)**, with the API key of a DSS administrator.
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

## What they do

1. Install the zip of your folder, or check the version of the plugin on the DSS, as the integration tests do.
2. Start Chromium and log in to the DSS UI with the UI login.
3. Create a scratch project, `DSSPM_IT_<random>`. It is deleted at the end, also when a test fails.
4. Open the Macros page of the scratch project, then the macro, and reset its form to its default values.
5. Take a screenshot of the dialog of the macro, and write it in place of the README image.

They change no instance-wide setting, and create no user and no API key.

## The images

- **Only the dialog**, at scale 2 (the device scale factor), in English and in the light theme of the browser. The window is tall enough to show the whole dialog without scrolling.
- **A frame of one pixel** in the colour of the borders of GitHub, `#d0d7de`, so that the white dialog stands out on the white page of the README. The images taken by hand have the same frame.
- **A palette of 256 colours**, so that each refresh adds a small file to the history of the repository.

Look at the new image before you commit it: `git diff` only says that it changed.

## When the DSS UI changes

Every detail of the DSS UI that the Dataiku docs do not give is in `tests/screenshots/dss_ui.py`: the labels of the login form, the link to the Macros page, the buttons of the dialog of a macro, the size of the window. They were read on DSS 13.4.4. The tests find fields and buttons by their visible English labels and their roles, never by CSS classes. When a DSS upgrade breaks a screenshot test, fix that module.

The Python of the repository is 3.9, the version of DSS 13. Playwright 1.61 and Pillow 12 need Python 3.10, and greenlet 3.2.5, which Playwright needs, has no wheel for Python 3.9 on Windows: `pyproject.toml` keeps the versions before them. The lock file then has one version of Playwright, and so one Chromium, until someone changes it.
