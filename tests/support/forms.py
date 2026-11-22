"""Read the form of a macro, its runnable.json, as DSS does."""

from typing import Any

from support.dataiku_stub import RUNNABLES
from support.files import read_json


def read_form(macro_id: str) -> dict[str, Any]:
    """Return the runnable.json of a macro, from the id of the macro: its form, with its parameters."""
    form: dict[str, Any] = read_json(RUNNABLES / macro_id / "runnable.json")
    return form


def named_params(settings: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return the parameters of a form or of plugin.json by name, without the separators of the sections."""
    return {param["name"]: param for param in settings["params"] if "name" in param}
