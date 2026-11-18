# Dataiku Plugin - Clear Datasets by Tags

[![CI](https://github.com/Zyniel/dss-plugin-clear-datasets-by-tags/actions/workflows/ci.yml/badge.svg)](https://github.com/Zyniel/dss-plugin-clear-datasets-by-tags/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/Zyniel/dss-plugin-clear-datasets-by-tags)](https://github.com/Zyniel/dss-plugin-clear-datasets-by-tags/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![DSS 13 and later](https://img.shields.io/badge/DSS-13%2B-blue)

**Clear Datasets by Tags** is a Dataiku DSS plugin with macros to maintain projects: it clears the data of the datasets selected by their tags, or of all datasets, and reports how the datasets use tags. A macro that changes data simulates by default: it shows what it would do before it changes anything.

> Community plugin: not affiliated with, supported or endorsed by Dataiku. For questions and bugs, open an [issue](https://github.com/Zyniel/dss-plugin-clear-datasets-by-tags/issues).

![The recap of a simulation: 4 datasets would be cleared, 3 are skipped and 1 is excluded](docs/images/recap-clear-datasets-by-tags.png)

| | |
|---|---|
| Plugin id | `clear-datasets-by-tags` |
| Version | 1.0.0 (see the [CHANGELOG](CHANGELOG.md)) |
| Works with | DSS 13 and later, in the built-in Python 3.9 environment, with no code environment |

## The macros

They are in the **Project maintenance** section of the **Macros** page of a project.

| Macro | What it does | Documentation |
|---|---|---|
| Clear Datasets by Tags | Clears the data of the datasets with the included tags, or of all datasets, except the excluded ones. | [User guide](docs/macros/clear-datasets-by-tags/user-guide.md), [automation](docs/macros/clear-datasets-by-tags/automation.md) |
| Report Dataset Tags | Reports how the datasets use tags: tags in use, unused tags, unknown category tags, datasets with no tag. Changes nothing. | [User guide](docs/macros/report-dataset-tags/user-guide.md), [automation](docs/macros/report-dataset-tags/automation.md) |

## Install

1. Download `dss-plugin-clear-datasets-by-tags-<version>.zip` from the [latest release](https://github.com/Zyniel/dss-plugin-clear-datasets-by-tags/releases/latest).
2. In DSS, as an administrator: **Plugins > Add plugin > Upload**, then select the zip. To update, read the [CHANGELOG](CHANGELOG.md), then upload the new zip in **Plugins > Installed > Clear Datasets by Tags**.
3. Set the [plugin settings](#plugin-settings) if needed.

To build the zip from the sources, see [development](docs/development.md#build-the-zip).

## Quick start

In DSS:

1. In a project, open **Macros** and select **Clear Datasets by Tags**.
2. Give the included tags, such as `temporary`, keep **Simulate** checked, and run the macro.
3. Read the recap: what would be cleared, what is skipped and why. Then uncheck **Simulate** and run it again.

From Python, in a notebook or a scenario of DSS:

```python
import dataiku

project = dataiku.api_client().get_default_project()
macro = project.get_macro("pyrunnable_clear-datasets-by-tags_clear-datasets-by-tags")
run_id = macro.run(params={"included_tags": ["temporary"]})  # A simulation: nothing is cleared
```

Add `"simulate": False` to clear. The parameters and the result are in [automation](docs/macros/clear-datasets-by-tags/automation.md).

## Plugin settings

An administrator sets them in **Plugins > Installed > Clear Datasets by Tags > Settings**. The details are in the [admin guide](docs/admin-guide.md#plugin-settings).

| Setting | Default | Use |
|---|---|---|
| AG Grid URL | AG Grid Community on cdn.jsdelivr.net | Where a downloaded recap loads its interactive table from. Empty: a simple table. |
| AG Grid integrity hash | The hash of that file | The browser loads the file only if it has this hash. |
| Tag categories | Empty: all categories | The categories that the "Cat. Tags" lists of the forms offer, such as `Stage`. |

## Documentation

| Document | Content |
|---|---|
| [Admin guide](docs/admin-guide.md) | For DSS administrators: install, settings, rights, what the macros change, network. |
| [Architecture](docs/architecture.md) | How the code is split, the import rules, the steps of a run. |
| [Development](docs/development.md) | Set up, the repository layout, the checks and the tests, build the zip. |
| [Releasing](docs/releasing.md) | Release a version: the workflows, the steps, what to do if something fails. |
| [Add a macro](docs/adding-a-macro.md) | The steps, in order, to add a macro to the plugin. |
| [Verification](docs/verification.md) | What the tests prove, and the checks to do on a real DSS. |
| [Integration tests](docs/integration-tests.md) | Run the macros on a real DSS, as an administrator, an editor and a reader. |
| [CHANGELOG](CHANGELOG.md) | What changes in each version. |

## Contributing

Bug reports and pull requests are welcome: see [contributing](.github/CONTRIBUTING.md). Report a vulnerability privately, as the [security policy](.github/SECURITY.md) explains.

## License

[MIT](LICENSE)
