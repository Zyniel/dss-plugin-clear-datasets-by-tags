"""Build the zip to upload in DSS: Plugins > Add plugin > Upload.

Run it with `uv run python build_plugin_zip.py`. It is also the build backend of pyproject.toml, so that
`uv build` stops with a message: uv builds Python wheels, and DSS installs a plugin zip.
"""

import json
import zipfile
from pathlib import Path
from typing import Any, NoReturn, Optional

# The paths are relative to this file, so that the script works from any folder.
ROOT = Path(__file__).resolve().parent

NOT_A_PACKAGE = (
    "This project is a plugin for Dataiku (DSS), not a Python package: uv build cannot make it.\n"
    "Build the plugin zip with: uv run python build_plugin_zip.py"
)


def build_plugin_zip() -> Path:
    """Build the plugin zip and return its path. Dataiku names plugin zips dss-plugin-<plugin id>-<version>.zip."""
    plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    zip_path = ROOT / "dist" / f"dss-plugin-{plugin['id']}-{plugin['version']}.zip"
    zip_path.parent.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as plugin_zip:
        plugin_zip.write(ROOT / "plugin.json", "plugin.json")
        plugin_zip.write(ROOT / "README.md", "README.md")
        plugin_zip.write(ROOT / "LICENSE", "LICENSE")
        for folder in ["python-lib", "python-runnables", "resource"]:
            for path in sorted((ROOT / folder).rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    plugin_zip.write(path, path.relative_to(ROOT).as_posix())
    return zip_path


# The hooks that uv build calls (PEP 517). They stop it: a wheel of this project would be of no use in DSS.
def build_sdist(sdist_directory: str, config_settings: Optional[dict[str, Any]] = None) -> NoReturn:
    """Stop uv build, which asks for a source package.

    :raises SystemExit: always, with how to build the plugin zip
    """
    raise SystemExit(NOT_A_PACKAGE)


def build_wheel(
    wheel_directory: str, config_settings: Optional[dict[str, Any]] = None, metadata_directory: Optional[str] = None
) -> NoReturn:
    """Stop uv build, which asks for a wheel.

    :raises SystemExit: always, with how to build the plugin zip
    """
    raise SystemExit(NOT_A_PACKAGE)


if __name__ == "__main__":
    print(build_plugin_zip())
