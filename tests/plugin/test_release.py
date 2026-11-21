"""Tests of release.py at its command line: prepare a version, and write the notes of its release.

They run a copy of release.py in a copy of the files a release changes, as the workflows run it. See docs/releasing.md.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import release
from support.dataiku_stub import ROOT
from support.files import read_json

DAY = "2026-12-01"
REPOSITORY = "Zyniel/repo"
CHANGELOG = """# Changelog

Intro.

## Unreleased

### Clear Datasets by Tags

- A fix. See the [user guide](docs/macros/clear-datasets-by-tags/user-guide.md#select-the-datasets).

## 1.0.0 - 2026-11-18

First version, under the [MIT License](LICENSE). Details on [GitHub](https://github.com/x/y), [below](#below).
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Return a copy of release.py and of the files it changes, with a CHANGELOG that has unreleased changes.

    The copies are at version 1.0.0, whatever the version of the repository: the tests must pass in every release.
    """
    shutil.copy(ROOT / "release.py", tmp_path)
    for name in release.VERSION_LINES:
        text = (ROOT / name).read_text(encoding="utf-8")
        (tmp_path / name).write_text(release.set_version(text, name, "1.0.0"), encoding="utf-8")
    write_changelog(tmp_path, CHANGELOG)
    return tmp_path


def run_release(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the release.py of a repository, or of a copy of it, as the workflows run it."""
    # The notes are UTF-8, whatever the code page of the console.
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    command = [sys.executable, str(repo / "release.py"), *arguments]
    return subprocess.run(command, cwd=repo, capture_output=True, encoding="utf-8", env=environment, check=False)


def read_copied_file(repo: Path, name: str) -> str:
    """Return the text of a file of the copy of the repository."""
    return (repo / name).read_text(encoding="utf-8")


def write_changelog(repo: Path, changelog: str) -> None:
    """Replace the CHANGELOG of the copy of the repository."""
    (repo / "CHANGELOG.md").write_text(changelog, encoding="utf-8")


def read_copied_files(repo: Path) -> dict[str, str]:
    """Return the text of each file of the copy of the repository, by name."""
    return {path.name: path.read_text(encoding="utf-8") for path in repo.iterdir() if path.is_file()}


def test_prepare_sets_the_version_everywhere_and_dates_the_changelog(repo: Path) -> None:
    result = run_release(repo, "prepare", "1.1.0", "--date", DAY)

    assert (result.returncode, result.stdout) == (0, "Prepared 1.1.0. Run `uv lock`, then commit.\n")
    assert read_json(repo / "plugin.json")["version"] == "1.1.0"
    assert '\nversion = "1.1.0"\n' in read_copied_file(repo, "pyproject.toml")
    assert "\n## 1.1.0 - 2026-12-01\n\n### Clear Datasets by Tags\n" in read_copied_file(repo, "CHANGELOG.md")
    assert "## Unreleased" not in read_copied_file(repo, "CHANGELOG.md")


def test_prepare_changes_only_the_version_lines(repo: Path) -> None:
    before = {name: read_copied_file(repo, name).splitlines() for name in release.VERSION_LINES}

    assert run_release(repo, "prepare", "1.1.0", "--date", DAY).returncode == 0

    for name, lines in before.items():
        after = read_copied_file(repo, name).splitlines()
        assert len(after) == len(lines)
        assert sum(old != new for old, new in zip(lines, after)) == 1, name


def test_the_first_release_keeps_the_version_of_plugin_json(repo: Path) -> None:
    write_changelog(repo, CHANGELOG.replace("## 1.0.0 - 2026-11-18", "## 0.9.0 - 2026-01-01"))

    assert run_release(repo, "prepare", "1.0.0", "--date", DAY).returncode == 0

    assert read_json(repo / "plugin.json")["version"] == "1.0.0"
    assert "\n## 1.0.0 - 2026-12-01\n" in read_copied_file(repo, "CHANGELOG.md")


@pytest.mark.parametrize(
    ("version", "changelog", "message"),
    [
        ("1.1", CHANGELOG, r"'1\.1' is not a version"),
        ("v1.1.0", CHANGELOG, r"'v1\.1\.0' is not a version"),
        ("0.9.0", CHANGELOG, r"0\.9\.0 is lower than the version of plugin\.json"),
        ("1.0.0", CHANGELOG, r"already has a section for 1\.0\.0"),
        ("1.1.0", CHANGELOG.replace("## Unreleased", "## Later"), r'no "## Unreleased" section'),
        ("1.1.0", "# Changelog\n\n## Unreleased\n\n## 1.0.0 - 2026-11-18\n\nText.\n", r"or it is empty"),
    ],
)
def test_prepare_refuses_and_changes_nothing(repo: Path, version: str, changelog: str, message: str) -> None:
    write_changelog(repo, changelog)
    before = read_copied_files(repo)

    result = run_release(repo, "prepare", version, "--date", DAY)

    assert result.returncode == 1
    assert re.match(rf"error: .*{message}", result.stderr)
    assert read_copied_files(repo) == before


def test_a_pre_release_can_follow_the_version_it_announces(repo: Path) -> None:
    assert run_release(repo, "prepare", "1.1.0-beta", "--date", DAY).returncode == 0

    assert read_json(repo / "plugin.json")["version"] == "1.1.0-beta"
    assert "\n## 1.1.0-beta - 2026-12-01\n" in read_copied_file(repo, "CHANGELOG.md")


def test_the_notes_are_the_section_of_the_version_with_absolute_links(repo: Path) -> None:
    result = run_release(repo, "notes", "1.0.0", "--ref", "1.0.0", "--repository", REPOSITORY)

    assert (result.returncode, result.stdout) == (
        0,
        "First version, under the [MIT License](https://github.com/Zyniel/repo/blob/1.0.0/LICENSE). "
        "Details on [GitHub](https://github.com/x/y), [below](#below).\n",
    )


def test_the_notes_of_a_version_stop_at_the_next_section(repo: Path) -> None:
    write_changelog(repo, CHANGELOG.replace("## Unreleased", "## 1.1.0 - 2026-12-01"))

    notes = run_release(repo, "notes", "1.1.0", "--ref", "release/1.1.0", "--repository", REPOSITORY).stdout

    assert notes.startswith("### Clear Datasets by Tags\n")
    assert "First version" not in notes
    assert "](https://github.com/Zyniel/repo/blob/release/1.1.0/docs/macros/" in notes


def test_the_notes_of_1_0_0_are_not_those_of_a_pre_release(repo: Path) -> None:
    write_changelog(repo, CHANGELOG.replace("## Unreleased", "## 1.0.0-beta - 2026-11-01"))

    assert "First version" in run_release(repo, "notes", "1.0.0", "--ref", "1.0.0", "--repository", REPOSITORY).stdout
    beta = run_release(repo, "notes", "1.0.0-beta", "--ref", "1.0.0-beta", "--repository", REPOSITORY)
    assert "A fix" in beta.stdout


def test_a_version_without_notes_is_refused_unless_a_dry_run_shows_the_unreleased_changes(repo: Path) -> None:
    refused = run_release(repo, "notes", "1.1.0", "--ref", "main", "--repository", REPOSITORY)

    assert (refused.returncode, refused.stdout) == (1, "")
    assert refused.stderr == "error: CHANGELOG.md has no section for 1.1.0.\n"

    dry_run = run_release(repo, "notes", "1.1.0", "--ref", "main", "--repository", REPOSITORY, "--unreleased-first")
    assert dry_run.stdout.startswith("### Clear Datasets by Tags\n")


@pytest.mark.parametrize(
    ("changelog", "version", "start"),
    [
        # On main: plugin.json still gives the last version released.
        (CHANGELOG, "1.0.0", "### Clear Datasets by Tags\n"),
        # On release/1.1.0: Prepare release turned "## Unreleased" into the section of the version.
        (CHANGELOG.replace("## Unreleased", "## 1.1.0 - 2026-12-01"), "1.1.0", "### Clear Datasets by Tags\n"),
        # Nothing changed since the last release yet.
        ("# Changelog\n\n## Unreleased\n\n## 1.0.0 - 2026-11-18\n\nText.\n", "1.0.0", "Text.\n"),
    ],
    ids=["on main", "on a release branch", "with nothing unreleased"],
)
def test_a_dry_run_shows_the_notes_of_the_next_release(repo: Path, changelog: str, version: str, start: str) -> None:
    write_changelog(repo, changelog)

    result = run_release(repo, "notes", version, "--ref", "main", "--repository", REPOSITORY, "--unreleased-first")

    assert result.stdout.startswith(start)


def test_the_command_line_reports_an_error_without_a_traceback(repo: Path) -> None:
    result = run_release(repo, "prepare", "1.1")

    assert result.returncode == 1
    assert result.stderr == "error: '1.1' is not a version such as 1.1.0, or 1.1.0-beta for a pre-release.\n"


def test_the_changelog_of_the_repository_can_be_released() -> None:
    # Either the changes to release are under "## Unreleased", or the version of plugin.json is released already.
    version = read_json(ROOT / "plugin.json")["version"]

    result = run_release(ROOT, "notes", version, "--ref", "main", "--repository", REPOSITORY, "--unreleased-first")

    assert result.returncode == 0
    assert result.stdout.strip()
