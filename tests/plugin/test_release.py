"""Tests of release.py at its command line: prepare a version, print notes, check a release branch and a pull request.

The notes are those of a version, or the notes of the next release, which a release branch must not have, and which a
pull request that changes the plugin adds to. The tests run a copy of release.py, and of the script it imports, in a
copy of the files a release changes, as the workflows run it: a git repository whose remote origin holds the tags and
branches of the versions. See docs/releasing.md.
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
# The CHANGELOG of the branch release/1.1.0, once Prepare release dated the notes of the next release.
PREPARED_CHANGELOG = CHANGELOG.replace("## Unreleased", f"## 1.1.0 - {DAY}")
# A CHANGELOG whose notes of the next release are empty: an "## Unreleased" section with nothing in it.
CHANGELOG_WITH_EMPTY_NOTES = "# Changelog\n\n## Unreleased\n\n## 1.0.0 - 2026-11-18\n\nText.\n"
# The two CHANGELOGs that have no notes of the next release.
WITHOUT_NEXT_RELEASE_NOTES = [
    pytest.param(CHANGELOG_WITH_EMPTY_NOTES, id="nothing changed since the last release"),
    pytest.param(PREPARED_CHANGELOG, id="dated by Prepare release"),
]
EMPTY_NEXT_RELEASE_NOTES = 'The notes of the next release are empty: CHANGELOG.md has nothing under "## Unreleased".\n'
# The CHANGELOG once a pull request added to the notes of the next release.
CHANGELOG_WITH_A_NEW_NOTE = CHANGELOG.replace("- A fix.", "- A new option.\n- A fix.")
# The branch of the pull request of the tests, which left main at its first commit.
PULL_REQUEST_BRANCH = "pull-request"
# The file of the plugin that change_plugin() changes.
CHANGED_PLUGIN_FILE = "python-lib/core/runner.py"
# The files of that first commit, besides those of the copy of the repository: one in each folder of the plugin zip,
# its README and its license, and a doc that the plugin zip does not hold.
BASE_FILES = {
    CHANGED_PLUGIN_FILE: "RUNNER = 1\n",
    "python-runnables/clear-datasets-by-tags/runnable.py": "RUNNABLE = 1\n",
    "resource/tag_choices.py": "CHOICES = 1\n",
    "README.md": "# Clear Datasets by Tags\n",
    "LICENSE": "MIT License\n",
    "docs/development.md": "# Development\n",
}
NOTHING_TO_CHECK = (
    "The pull request changes nothing in plugin.json, python-lib/, python-runnables/ or resource/: "
    "its notes of the next release are not checked.\n"
)
# The CI has no git identity: the commits of the tests get one of their own.
GIT_IDENTITY = ["-c", "user.name=Tests", "-c", "user.email=tests@example.com"]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Return a copy of release.py, the script it imports and the files it changes, with notes of the next release.

    The copies are at version 1.0.0, whatever the version of the repository: the tests must pass in every release.
    They are in a git repository, on main with no commit yet, whose remote origin has no tag and no branch yet.
    """
    copy = tmp_path / "repo"
    copy.mkdir()
    for name in ["release.py", "build_plugin_zip.py", *release.VERSION_LINES]:
        shutil.copy(ROOT / name, copy)
    set_version(copy, "1.0.0")
    write_changelog(copy, CHANGELOG)
    run_git(tmp_path, "init", "--bare", "origin.git")
    run_git(copy, "init", "--initial-branch=main")
    run_git(copy, "remote", "add", "origin", str(tmp_path / "origin.git"))
    return copy


@pytest.fixture
def pull_request(repo: Path) -> Path:
    """Return the copy of the repository on the branch of a pull request, which left main at its first commit."""
    for name, text in BASE_FILES.items():
        write_copied_file(repo, name, text)
    commit_all(repo, "The base of the pull request")
    run_git(repo, "switch", "--create", PULL_REQUEST_BRANCH)
    return repo


def run_git(folder: Path, *arguments: str) -> None:
    """Run a git command in a folder, and fail the test if it fails."""
    subprocess.run(["git", *arguments], cwd=folder, capture_output=True, check=True)


def commit_all(repo: Path, message: str) -> None:
    """Commit every change of the copy of the repository, on its current branch."""
    run_git(repo, "add", "--all")
    run_git(repo, *GIT_IDENTITY, "commit", "--message", message)


def change_plugin(repo: Path) -> None:
    """Change a file of the plugin in the copy of the repository: CHANGED_PLUGIN_FILE."""
    write_copied_file(repo, CHANGED_PLUGIN_FILE, "RUNNER = 2\n")


def push_to_origin(repo: Path, ref: str) -> None:
    """Push a new commit of the copy of the repository to a ref of origin, such as refs/tags/1.1.0."""
    run_git(repo, *GIT_IDENTITY, "commit", "--allow-empty", "--message", f"Commit of {ref}")
    run_git(repo, "push", "origin", f"HEAD:{ref}")


def set_version(repo: Path, version: str) -> None:
    """Set the version in every file of the copy of the repository that holds it, as `release.py prepare` does."""
    for name in release.VERSION_LINES:
        text = read_copied_file(repo, name)
        (repo / name).write_text(release.replace_version(text, name, version), encoding="utf-8")


def run_release(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the release.py of a repository, or of a copy of it, as the workflows run it."""
    # The notes are UTF-8, whatever the code page of the console.
    environment = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    command = [sys.executable, str(repo / "release.py"), *arguments]
    return subprocess.run(command, cwd=repo, capture_output=True, encoding="utf-8", env=environment, check=False)


def run_prepare(repo: Path, version: str) -> subprocess.CompletedProcess[str]:
    """Run `release.py prepare` on the copy of the repository, on the day of the tests."""
    return run_release(repo, "prepare", version, "--date", DAY)


def run_notes(repo: Path, version: str, *, ref: str) -> subprocess.CompletedProcess[str]:
    """Run `release.py notes`, with the links of the notes pointing to the files of REPOSITORY at `ref`."""
    return run_release(repo, "notes", version, "--ref", ref, "--repository", REPOSITORY)


def run_next_release_notes(repo: Path, *, ref: str) -> subprocess.CompletedProcess[str]:
    """Run `release.py next-release-notes`, with the links pointing to the files of REPOSITORY at `ref`."""
    return run_release(repo, "next-release-notes", "--ref", ref, "--repository", REPOSITORY)


def run_check_branch(repo: Path, branch: str) -> subprocess.CompletedProcess[str]:
    """Run `release.py check-branch` on the copy of the repository, as the CI runs it on the branch of its run."""
    return run_release(repo, "check-branch", branch)


def run_check_pull_request(repo: Path, base: str, head: str) -> subprocess.CompletedProcess[str]:
    """Run `release.py check-pull-request` on the copy of the repository, with the base and the head to compare."""
    return run_release(repo, "check-pull-request", base, head)


def read_copied_file(repo: Path, name: str) -> str:
    """Return the text of a file of the copy of the repository."""
    return (repo / name).read_text(encoding="utf-8")


def write_copied_file(repo: Path, name: str, text: str) -> None:
    """Write a file of the copy of the repository, and its folders."""
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_changelog(repo: Path, changelog: str) -> None:
    """Replace the CHANGELOG of the copy of the repository."""
    write_copied_file(repo, "CHANGELOG.md", changelog)


def read_copied_files(repo: Path) -> dict[str, str]:
    """Return the text of each file of the copy of the repository, by name."""
    return {path.name: path.read_text(encoding="utf-8") for path in repo.iterdir() if path.is_file()}


def test_prepare_sets_the_version_everywhere_and_dates_the_changelog(repo: Path) -> None:
    result = run_prepare(repo, "1.1.0")

    assert (result.returncode, result.stdout) == (0, "Prepared 1.1.0. Run `uv lock`, then commit.\n")
    assert read_json(repo / "plugin.json")["version"] == "1.1.0"
    assert '\nversion = "1.1.0"\n' in read_copied_file(repo, "pyproject.toml")
    assert "\n## 1.1.0 - 2026-12-01\n\n### Clear Datasets by Tags\n" in read_copied_file(repo, "CHANGELOG.md")
    assert "## Unreleased" not in read_copied_file(repo, "CHANGELOG.md")


def test_prepare_changes_only_the_version_lines(repo: Path) -> None:
    before = {name: read_copied_file(repo, name).splitlines() for name in release.VERSION_LINES}

    assert run_prepare(repo, "1.1.0").returncode == 0

    for name, lines in before.items():
        after = read_copied_file(repo, name).splitlines()
        assert len(after) == len(lines)
        assert sum(old != new for old, new in zip(lines, after)) == 1, name


@pytest.mark.parametrize(
    ("version", "changelog", "message"),
    [
        ("1.1", CHANGELOG, r"'1\.1' is not a version such as 1\.1\.0, or 1\.1\.0-beta for a pre-release\."),
        ("v1.1.0", CHANGELOG, r"'v1\.1\.0' is not a version"),
        ("1.1.0beta", CHANGELOG, r"'1\.1\.0beta' is not a version"),
        ("1.1.0-rc.1", CHANGELOG, r"'1\.1\.0-rc\.1' is not a version"),
        ("1.01.0", CHANGELOG, r"'1\.01\.0' is not a version"),
        (
            "1.1.0",
            CHANGELOG.replace("## 1.0.0 - 2026-11-18", "## 1.1.0 - 2026-11-18"),
            r"CHANGELOG\.md already has a section for 1\.1\.0: choose a new version\.",
        ),
        ("1.1.0", CHANGELOG.replace("## Unreleased", "## Later"), r'no "## Unreleased" section'),
        ("1.1.0", CHANGELOG_WITH_EMPTY_NOTES, r"or it is empty"),
    ],
    ids=[
        "too short",
        "with a v",
        "beta without a dash",
        "another pre-release",
        "a leading zero",
        "a section already",
        "no unreleased section",
        "empty notes of the next release",
    ],
)
def test_prepare_refuses_and_changes_nothing(repo: Path, version: str, changelog: str, message: str) -> None:
    write_changelog(repo, changelog)
    before = read_copied_files(repo)

    result = run_prepare(repo, version)

    assert result.returncode == 1
    assert re.match(rf"error: .*{message}", result.stderr)
    assert read_copied_files(repo) == before


@pytest.mark.parametrize(
    ("current", "version"),
    [
        ("1.0.0", "1.0.1"),
        ("1.0.0", "1.1.0-beta"),
        ("1.0.2-beta", "1.0.3-beta"),
        ("1.0.2-beta", "1.0.2"),
        ("1.9.0", "1.10.0"),
    ],
)
def test_a_version_after_the_version_of_the_plugin_is_prepared(repo: Path, current: str, version: str) -> None:
    set_version(repo, current)

    assert run_prepare(repo, version).returncode == 0

    assert read_json(repo / "plugin.json")["version"] == version
    assert f"\n## {version} - 2026-12-01\n" in read_copied_file(repo, "CHANGELOG.md")


@pytest.mark.parametrize(
    ("current", "version"),
    [
        ("1.0.0", "1.0.0"),
        ("1.0.2-beta", "1.0.2-beta"),
        ("1.1.0", "1.1.0-beta"),
        ("1.0.2", "1.0.1"),
        ("1.10.0", "1.9.0"),
    ],
)
def test_a_version_that_is_not_after_the_version_of_the_plugin_is_refused(
    repo: Path, current: str, version: str
) -> None:
    set_version(repo, current)
    before = read_copied_files(repo)

    result = run_prepare(repo, version)

    assert result.returncode == 1
    assert result.stderr == (
        f"error: {version} is not after {current}, the version of plugin.json. Choose a later version: "
        "a pre-release such as 1.1.0-beta comes before 1.1.0.\n"
    )
    assert read_copied_files(repo) == before


@pytest.mark.parametrize(
    ("ref", "message"),
    [
        ("refs/tags/1.1.0", "The tag 1.1.0 exists: 1.1.0 is released, or abandoned. Choose a new version."),
        (
            "refs/heads/release/1.1.0",
            "The branch release/1.1.0 exists: close its release pull request and delete the branch, "
            "then prepare 1.1.0 again.",
        ),
    ],
    ids=["its tag", "its release branch"],
)
def test_a_version_whose_tag_or_release_branch_exists_is_refused(repo: Path, ref: str, message: str) -> None:
    push_to_origin(repo, ref)
    before = read_copied_files(repo)

    result = run_prepare(repo, "1.1.0")

    assert (result.returncode, result.stderr) == (1, f"error: {message}\n")
    assert read_copied_files(repo) == before


def test_the_tag_and_the_release_branch_of_a_pre_release_do_not_block_its_version(repo: Path) -> None:
    push_to_origin(repo, "refs/tags/1.1.0-beta")
    push_to_origin(repo, "refs/heads/release/1.1.0-beta")

    assert run_prepare(repo, "1.1.0").returncode == 0


def test_prepare_refuses_when_it_cannot_read_the_tags_and_branches_of_origin(repo: Path) -> None:
    run_git(repo, "remote", "remove", "origin")
    before = read_copied_files(repo)

    result = run_prepare(repo, "1.1.0")

    assert result.returncode == 1
    assert result.stderr.startswith("error: Cannot read the tags and branches of origin: fatal: ")
    assert read_copied_files(repo) == before


def test_the_notes_are_the_section_of_the_version_with_absolute_links(repo: Path) -> None:
    result = run_notes(repo, "1.0.0", ref="1.0.0")

    assert (result.returncode, result.stdout) == (
        0,
        "First version, under the [MIT License](https://github.com/Zyniel/repo/blob/1.0.0/LICENSE). "
        "Details on [GitHub](https://github.com/x/y), [below](#below).\n",
    )


def test_the_notes_of_a_version_stop_at_the_next_section(repo: Path) -> None:
    write_changelog(repo, PREPARED_CHANGELOG)

    notes = run_notes(repo, "1.1.0", ref="release/1.1.0").stdout

    assert notes.startswith("### Clear Datasets by Tags\n")
    assert "First version" not in notes
    assert "](https://github.com/Zyniel/repo/blob/release/1.1.0/docs/macros/" in notes


def test_the_notes_of_1_0_0_are_not_those_of_a_pre_release(repo: Path) -> None:
    write_changelog(repo, CHANGELOG.replace("## Unreleased", "## 1.0.0-beta - 2026-11-01"))

    assert "First version" in run_notes(repo, "1.0.0", ref="1.0.0").stdout
    assert "A fix" in run_notes(repo, "1.0.0-beta", ref="1.0.0-beta").stdout


def test_a_version_without_notes_is_refused(repo: Path) -> None:
    result = run_notes(repo, "1.1.0", ref="main")

    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr == "error: CHANGELOG.md has no section for 1.1.0.\n"


def test_the_notes_of_the_next_release_are_printed_with_absolute_links(repo: Path) -> None:
    # The CI points the links to the commit of its run.
    result = run_next_release_notes(repo, ref="4b825dc")

    assert (result.returncode, result.stdout) == (
        0,
        "### Clear Datasets by Tags\n\n- A fix. See the [user guide](https://github.com/Zyniel/repo/blob/4b825dc/"
        "docs/macros/clear-datasets-by-tags/user-guide.md#select-the-datasets).\n",
    )


@pytest.mark.parametrize("changelog", WITHOUT_NEXT_RELEASE_NOTES)
def test_empty_notes_of_the_next_release_say_so(repo: Path, changelog: str) -> None:
    write_changelog(repo, changelog)

    result = run_next_release_notes(repo, ref="main")

    assert (result.returncode, result.stdout, result.stderr) == (0, EMPTY_NEXT_RELEASE_NOTES, "")


@pytest.mark.parametrize("changelog", WITHOUT_NEXT_RELEASE_NOTES)
def test_a_release_branch_without_notes_of_the_next_release_passes(repo: Path, changelog: str) -> None:
    write_changelog(repo, changelog)

    result = run_check_branch(repo, "release/1.1.0")

    assert (result.returncode, result.stdout) == (0, "release/1.1.0 has no notes of the next release.\n")


def test_a_release_branch_with_notes_of_the_next_release_fails_and_says_to_prepare_again(repo: Path) -> None:
    # A change that reached the branch after Prepare release, under a new "## Unreleased" section.
    write_changelog(repo, PREPARED_CHANGELOG.replace("## 1.1.0", "## Unreleased\n\n- A late change.\n\n## 1.1.0"))

    result = run_check_branch(repo, "release/1.1.0")

    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr == (
        "error: The branch release/1.1.0 has notes of the next release: changes that 1.1.0 would ship untested, "
        "and missing from its notes. Close its release pull request, delete the branch, and prepare 1.1.0 again.\n"
    )


@pytest.mark.parametrize("branch", ["main", "fix/release/1.1.0"])
def test_a_branch_that_is_not_a_release_branch_passes_with_notes_of_the_next_release(repo: Path, branch: str) -> None:
    result = run_check_branch(repo, branch)

    assert (result.returncode, result.stdout) == (
        0,
        f"{branch} is not a release branch: its notes of the next release are not checked.\n",
    )


def test_a_pull_request_that_changes_the_plugin_and_the_notes_of_the_next_release_passes(pull_request: Path) -> None:
    change_plugin(pull_request)
    write_changelog(pull_request, CHANGELOG_WITH_A_NEW_NOTE)
    commit_all(pull_request, "A new option")

    result = run_check_pull_request(pull_request, "main", PULL_REQUEST_BRANCH)

    assert (result.returncode, result.stdout) == (
        0,
        "The pull request changes the plugin, and the notes of the next release.\n",
    )


@pytest.mark.parametrize(
    "changelog",
    [
        pytest.param(CHANGELOG, id="the changelog unchanged"),
        pytest.param(CHANGELOG.replace("First version", "The first version"), id="an older section changed"),
    ],
)
def test_a_pull_request_that_changes_the_plugin_and_not_the_notes_fails_and_names_its_files_and_the_label(
    pull_request: Path, changelog: str
) -> None:
    set_version(pull_request, "1.0.1")  # plugin.json, and pyproject.toml, which the plugin zip does not hold
    change_plugin(pull_request)
    write_copied_file(pull_request, "python-runnables/clear-datasets-by-tags/runnable.json", "{}\n")
    (pull_request / "resource" / "tag_choices.py").unlink()
    write_copied_file(pull_request, "README.md", "# Clear Datasets by Tags, a plugin\n")
    write_changelog(pull_request, changelog)
    commit_all(pull_request, "A change of the plugin")

    result = run_check_pull_request(pull_request, "main", PULL_REQUEST_BRANCH)

    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr == (
        "error: The pull request changes the plugin, and not the notes of the next release. It changes:\n"
        "- plugin.json\n"
        f"- {CHANGED_PLUGIN_FILE}\n"
        "- python-runnables/clear-datasets-by-tags/runnable.json\n"
        "- resource/tag_choices.py\n"
        'Describe the change for users under "## Unreleased" in CHANGELOG.md. If users cannot notice it, add the '
        "label no-changelog to the pull request instead.\n"
    )


@pytest.mark.parametrize(
    ("name", "text"),
    [
        pytest.param("README.md", "# Clear Datasets by Tags, a plugin\n", id="the README"),
        pytest.param("LICENSE", "MIT License, 2026\n", id="the license"),
        pytest.param("docs/development.md", "# Develop\n", id="a doc"),
        pytest.param("resources/notes.md", "Notes\n", id="a folder whose name starts like one of the plugin"),
        pytest.param("CHANGELOG.md", CHANGELOG_WITH_A_NEW_NOTE, id="the notes of the next release only"),
    ],
)
def test_a_pull_request_that_does_not_change_the_plugin_passes_without_a_check_of_its_notes(
    pull_request: Path, name: str, text: str
) -> None:
    write_copied_file(pull_request, name, text)
    commit_all(pull_request, f"A change of {name}")

    result = run_check_pull_request(pull_request, "main", PULL_REQUEST_BRANCH)

    assert (result.returncode, result.stdout) == (0, NOTHING_TO_CHECK)


def test_the_changes_that_main_got_after_the_pull_request_left_it_do_not_count(pull_request: Path) -> None:
    change_plugin(pull_request)
    commit_all(pull_request, "A change of the plugin, without notes")
    run_git(pull_request, "switch", "main")
    # Another pull request, merged into main since: a change of the plugin, with its notes.
    write_copied_file(pull_request, "resource/tag_choices.py", "CHOICES = 2\n")
    write_changelog(pull_request, CHANGELOG_WITH_A_NEW_NOTE)
    commit_all(pull_request, "Another change of the plugin, with its notes")

    result = run_check_pull_request(pull_request, "main", PULL_REQUEST_BRANCH)

    assert result.returncode == 1
    assert f"It changes:\n- {CHANGED_PLUGIN_FILE}\nDescribe" in result.stderr


@pytest.mark.parametrize(
    ("changelog", "returncode"),
    [pytest.param(CHANGELOG, 1, id="without notes"), pytest.param(CHANGELOG_WITH_A_NEW_NOTE, 0, id="with notes")],
)
def test_the_merge_of_a_pull_request_into_its_base_is_checked_against_its_first_parent(
    pull_request: Path, changelog: str, returncode: int
) -> None:
    change_plugin(pull_request)
    write_changelog(pull_request, changelog)
    commit_all(pull_request, "A change of the plugin")
    run_git(pull_request, "switch", "main")
    write_copied_file(pull_request, "docs/development.md", "# Develop\n")
    commit_all(pull_request, "A change of main since")
    # On a pull request, the CI checks out such a merge: its first parent is main, its second the pull request.
    run_git(pull_request, *GIT_IDENTITY, "merge", "--no-ff", "--no-edit", PULL_REQUEST_BRANCH)

    result = run_check_pull_request(pull_request, "HEAD^1", "HEAD")

    assert result.returncode == returncode


def test_the_check_of_a_pull_request_fails_when_git_cannot_compare_its_commits(pull_request: Path) -> None:
    result = run_check_pull_request(pull_request, "main", "no-such-branch")

    assert result.returncode == 1
    assert result.stderr.startswith("error: Cannot compare no-such-branch with main: fatal: ")


def test_the_command_line_reports_an_error_without_a_traceback(repo: Path) -> None:
    result = run_prepare(repo, "1.1")

    assert result.returncode == 1
    assert result.stderr == "error: '1.1' is not a version such as 1.1.0, or 1.1.0-beta for a pre-release.\n"


def test_the_changelog_of_the_repository_can_be_released() -> None:
    # The version of plugin.json has its notes: on main, those of the last release; on a release branch, those that
    # Prepare release dated.
    version = read_json(ROOT / "plugin.json")["version"]

    result = run_notes(ROOT, version, ref="main")

    assert result.returncode == 0
    assert result.stdout.strip()
