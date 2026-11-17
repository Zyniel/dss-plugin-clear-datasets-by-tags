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
├── plugin.json                Id, version, name and settings of the plugin
├── python-lib/                All the code, testable without DSS
│   ├── core/                  Shared: run a macro, read the form, read a project, tags
│   ├── recap/                 Shared: the HTML recap and the summary dataset
│   └── macros/                The code of each macro, one folder per macro
│       ├── clear_datasets_by_tags/
│       └── report_dataset_tags/
├── python-runnables/          The macros as DSS sees them, one folder per macro
│   ├── clear-datasets-by-tags/
│   │   ├── runnable.json      The form
│   │   └── runnable.py        The entry point
│   └── report-dataset-tags/   The same two files
├── resource/
│   └── tag_choices.py         Fills the "Cat. Tags" lists of the forms
├── tests/                     pytest tests: core/, recap/ and macros/ mirror python-lib
│   ├── core/
│   ├── recap/
│   ├── macros/
│   ├── plugin/                The plugin files of every macro: forms, runnables, imports, zip
│   ├── integration/           The macros on a real DSS, skipped without a config file
│   └── support/               Fake DSS objects and test helpers
├── docs/                      Documentation
│   ├── images/                The screenshot of the README
│   └── macros/                The user guide and automation page of each macro
├── README.md                  For users: what the plugin does, install, settings
├── CHANGELOG.md               The changes of each version
├── LICENSE                    MIT License
├── build_plugin_zip.py        Builds the zip to install in DSS
├── pyproject.toml             Development tools and their settings
├── uv.lock                    Exact versions of the tools
├── .python-version            Python 3.9, the version DSS 13 runs
└── .github/
    ├── workflows/
    │   ├── ci.yml             Checks and tests on each push and pull request
    │   └── release.yml        Publishes the release of a version tag, with its zip
    ├── ISSUE_TEMPLATE/        The bug report form
    ├── CONTRIBUTING.md        How to contribute
    └── SECURITY.md            How to report a vulnerability
```

## Run the checks

Bash:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
for f in python-runnables/*/runnable.py; do uv run mypy "$f"; done
```

PowerShell:

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
Get-ChildItem python-runnables\*\runnable.py | ForEach-Object { uv run mypy $_.FullName }
```

Good to know:

- **`uv run ruff format .`** fixes the format. `uv run ruff check --fix .` fixes what it can.
- **mypy, one runnable at a time.** All runnables are named `runnable.py`, and mypy refuses two files with the same name in one run. This is why there is a loop.
- **mypy 1.x.** mypy 2 cannot check code for Python 3.9 any more.
- **Another Python version.** To run the tests on Python 3.13, like the CI: `uv run --isolated --python 3.13 --group dev pytest`.
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
| `tests/support/` | Tools for the tests: fake DSS objects (`fakes.py`), a fake `dataiku` package (`dataiku_stub.py`), a helper to run a macro (`runs.py`), and the smallest possible macro (`sample_macro.py`). |
| `tests/core/` | The shared code of `core`: options, tags, project, runner. The runner is tested with `sample_macro.py`, without a real macro. |
| `tests/recap/` | The HTML recap, with a page made by hand, and the summary dataset. |
| `tests/macros/<macro>/` | One macro: its work, its options, its recap, its form, its `runnable.py`. |
| `tests/plugin/` | The plugin files, for **each** macro: form, `runnable.py`, import rules, zip. A new macro gets these tests with nothing to write. |
| `tests/integration/` | The macros on a real DSS. Skipped unless you give a config file: see [integration tests](integration-tests.md). |

To run only a part:

```bash
uv run pytest tests/macros/clear_datasets_by_tags
```

Two test files can have the same name in two different folders (`--import-mode=importlib` in `pyproject.toml`).

The fake objects copy the shape of the DSS answers. If a real DSS answers in another way (see [verification](verification.md) and the [integration tests](integration-tests.md)), fix the fake object and the code together.

## The CI

`.github/workflows/ci.yml` runs on each push and pull request.

| Job | Steps |
|---|---|
| Lint, types and plugin zip | `uv sync --locked`, ruff, ruff format, mypy, mypy for each runnable, then the build of the zip, kept as the `plugin-zip` artifact. |
| Tests on Python 3.9 and 3.13 | `uv run --locked --python <version> pytest`. |

`.github/workflows/release.yml` runs when a version tag is pushed: see [Release a version](#release-a-version).

## Change an option

Example with an option of Clear Datasets by Tags:

1. **Code:** in `macros/clear_datasets_by_tags/cleanup.py`, add it to `OPTION_DEFAULTS` and `OPTION_LABELS`. The default value must be the safe side.
2. **Form:** add it to `python-runnables/clear-datasets-by-tags/runnable.json`. A test checks that the default value and the label are the same as in the code.
3. **Tests:** add it to `OPTION_PARAMS` in `tests/macros/clear_datasets_by_tags/test_form.py`, and test its effect.
4. **Docs:** the user guide of the macro, its automation page, and the CHANGELOG.

The options of the "Summary" section are the same for all macros, and the "Run" section is the same for all macros that change data: they are in `core/options.py`.

## Do not rename

- **The plugin id** (`clear-datasets-by-tags` in `plugin.json`): it is part of the id of each macro and of the name of the zip. If it changes, scenarios and API calls break, and DSS sees another plugin.
- **The id of a macro** (the name of its folder): scenarios and the API use it, for example `pyrunnable_clear-datasets-by-tags_clear-datasets-by-tags`.

## Release a version

1. **Version:** set the same version in `plugin.json` and `pyproject.toml`, then run `uv lock`. A test checks that the two versions are equal.
2. **CHANGELOG:** describe the changes in [CHANGELOG.md](../CHANGELOG.md).
3. **Checks:** run them all, then [build the zip](#build-the-zip).
4. **Install:** in DSS, update the plugin with the new zip, in **Plugins > Installed**.
5. **Verify:** simulate the macro on a test project, then do the checks of [verification](verification.md) that the change touches.
6. **Publish:** push the commits to `main`, then tag the version and push the tag:

```bash
git tag 1.0.0
git push origin 1.0.0
```

The Release workflow checks that the tag is the version of `plugin.json`, runs the checks, builds the zip and publishes the GitHub release, with the section of the version in the CHANGELOG as its notes. A tag with a hyphen, such as `1.1.0-beta`, is published as a pre-release.
