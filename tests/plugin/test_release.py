"""Tests of release.py: prepare a version, and write the notes of its release. See docs/releasing.md."""

import datetime
import json
from pathlib import Path
from typing import Any

import pytest

from support.dataiku_stub import ROOT, load_module

release: Any = load_module(ROOT / "release.py")

DAY = datetime.date(2026, 12, 1)
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
    """A copy of the files release.py changes, with a CHANGELOG that has unreleased changes.

    The copies are at version 1.0.0, whatever the version of the repository: the tests must pass in every release.
    """
    for name, (pattern, line) in release.VERSION_LINES.items():
        text = (ROOT / name).read_text(encoding="utf-8")
        (tmp_path / name).write_text(release.replace_line(text, pattern, line.format("1.0.0"), name), "utf-8")
    (tmp_path / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    return tmp_path


def text(repo: Path, name: str) -> str:
    return (repo / name).read_text(encoding="utf-8")


def test_prepare_sets_the_version_everywhere_and_dates_the_changelog(repo: Path) -> None:
    release.prepare(repo, "1.1.0", DAY)

    assert json.loads(text(repo, "plugin.json"))["version"] == "1.1.0"
    assert '\nversion = "1.1.0"\n' in text(repo, "pyproject.toml")
    assert "\n| Version | 1.1.0 (see the [CHANGELOG](CHANGELOG.md)) |\n" in text(repo, "README.md")
    assert "\n## 1.1.0 - 2026-12-01\n\n### Clear Datasets by Tags\n" in text(repo, "CHANGELOG.md")
    assert "## Unreleased" not in text(repo, "CHANGELOG.md")


def test_prepare_changes_only_the_version_lines(repo: Path) -> None:
    before = {name: text(repo, name).splitlines() for name in ["plugin.json", "pyproject.toml", "README.md"]}

    release.prepare(repo, "1.1.0", DAY)

    for name, lines in before.items():
        after = text(repo, name).splitlines()
        assert len(after) == len(lines)
        assert sum(old != new for old, new in zip(lines, after)) == 1, name


def test_the_first_release_keeps_the_version_of_plugin_json(repo: Path) -> None:
    (repo / "CHANGELOG.md").write_text(CHANGELOG.replace("## 1.0.0 - 2026-11-18", "## 0.9.0 - 2026-01-01"), "utf-8")

    release.prepare(repo, "1.0.0", DAY)

    assert json.loads(text(repo, "plugin.json"))["version"] == "1.0.0"
    assert "\n## 1.0.0 - 2026-12-01\n" in text(repo, "CHANGELOG.md")


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
    (repo / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    before = {path.name: path.read_text(encoding="utf-8") for path in repo.iterdir()}

    with pytest.raises(release.ReleaseError, match=message):
        release.prepare(repo, version, DAY)

    assert {path.name: path.read_text(encoding="utf-8") for path in repo.iterdir()} == before


def test_a_pre_release_can_follow_the_version_it_announces(repo: Path) -> None:
    release.prepare(repo, "1.1.0-beta", DAY)

    assert json.loads(text(repo, "plugin.json"))["version"] == "1.1.0-beta"
    assert "\n## 1.1.0-beta - 2026-12-01\n" in text(repo, "CHANGELOG.md")


def test_the_notes_are_the_section_of_the_version_with_absolute_links() -> None:
    notes = release.release_notes(CHANGELOG, "1.0.0", "1.0.0", "Zyniel/repo")

    assert notes == (
        "First version, under the [MIT License](https://github.com/Zyniel/repo/blob/1.0.0/LICENSE). "
        "Details on [GitHub](https://github.com/x/y), [below](#below).\n"
    )


def test_the_notes_of_a_version_stop_at_the_next_section() -> None:
    changelog = CHANGELOG.replace("## Unreleased", "## 1.1.0 - 2026-12-01")

    notes = release.release_notes(changelog, "1.1.0", "release/1.1.0", "Zyniel/repo")

    assert notes.startswith("### Clear Datasets by Tags\n")
    assert "First version" not in notes
    assert "](https://github.com/Zyniel/repo/blob/release/1.1.0/docs/macros/" in notes


def test_the_notes_of_1_0_0_are_not_those_of_a_pre_release() -> None:
    changelog = CHANGELOG.replace("## Unreleased", "## 1.0.0-beta - 2026-11-01")

    assert "First version" in release.release_notes(changelog, "1.0.0", "1.0.0", "Zyniel/repo")
    assert "A fix" in release.release_notes(changelog, "1.0.0-beta", "1.0.0-beta", "Zyniel/repo")


def test_a_version_without_notes_is_refused_unless_a_dry_run_falls_back_on_unreleased() -> None:
    with pytest.raises(release.ReleaseError, match=r"no section for 1\.1\.0"):
        release.release_notes(CHANGELOG, "1.1.0", "main", "Zyniel/repo")

    notes = release.release_notes(CHANGELOG, "1.1.0", "main", "Zyniel/repo", or_unreleased=True)
    assert notes.startswith("### Clear Datasets by Tags\n")


def test_the_command_line_reports_an_error_without_a_traceback() -> None:
    with pytest.raises(SystemExit, match=r"^error: '1\.1' is not a version"):
        release.main(["prepare", "1.1"])


def test_the_changelog_of_the_repository_can_be_released() -> None:
    # Either the changes to release are under "## Unreleased", or the version of plugin.json is released already.
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]

    assert release.release_notes(changelog, version, "main", "Zyniel/repo", or_unreleased=True).strip()
