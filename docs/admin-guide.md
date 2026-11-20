# Admin guide

What a DSS administrator must know to install the plugin and trust it.

## Requirements

- DSS 13. Checked on DSS 13.4.4.
- The built-in Python 3.9 environment of DSS. No code environment, no extra package.

## Install and update

1. Download the zip of a version from the [Releases](https://github.com/Zyniel/dss-plugin-clear-datasets-by-tags/releases) of the repository.
2. Install: **Plugins > Add plugin > Upload**. Update: **Plugins > Installed > Clear Datasets by Tags**, then upload the new zip.
3. Set the [plugin settings](#plugin-settings) if needed.

After an update, DSS still shows each user the values of their last run in the form. "Reset to default" shows the new defaults.

Before an update, read the [CHANGELOG](../CHANGELOG.md): a change can change the result of a scenario or a script.

## Plugin settings

Set them once, in **Plugins > Installed > Clear Datasets by Tags > Settings**. They apply to all macros.

| Setting | Default | Use |
|---|---|---|
| AG Grid URL | AG Grid Community 29.2.0 on cdn.jsdelivr.net | Where a downloaded recap loads AG Grid from, to show its interactive table. Set the URL of an internal mirror, or leave it empty to load nothing: the recap then shows a simple table. |
| AG Grid integrity hash | The hash of that file | The browser loads the file only if it has this hash. Change it together with the URL. Several hashes, separated by spaces, are accepted. Empty: no check. |
| Tag categories | Empty | The "Cat. Tags" lists of the forms offer only the tags of these categories, such as `Stage`. Exact names, upper and lower case included. An entry such as `Stage:` or `Stage:Raw` means `Stage`. Empty: all categories. |

Inside DSS, the recap always uses the AG Grid of DSS, never the two AG Grid settings.

The AG Grid URL must start with `http://` or `https://`, since a downloaded recap is opened from a file. The integrity hash must be made of `sha256-`, `sha384-` or `sha512-` hashes. With any other value, the macros ignore both settings, as with an empty URL: downloaded recaps show the simple table, and the log of each run has a WARNING line near its start, with the value. The macros check these values at each run, not when you save them.

## Rights

The macros run with the rights of the user who runs them (`"impersonate": true`). They give no extra rights.

| Macro | Who can run it | What it changes |
|---|---|---|
| Clear Datasets by Tags | Users who can write in the project | The data of the datasets to clear, which can be all the datasets of the project. It cannot be undone. |
| Report Dataset Tags | Users who can read the project | Nothing. |

Some checks need more rights. Only project administrators can read which datasets are shared, and only DSS administrators can read the global tag categories. Without these rights, the recap says what was not checked.

The macros were checked on DSS as a DSS administrator only. See [verification](verification.md).

## What Clear Datasets by Tags never does

- It never clears data while "Simulate" is checked, and "Simulate" is checked by default.
- It never clears an external dataset or the summary dataset.
- It never deletes a dataset: only the data is cleared, the definition stays.

"Clear shared datasets" is checked by default: the projects that use a shared dataset can break when it is cleared.

## Network

- In DSS, nothing is loaded from the internet: the recap uses the AG Grid of DSS.
- A downloaded recap, opened outside DSS, loads AG Grid from the "AG Grid URL" setting (by default, cdn.jsdelivr.net). The browser checks the file with the integrity hash. It sends no project data. Set an internal copy, or leave the URL empty to load nothing.

## Audit

- Each run writes its whole recap on the `RECAP_JSON` line of its log. A run that ends in error before its work, because the form is not valid or a check blocks it, writes no recap: only its message says why. A scenario keeps it in its "Last runs".
- A user can also write the recap to a dataset of the project, in "Append mode" to keep a history.

The DSS API calls of the macros are listed in [architecture](architecture.md#the-dss-api-calls).
