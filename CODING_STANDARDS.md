# Coding standards

The Python conventions of this repository that ruff cannot check. Ruff checks the others: see `[tool.ruff.lint]` in `pyproject.toml`. The words come from the [glossary](GLOSSARY.md), and the layout from the [architecture](docs/architecture.md).

## Names

- **`build_*`** returns data: a `RecapPage`, a `Table`, banners, rows. **`render_*`** returns HTML, and lives in `recap/html.py`.
- **`format_*`** turns one value into a short text: `format_count(2, "dataset")` gives "2 datasets". **`describe_*`** writes a sentence or a clause for the reader, such as `describe_dss_error()` or `describe_unchecked()`. `describe_failures()` returns a `WorkFailure`, a record of such texts.
- **`count_*`** returns numbers: an `int`, or a `dict` of them.
- **`make_*`** builds sample data, in the tests only.
- **Text helpers** that write no HTML live in `recap/text.py`. `recap/html.py` escapes every free text with `escape_text()`.
- **Exceptions** end with `Error`, such as `RunBlockedError`.
- **Glossary words** in names, comments, log lines and test names: a risk, not a warning; the recap, not the report; Include, not scope; clear, not purge.
- **API names stay**: the parameters of the forms, the fields of the JSON recap and the columns of the summary dataset never change, since scenarios and API calls use them. Some keep a word the glossary avoids, such as `recap_dataset`, `purge_shared`, `included_scope` or `warnings`. Where the code defines them, a comment says why, and the code around them uses the glossary word.

## Records

- A record with fixed fields is a `NamedTuple`.
- A record that becomes JSON as it is, or that the code fills in steps, is a `TypedDict`, such as `DatasetRow` or `GridCdn`. `json.dumps` would write a `NamedTuple` as a list.
- A plain `dict` holds data whose keys vary: the recap, since each macro has its own fields, and the rows of a `Table`, whose keys are the column fields.
- A field of several items is a `list`. With a default, it is a `Sequence` with `()` as the default, such as `Section.chips`: a list default would be shared by every instance.

## Errors as text

- `format_error(error)` gives an exception as its type and its message: "OSError: disk full".
- `describe_dss_error(error)` ends a message with an error of DSS: "DSS said: Disk full.", cut after 200 characters. The log has the whole error.

## Messages

- A form label or choice goes between double quotes: `Uncheck "Simulate" to clear.`
- It comes from its constant, such as `OPTION_LABELS`, `RUN_OPTION_LABELS` or `INCLUDE_CHOICES`, so that the message follows the form.

## Docstrings

Ruff checks that each module, class and function has a docstring, with a one-line summary in the imperative. In the body, Sphinx fields:

- `:param name:` for each parameter that its name and type do not explain, and only those.
- `:raises SomeError:` for each exception a function raises on purpose, its own or a callee's, with when. Always as a field, so that a reader finds every one in the same place.
- `:returns:` only when the summary cannot say it, such as the parts of a tuple.

A method that only stands for another one of the same name has no docstring: the methods of `macros/*/macro.py`, which `MaintenanceMacro` documents, and the methods of `tests/support/fakes.py`, which stand for the DSS methods. A nested function has none either.

## Tests

- A test is named after what it shows, `test_<sentence>`, and its name is its only docstring.
- Each helper has a one-line docstring. Ruff checks it in `tests/support` only: in a test file, it cannot tell a helper from a test.
- A helper that two test files need lives in `tests/support`.
