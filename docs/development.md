# Development

## Set up

1. Install [uv](https://docs.astral.sh/uv/).
2. At the root of the repository, run:

```bash
uv sync
```

uv reads two files:

- `.python-version`: Python 3.9, the version of DSS 13. uv downloads it if needed.
- `uv.lock`: the exact versions of the tools, the same for everyone and for the CI.

3. Commit with your GitHub noreply address, never a personal or company address: the repository is public. Your address is on GitHub, in **Settings > Emails**. Run this once, at the root of the repository:

```bash
git config user.email "<id>+<login>@users.noreply.github.com"
```

Git uses it for your commits in this repository, and for the commits Claude Code makes for you. In **Settings > Emails**, also check "Keep my email addresses private" and "Block command line pushes that expose my email".

## Repository layout

```
.
├── plugin.json                   Id, version, name and settings of the plugin
├── python-lib/                   All the code, testable without DSS
│   ├── core/                     Shared: run a macro, read the form, read a project, tags
│   ├── recap/                    Shared: the HTML recap and the summary dataset
│   └── macros/                   The code of each macro, one folder per macro
│       ├── clear_datasets_by_tags/
│       └── report_dataset_tags/
├── python-runnables/             The macros as DSS sees them, one folder per macro
│   ├── clear-datasets-by-tags/
│   │   ├── runnable.json         The form
│   │   └── runnable.py           The entry point
│   └── report-dataset-tags/      The same two files
├── resource/
│   └── tag_choices.py            Fills the "Cat. Tags" lists of the forms
├── tests/                        pytest tests: core/, recap/ and macros/ mirror python-lib
│   ├── core/
│   ├── recap/
│   ├── macros/
│   ├── plugin/                   The plugin files of every macro, the zip, release.py
│   ├── integration/              The macros on a real DSS, skipped without a config file
│   ├── screenshots/              The README screenshots on a real DSS, skipped without --screenshots
│   └── support/                  Fake DSS objects and test helpers
├── docs/                         Documentation
│   ├── adr/                      The decisions that are hard to reverse, and why
│   ├── agents/                   For agents: the issue tracker, and the domain docs
│   ├── images/                   The screenshots of the README, a folder per macro
│   └── macros/                   The user guide and automation page of each macro
├── README.md                     For users: what the plugin does, install, settings
├── GLOSSARY.md                   The words of the plugin, and the ones to avoid
├── CODING_STANDARDS.md           The Python conventions that ruff cannot check
├── AGENTS.md                     For agents: the docs to read, the checks to run
├── CHANGELOG.md                  The changes of each version, and the unreleased ones
├── LICENSE                       MIT License
├── build_plugin_zip.py           Builds the zip to install in DSS
├── check.py                      Runs the checks of the CI
├── release.py                    Prepares a release, and writes its notes
├── pyproject.toml                Development tools and their settings
├── uv.lock                       Exact versions of the tools
├── .python-version               Python 3.9, the version DSS 13 runs
├── .claude/                      Claude Code, for everyone who uses it
│   ├── settings.json             Runs the hook after each edit
│   └── hooks/
│       └── ruff_after_edit.py    Checks with ruff each Python file that Claude Code edits
└── .github/
    ├── actions/setup/            The setup step of the workflows: checkout, uv, environment
    ├── workflows/                See releasing.md for the last three
    │   ├── ci.yml                Checks and tests on each push and pull request
    │   ├── prepare-release.yml   Opens the pull request of a release
    │   ├── tag-release.yml       Tags a merged release pull request
    │   └── release.yml           Publishes the release of a version tag
    ├── dependabot.yml            Updates the GitHub Actions, once a month
    ├── ISSUE_TEMPLATE/           The bug report form
    ├── CONTRIBUTING.md           How to contribute
    └── SECURITY.md               How to report a vulnerability
```

## Run the checks

```bash
uv run python check.py
```

It runs the checks of the CI, one after the other: ruff, ruff format, mypy, mypy for each runnable, the build of the zip, then pytest on Python 3.9 and 3.13. It prints `ok` or `FAIL` for each, the output of those that fail only, and ends in error if one fails. The command is the same in bash and PowerShell. `--no-tests` skips pytest.

Good to know:

- **One check at a time.** `check.py` lists the command of each check, such as `uv run pytest` or `uv run ruff check .`.
- **`uv run ruff format .`** fixes the format. `uv run ruff check --fix .` fixes what it can.
- **The conventions.** Ruff checks those it can, with the rules of `pyproject.toml`. [CODING_STANDARDS.md](../CODING_STANDARDS.md) gives the others.
- **mypy, one runnable at a time.** All runnables are named `runnable.py`, and mypy refuses two files with the same name in one run. This is why `check.py` runs mypy on each.
- **mypy 1.x.** mypy 2 cannot check code for Python 3.9 any more.
- **Another Python version.** `check.py` runs the tests on Python 3.13 with `uv run --isolated --locked --python 3.13 pytest`. `--isolated` leaves the environment of the project on Python 3.9.
- **Node.js.** If it is installed, a test also checks the syntax of the script of the interactive table.

## Build the zip

```bash
uv run python build_plugin_zip.py
```

The zip is in `dist/dss-plugin-clear-datasets-by-tags-<version>.zip`. It holds `plugin.json`, `README.md`, `LICENSE`, `python-lib/`, `python-runnables/` and `resource/`: the rest of the repository is for development. The command is the same in bash and PowerShell, and uv installs Python 3.9 and the tools the first time.

`uv build` does not build the plugin: it only makes Python wheels, so it stops with a message.

To try the zip, install it in DSS: **Plugins > Add plugin > Upload**.

## The tests

The tests have the same layout as `python-lib`:

| Folder | Content |
|---|---|
| `tests/support/` | Tools for the tests: fake DSS objects (`fakes.py`), a fake `dataiku` package (`dataiku_stub.py`), a helper to run a macro (`runs.py`), helpers to read a form (`forms.py`), an HTML recap (`pages.py`) and a JSON file (`files.py`), and the smallest possible macro (`sample_macro.py`). A helper that two test files need goes here. |
| `tests/core/` | The shared code of `core`: options, tags, project, runner. The runner is tested with `sample_macro.py`, without a real macro. |
| `tests/recap/` | The HTML recap, with a page made by hand, and the summary dataset. |
| `tests/macros/<macro>/` | One macro: its work, its options, its recap, its form, its `runnable.py`. |
| `tests/plugin/` | The plugin files, for **each** macro: form, `runnable.py`, import rules, zip. A new macro gets these tests with nothing to write. |
| `tests/integration/` | The macros on a real DSS. Skipped unless you give a config file: see [integration tests](integration-tests.md). |
| `tests/screenshots/` | The README screenshots, taken on the test DSS of the integration tests, with their fixtures. Skipped unless pytest gets `--screenshots`, even with a config file: running the tests never rewrites the README images. See [screenshots](screenshots.md). |

`tests/conftest.py` shares the fixtures of the integration tests with every test folder, and adds the `--screenshots` option. pytest takes pytest plugins and options only from the `conftest.py` files it loads at startup, and the one at the root of the tests is always among them.

To run only a part:

```bash
uv run pytest tests/macros/clear_datasets_by_tags
```

Two test files can have the same name in two different folders (`--import-mode=importlib` in `pyproject.toml`).

The fake objects copy the shape of the DSS answers. If a real DSS answers in another way (see [verification](verification.md) and the [integration tests](integration-tests.md)), fix the fake object and the code together.

## The CI

`.github/workflows/ci.yml` runs on each push and pull request, and when the Prepare release workflow starts it.

| Job | Steps |
|---|---|
| Lint, types and plugin zip | The setup step, then `check.py --no-tests`: ruff, ruff format, mypy, mypy for each runnable, and the build of the zip, kept as the `plugin-zip` artifact. |
| Tests on Python 3.9 and 3.13 | The setup step on that Python, then `uv run --locked pytest`. |

The setup step is the composite action `.github/actions/setup`. It checks out the repository, installs uv and runs `uv sync --locked`. A workflow calls it with `uses: $/.github/actions/setup`, which GitHub takes from the commit of the run: no checkout comes before it. Its inputs, both optional:

- `ref`: the branch, tag or commit to check out. By default, the commit of the run.
- `python`: the Python of the environment, such as `3.13`. By default, the one of `.python-version`. The uv commands after the step use it too.

Dependabot keeps the actions of the workflows and of the setup step current: once a month, it opens one pull request with every update. Its settings are in `.github/dependabot.yml`.

Three more workflows release a version: `prepare-release.yml`, `tag-release.yml` and `release.yml`. See [releasing](releasing.md).

## Change an option

Example with an option of Clear Datasets by Tags:

1. **Code:** in `macros/clear_datasets_by_tags/clearing.py`, add it to `OPTION_DEFAULTS` and `OPTION_LABELS`. The default value must be the safe side.
2. **Form:** add it to `python-runnables/clear-datasets-by-tags/runnable.json`. A test checks that the default value and the label are the same as in the code.
3. **Tests:** add it to `OPTION_PARAMS` in `tests/macros/clear_datasets_by_tags/test_form.py`, and test its effect.
4. **Docs:** the user guide of the macro, its automation page, and the CHANGELOG.

The options of the "Summary" section are the same for all macros, and the "Run" section is the same for all macros that change data: they are in `core/options.py`.

## Do not rename

- **The plugin id** (`clear-datasets-by-tags` in `plugin.json`): it is part of the id of each macro and of the name of the zip. If it changes, scenarios and API calls break, and DSS sees another plugin.
- **The id of a macro** (the name of its folder): scenarios and the API use it, for example `pyrunnable_clear-datasets-by-tags_clear-datasets-by-tags`.

## Release a version

See [releasing](releasing.md). In short: write the changes under `## Unreleased` in the [CHANGELOG](../CHANGELOG.md), run the Prepare release workflow, test the zip of the release pull request on a DSS, and merge it. The workflows set the version, tag it and publish the release with the zip.
