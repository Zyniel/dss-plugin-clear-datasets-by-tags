"""Read the files of the repository, or of a copy of it."""

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    """Return the content of a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))
