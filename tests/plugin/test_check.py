"""Tests of check.py, which runs the checks of the CI: its mode that runs only the tests, on one Python.

The tests jobs of the CI run that mode, one Python each. See docs/development.md.
"""

import subprocess
import sys
from typing import Any

import pytest

import check
from support.dataiku_stub import ROOT


def record_commands(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Make every command that check.py runs pass without running it, and return the list of those commands."""
    commands: list[list[str]] = []

    def run(command: list[str], **options: Any) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    return commands


@pytest.mark.parametrize(
    ("version", "command"),
    [
        # The environment of the project, which runs check.py: the Python of .python-version, that of DSS 13.
        ("3.9", [sys.executable, "-m", "pytest"]),
        # An environment of its own, so that the one of the project stays on the Python of DSS 13.
        ("3.13", ["uv", "run", "--isolated", "--locked", "--python", "3.13", "pytest"]),
    ],
)
def test_tests_on_a_python_runs_pytest_on_that_python_and_nothing_else(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], version: str, command: list[str]
) -> None:
    commands = record_commands(monkeypatch)

    exit_code = check.main(["--tests-on", version])

    assert exit_code == 0
    assert commands == [command]
    assert capsys.readouterr().out == f"ok   pytest on Python {version}\n"


def test_tests_on_a_python_that_the_checks_do_not_test_fails_with_the_versions_they_test() -> None:
    command = [sys.executable, str(ROOT / "check.py"), "--tests-on", "3.11"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, encoding="utf-8", check=False)

    # The last line is the error of argparse, which quotes the versions or not, depending on the Python.
    error = result.stderr.splitlines()[-1].replace("'", "")
    assert result.returncode == 2
    assert error == "check.py: error: argument --tests-on: invalid choice: 3.11 (choose from 3.9, 3.13)"
    assert result.stdout == ""
