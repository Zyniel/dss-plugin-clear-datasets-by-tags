"""Run the checks of the CI, one after the other, and print the output of those that fail.

Run it with `uv run python check.py`. The CI and the release workflows call it too, so that the checks and the
Python versions of the tests are the same everywhere. `--no-tests` skips the tests. `--tests-on 3.13` runs only the
tests, on Python 3.13: each tests job of the CI runs it with its Python. `--help` lists the Python versions.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, Optional

# The paths are relative to this file, so that the script works from any folder.
ROOT = Path(__file__).resolve().parent

# The Python of DSS 13, given by .python-version: the environment of the project, which runs this script, is on it.
DSS_PYTHON = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
# The newer one shows the code keeps working after a DSS upgrade.
NEWER_PYTHON = "3.13"
# The tests run on each of them, in this order.
TESTED_PYTHONS = [DSS_PYTHON, NEWER_PYTHON]


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
        checks.extend(build_tests_check(version) for version in TESTED_PYTHONS)
    return checks


def build_tests_check(version: str) -> Check:
    """Return the check that runs the tests on a Python of TESTED_PYTHONS."""
    if version == DSS_PYTHON:
        command = [sys.executable, "-m", "pytest"]
    else:
        # --isolated leaves the environment of the project on the Python of DSS 13.
        command = ["uv", "run", "--isolated", "--locked", "--python", version, "pytest"]
    return Check(f"pytest on Python {version}", command)


def run_check(check: Check) -> bool:
    """Run the check, print its name and whether it passed, and its output if it failed. Return True if it passed."""
    result = subprocess.run(check.command, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")
    passed = result.returncode == 0
    print(f"{'ok  ' if passed else 'FAIL'} {check.name}", flush=True)
    if not passed:
        print(result.stdout + result.stderr, flush=True)
    return passed


def main(argv: Optional[list[str]] = None) -> int:
    """Run the checks that the arguments ask for, even after one fails, and return 1 if one failed.

    :param argv: the arguments of the command line, without the name of the script. By default, those of `sys.argv`.
    """
    parser = argparse.ArgumentParser(description="Run the checks of the CI.")
    tests_options = parser.add_mutually_exclusive_group()
    tests_options.add_argument("--no-tests", action="store_true", help="skip the tests")
    tests_options.add_argument(
        "--tests-on",
        choices=TESTED_PYTHONS,
        metavar="PYTHON",
        help=f"run only the tests, on this Python: {' or '.join(TESTED_PYTHONS)}",
    )
    args = parser.parse_args(argv)
    checks = [build_tests_check(args.tests_on)] if args.tests_on else list_checks(with_tests=not args.no_tests)
    results = [run_check(check) for check in checks]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
