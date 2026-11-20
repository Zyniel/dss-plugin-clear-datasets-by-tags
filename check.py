"""Run the checks of the CI, one after the other, and print the output of those that fail.

Run it with `uv run python check.py`. The CI and the release workflows call it too, so that the checks
are the same everywhere. `--no-tests` skips pytest: the tests job of the CI runs it on each Python version.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

# The paths are relative to this file, so that the script works from any folder.
ROOT = Path(__file__).resolve().parent

# .python-version gives the Python of DSS 13. The newer one shows the code keeps working after a DSS upgrade.
NEWER_PYTHON = "3.13"


class Check(NamedTuple):
    """A check: its name, and the command that runs it from the root of the repository."""

    name: str
    command: list[str]


def list_checks(with_tests: bool) -> list[Check]:
    """Return the checks, in the order the CI runs them."""
    python = sys.executable
    checks = [
        Check("ruff", [python, "-m", "ruff", "check", "."]),
        Check("ruff format", [python, "-m", "ruff", "format", "--check", "."]),
        Check("mypy", [python, "-m", "mypy"]),
    ]
    # The runnables all have the same file name, so mypy checks them one at a time.
    for runnable in sorted(ROOT.glob("python-runnables/*/runnable.py")):
        path = runnable.relative_to(ROOT).as_posix()
        checks.append(Check(f"mypy {path}", [python, "-m", "mypy", path]))
    checks.append(Check("plugin zip", [python, "build_plugin_zip.py"]))
    if with_tests:
        checks.append(Check("pytest", [python, "-m", "pytest"]))
        # --isolated leaves the environment of the project on the Python of DSS 13.
        newer = ["uv", "run", "--isolated", "--locked", "--python", NEWER_PYTHON, "pytest"]
        checks.append(Check(f"pytest on Python {NEWER_PYTHON}", newer))
    return checks


def run_check(check: Check) -> bool:
    """Run the check, print its name and whether it passed, and its output if it failed. Return True if it passed."""
    result = subprocess.run(check.command, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")
    passed = result.returncode == 0
    print(f"{'ok  ' if passed else 'FAIL'} {check.name}", flush=True)
    if not passed:
        print(result.stdout + result.stderr, flush=True)
    return passed


def main() -> int:
    """Run every check, even after one fails, and return 1 if one failed."""
    parser = argparse.ArgumentParser(description="Run the checks of the CI.")
    parser.add_argument("--no-tests", action="store_true", help="skip pytest")
    args = parser.parse_args()
    results = [run_check(check) for check in list_checks(with_tests=not args.no_tests)]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
