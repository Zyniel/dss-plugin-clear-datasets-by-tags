# Dataiku Plugin - Clear Datasets by Tags

**Clear Datasets by Tags** is a Dataiku DSS plugin with macros to maintain projects: it clears the data of the datasets selected by their tags, or of all datasets, and reports how the datasets use tags. A macro that changes data simulates by default: it shows what it would do before it changes anything.

| | |
|---|---|
| Plugin id | `clear-datasets-by-tags` |
| Version | 1.0.0 (see the [CHANGELOG](CHANGELOG.md)) |
| Works with | DSS 13 and later, in the built-in Python 3.9 environment, with no code environment |
| License | [MIT](LICENSE): free to use for any purpose, keeping the copyright notice and the license text in copies |

## The macros

In a project, open **Macros**: the macros of the plugin are in the **Project maintenance** section.

| Macro | What it does | Documentation |
|---|---|---|
| Clear Datasets by Tags | Clears the data of the datasets with the included tags, or of all datasets, except the excluded ones. | [User guide](docs/macros/clear-datasets-by-tags/user-guide.md), [automation](docs/macros/clear-datasets-by-tags/automation.md) |
| Report Dataset Tags | Reports how the datasets use tags: tags in use, unused tags, unknown category tags, datasets with no tag. Changes nothing. | [User guide](docs/macros/report-dataset-tags/user-guide.md), [automation](docs/macros/report-dataset-tags/automation.md) |

## Install

1. Build the zip: `uv run python build_plugin_zip.py`. The zip is in `dist/dss-plugin-clear-datasets-by-tags-<version>.zip`. `uv build` does not build the plugin: it only makes Python wheels, so it stops with a message.
2. In DSS: **Plugins > Add plugin > Upload**, then select the zip.
3. In a project: open **Macros**, select a macro and run it. For a macro that changes data, keep "Simulate" checked first, and read the recap before a real run.

[uv](https://docs.astral.sh/uv/) installs Python 3.9 and the tools the first time. The command is the same in bash and PowerShell.

## Plugin settings

A DSS administrator sets them once, in **Plugins > Installed > Clear Datasets by Tags > Settings**. They apply to all macros.

| Setting | Default | Use |
|---|---|---|
| AG Grid URL | AG Grid Community 29.2.0 on cdn.jsdelivr.net | Where a downloaded recap loads AG Grid from, to show its interactive table. Set the URL of an internal mirror, or leave it empty to load nothing: the recap then shows a simple table. |
| AG Grid integrity hash | The hash of that file | The browser loads the file only if it has this hash. Change it together with the URL. Several hashes, separated by spaces, are accepted. Empty: no check. |
| Tag categories | Empty | The "Cat. Tags" lists of the forms offer only the tags of these categories, such as `Stage`. Exact names, upper and lower case included. An entry such as `Stage:` or `Stage:Raw` means `Stage`. Empty: all categories. |

Inside DSS, the recap always uses the AG Grid of DSS, never the two AG Grid settings.

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
├── docs/                      Documentation, see the table below
│   └── macros/                The user guide and automation page of each macro
├── README.md                  This page
├── CHANGELOG.md               The changes of each version
├── LICENSE                    MIT License
├── build_plugin_zip.py        Builds the zip to install in DSS
├── pyproject.toml             Development tools and their settings
├── uv.lock                    Exact versions of the tools
├── .python-version            Python 3.9, the version DSS 13 runs
└── .github/workflows/ci.yml   The CI: checks and tests on each push and pull request
```

The plugin zip holds `plugin.json`, `README.md`, `LICENSE`, `python-lib/`, `python-runnables/` and `resource/`. The rest is for development.

## Documentation

| Document | Content |
|---|---|
| [Admin guide](docs/admin-guide.md) | For DSS administrators: install, rights, what the macros change, network. |
| [Architecture](docs/architecture.md) | How the code is split, the import rules, the steps of a run. |
| [Development](docs/development.md) | Set up, run the checks and the tests, release a version. |
| [Add a macro](docs/adding-a-macro.md) | The steps, in order, to add a macro to the plugin. |
| [Verification](docs/verification.md) | What the tests prove, and the checks to do on a real DSS. |
| [Integration tests](docs/integration-tests.md) | Run the macros on a real DSS, as an administrator, an editor and a reader. |
| [CHANGELOG](CHANGELOG.md) | What changes in each version. |
