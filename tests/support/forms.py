"""Read the form of a macro, its runnable.json, as DSS does."""

import json
from typing import Any

from support.dataiku_stub import RUNNABLES


def read_form(macro_id: str) -> dict[str, Any]:
    """Return the runnable.json of a macro, from the id of the macro: its form, with its parameters."""
    form: dict[str, Any] = json.loads((RUNNABLES / macro_id / "runnable.json").read_text(encoding="utf-8"))
    return form


def named_params(settings: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return the parameters of a form or of plugin.json by name, without the separators of the sections."""
    return {param["name"]: param for param in settings["params"] if "name" in param}
