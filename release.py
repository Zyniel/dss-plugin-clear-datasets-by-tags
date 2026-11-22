"""Release tools: prepare a version, read one, print notes, check a branch and a pull request. See docs/releasing.md.

- `uv run python release.py prepare 1.1.0` sets the version in plugin.json and pyproject.toml, and turns the
  "## Unreleased" section of the CHANGELOG into "## 1.1.0 - <today>". Run `uv lock` after it. The README holds no
  version: a release never changes it. It first checks that it can prepare the version: its form, that it comes
  after the version of plugin.json, that origin has neither its tag nor its release branch, and the CHANGELOG.
- `uv run python release.py version` prints the version of the plugin, from plugin.json, and
  `uv run python release.py is-pre-release 1.1.0-beta` prints true for a pre-release, false for a version without
  -beta. The Release workflow publishes the version of the plugin, as a pre-release when it is one.
- `uv run python release.py notes 1.1.0 --ref 1.1.0 --repository owner/name` prints the notes of the version: its
  section of the CHANGELOG, with its relative links made absolute, so that they work on the release page.
- `uv run python release.py next-release-notes --ref main --repository owner/name` prints the notes of the next
  release, the "## Unreleased" section, the same way, or says that they are empty. The CI writes them to the summary
  of each run.
- `uv run python release.py check-branch release/1.1.0` fails when a release branch has notes of the next release:
  changes that reached it after Prepare release dated the notes. Any other branch passes.
- `uv run python release.py check-pull-request main HEAD` fails when the changes of HEAD since it left main change
  the plugin, and not the notes of the next release. The CI runs it on each pull request, but those of a release
  branch and those with the label no-changelog.

The workflows of .github/workflows run them. Nothing here changes a file until every check has passed.
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, NamedTuple, Optional

from build_plugin_zip import PLUGIN_FOLDERS

ROOT = Path(__file__).resolve().parent
CHANGELOG_FILE = "CHANGELOG.md"
# The heading of the notes of the next release.
UNRELEASED = "## Unreleased"
# The branch of a release pull request is this prefix and the version, such as release/1.1.0. prepare-release.yml
# names the branch with the same prefix, and ci.yml and release.yml check it.
RELEASE_BRANCH_PREFIX = "release/"
# The files and folders of the plugin: what the plugin zip holds, but its README and its license. A pull request that
# changes them adds to the notes of the next release. A folder ends with "/", for git and for the reader.
PLUGIN_PATHS = ["plugin.json", *(f"{folder}/" for folder in PLUGIN_FOLDERS)]
# The label of a pull request whose change users cannot notice: the CI does not check its notes. ci.yml checks the
# same name. It is the name of the label on GitHub, so it stays: "changelog" means the file CHANGELOG.md, not the notes.
NO_CHANGELOG_LABEL = "no-changelog"
# A version is X.Y.Z, or X.Y.Z-beta for a pre-release, and nothing else. As in semantic versioning, which Dataiku
# recommends for a plugin, a number has no leading zero.
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-beta)?")
# A relative Markdown link: not a URL, and not an anchor of the same page.
RELATIVE_LINK = re.compile(r"\]\((?!https?://|mailto:|#)([^)\s]+)\)")


class VersionLine(NamedTuple):
    """The line that holds the version in a file: the pattern that finds it, and the template that writes it."""

    pattern: str
    template: str


# The line that holds the version in each file.
VERSION_LINES = {
    "plugin.json": VersionLine(r'^    "version": "[^"]*",$', '    "version": "{}",'),
    "pyproject.toml": VersionLine(r'^version = "[^"]*"$', 'version = "{}"'),
}


class LinkTarget(NamedTuple):
    """The files that the relative links of the notes point to: those of a repository on GitHub, at a ref."""

    repository: str  # On GitHub: owner/name.
    ref: str  # A tag, a branch or a commit.

    def url(self, path: str) -> str:
        """Return the URL of a file at the ref, from its path relative to the root of the repository."""
        return f"https://github.com/{self.repository}/blob/{self.ref}/{path}"


class VersionOrder(NamedTuple):
    """Where a version comes in the order of versions: by its three numbers, then a pre-release first.

    So 1.0.2-beta comes before 1.0.2, which comes before 1.0.3-beta.
    """

    major: int
    minor: int
    patch: int
    without_beta: bool


class ReleaseError(Exception):
    """The release cannot go on. The message says why, and what to do."""


def parse_version(version: str) -> VersionOrder:
    """Return where a version comes in the order of versions.

    :raises ReleaseError: if it is not a version
    """
    match = VERSION.fullmatch(version)
    if not match:
        raise ReleaseError(f"{version!r} is not a version such as 1.1.0, or 1.1.0-beta for a pre-release.")
    return VersionOrder(int(match[1]), int(match[2]), int(match[3]), without_beta=not match[4])


def read_plugin_version(root: Path) -> str:
    """Return the version of the plugin, from its plugin.json.

    :param root: the folder of the repository
    :raises ReleaseError: if it is not a version
    """
    version: str = json.loads((root / "plugin.json").read_text(encoding="utf-8"))["version"]
    try:
        parse_version(version)
    except ReleaseError as error:
        raise ReleaseError(f"plugin.json: {error}") from None
    return version


def is_pre_release(version: str) -> bool:
    """Return whether a version is a pre-release: X.Y.Z-beta.

    :raises ReleaseError: if it is not a version
    """
    return not parse_version(version).without_beta


def read_git(root: Path, arguments: list[str], failure: str) -> str:
    """Run a git command that reads the repository or its remote, and return what it prints.

    :param root: the folder of the repository
    :param failure: the start of the message of the error, such as "Cannot read the tags and branches of origin"
    :raises ReleaseError: if git fails, with `failure` and what git said
    """
    result = subprocess.run(["git", *arguments], cwd=root, capture_output=True, encoding="utf-8", check=False)
    if result.returncode != 0:
        raise ReleaseError(f"{failure}: {result.stderr.strip()}")
    return result.stdout


def read_remote_refs(root: Path, refs: list[str]) -> set[str]:
    """Return those of `refs`, such as refs/tags/1.1.0, that the remote origin of the repository has.

    :param root: the folder of the repository
    :raises ReleaseError: if git cannot read the refs of origin
    """
    output = read_git(root, ["ls-remote", "origin", *refs], "Cannot read the tags and branches of origin")
    # Each line is "<commit>\t<ref>". git matches the end of a ref, so keep only the refs asked for.
    return {line.partition("\t")[2] for line in output.splitlines()} & set(refs)


def changelog_section(changelog: str, heading: str) -> Optional[str]:
    """Return the text of the section whose heading is `heading`, or starts with `heading` and a space.

    None if there is no such section. The section ends at the next "## " heading.

    :param changelog: the text of the CHANGELOG
    """
    lines: list[str] = []
    found = False
    for line in changelog.splitlines(keepends=True):
        if line.startswith("## "):
            if found:
                break
            title = line.rstrip("\n")
            found = title == heading or title.startswith(heading + " ")
        elif found:
            lines.append(line)
    return "".join(lines).strip("\n") + "\n" if found else None


def read_notes(changelog: str, heading: str) -> Optional[str]:
    """Return the text of a section of the CHANGELOG, or None if it is missing or empty.

    :param changelog: the text of the CHANGELOG
    :param heading: the heading of the section, as for `changelog_section()`
    """
    section = changelog_section(changelog, heading)
    return section if section and section.strip() else None


def replace_line(text: str, pattern: str, line: str, file_name: str) -> str:
    """Replace the one line of a text that matches `pattern`, a regular expression, with `line`.

    :param file_name: the file of the text, for the message of the error
    :raises ReleaseError: if no line or several lines match
    """
    new_text, count = re.subn(pattern, lambda _: line, text, flags=re.M)
    if count != 1:
        raise ReleaseError(f"{file_name}: expected one line that matches {pattern}, found {count}.")
    return new_text


def replace_version(text: str, file_name: str, version: str) -> str:
    """Return the text of a file, with `version` in the line that holds the version.

    :param file_name: a file of VERSION_LINES
    :raises ReleaseError: if no line or several lines hold the version
    """
    version_line = VERSION_LINES[file_name]
    return replace_line(text, version_line.pattern, version_line.template.format(version), file_name)


def prepare(root: Path, version: str, today: datetime.date) -> None:
    """Set the version in every file, and date the "## Unreleased" section of the CHANGELOG with it.

    :param root: the folder of the repository, whose remote origin has the tags and the branches of the versions
    :param today: the date of the section of the version
    :raises ReleaseError: if the version, or the one of plugin.json, is not a version; if the version does not come
        after the current one; if origin has its tag or its release branch, or git cannot read them; if the version
        already has a section; if the "## Unreleased" section is missing or empty; or if a file has no line or several
        lines to replace: the "## Unreleased" heading, or the version
    """
    order = parse_version(version)
    current = read_plugin_version(root)
    if order <= parse_version(current):
        raise ReleaseError(
            f"{version} is not after {current}, the version of plugin.json. Choose a later version: "
            "a pre-release such as 1.1.0-beta comes before 1.1.0."
        )

    branch = f"{RELEASE_BRANCH_PREFIX}{version}"
    tag_ref, branch_ref = f"refs/tags/{version}", f"refs/heads/{branch}"
    remote_refs = read_remote_refs(root, [tag_ref, branch_ref])
    if tag_ref in remote_refs:
        raise ReleaseError(f"The tag {version} exists: {version} is released, or abandoned. Choose a new version.")
    if branch_ref in remote_refs:
        raise ReleaseError(
            f"The branch {branch} exists: close its release pull request and delete the branch, "
            f"then prepare {version} again."
        )

    changelog = read_changelog(root)
    if changelog_section(changelog, f"## {version}") is not None:
        raise ReleaseError(f"{CHANGELOG_FILE} already has a section for {version}: choose a new version.")
    if read_notes(changelog, UNRELEASED) is None:
        raise ReleaseError(
            f'{CHANGELOG_FILE} has no "{UNRELEASED}" section, or it is empty: describe the changes there.'
        )

    new_texts = {CHANGELOG_FILE: replace_line(changelog, rf"^{UNRELEASED}$", f"## {version} - {today}", CHANGELOG_FILE)}
    for file_name in VERSION_LINES:
        text = (root / file_name).read_text(encoding="utf-8")
        new_texts[file_name] = replace_version(text, file_name, version)
    for file_name, text in new_texts.items():
        (root / file_name).write_text(text, encoding="utf-8")


def with_absolute_links(notes: str, links: LinkTarget) -> str:
    """Return notes whose relative links point to the files of `links`, so that they work outside the repository."""
    return RELATIVE_LINK.sub(lambda match: f"]({links.url(match[1])})", notes)


def release_notes(changelog: str, version: str, links: LinkTarget) -> str:
    """Return the notes of a version, its section of the CHANGELOG, with its relative links made absolute.

    :param changelog: the text of the CHANGELOG
    :raises ReleaseError: if the CHANGELOG has no section for the version
    """
    notes = read_notes(changelog, f"## {version}")
    if notes is None:
        raise ReleaseError(f"{CHANGELOG_FILE} has no section for {version}.")
    return with_absolute_links(notes, links)


def next_release_notes(changelog: str, links: LinkTarget) -> str:
    """Return the notes of the next release with their relative links made absolute, or a sentence if they are empty.

    They are empty when nothing changed since the last release, and on a release branch, whose notes Prepare release
    dated.

    :param changelog: the text of the CHANGELOG
    """
    notes = read_notes(changelog, UNRELEASED)
    if notes is None:
        return f'The notes of the next release are empty: {CHANGELOG_FILE} has nothing under "{UNRELEASED}".\n'
    return with_absolute_links(notes, links)


def check_branch(changelog: str, branch: str) -> str:
    """Check that a release branch has no notes of the next release, and return what the check found.

    Prepare release dated them: notes of the next release on its branch are changes that reached it later, and that
    the notes of its version miss. Any other branch passes.

    :param changelog: the text of the CHANGELOG of the branch
    :param branch: such as release/1.1.0, or main
    :raises ReleaseError: if it is a release branch, and its notes of the next release are not empty
    """
    if not branch.startswith(RELEASE_BRANCH_PREFIX):
        return f"{branch} is not a release branch: its notes of the next release are not checked."
    if read_notes(changelog, UNRELEASED) is not None:
        version = branch.removeprefix(RELEASE_BRANCH_PREFIX)
        raise ReleaseError(
            f"The branch {branch} has notes of the next release: changes that {version} would ship untested, and "
            f"missing from its notes. Close its release pull request, delete the branch, and prepare {version} again."
        )
    return f"{branch} has no notes of the next release."


def read_changelog(root: Path) -> str:
    """Return the text of the CHANGELOG of the working tree.

    :param root: the folder of the repository
    """
    return (root / CHANGELOG_FILE).read_text(encoding="utf-8")


def read_changelog_at(root: Path, ref: str) -> str:
    """Return the text of the CHANGELOG at a commit or a branch of the repository.

    :param root: the folder of the git repository
    :raises ReleaseError: if git cannot read it
    """
    return read_git(root, ["show", f"{ref}:{CHANGELOG_FILE}"], f"Cannot read {CHANGELOG_FILE} at {ref}")


def check_pull_request(root: Path, base: str, head: str) -> str:
    """Check that a pull request that changes the plugin adds to the notes of the next release, and say what it found.

    The changes of the pull request are those of `head` since it left `base`, as GitHub shows them: from the last
    commit they have in common. The plugin is what PLUGIN_PATHS names.

    :param root: the folder of the git repository
    :param base: the branch that the pull request merges into, such as main, or a commit
    :param head: the branch of the pull request, or a commit
    :raises ReleaseError: if the pull request changes the plugin and not the notes of the next release; or if git
        cannot compare `head` with `base`, or read the CHANGELOG at their merge base or at `head`
    """
    failure = f"Cannot compare {head} with {base}"
    merge_base = read_git(root, ["merge-base", base, head], failure).strip()
    # -z: the names as they are, one after the other, even with unusual characters. --no-renames: a file moved out of
    # the plugin is a change of the plugin too.
    arguments = ["diff", "--name-only", "--no-renames", "-z", merge_base, head, "--", *PLUGIN_PATHS]
    plugin_files = [name for name in read_git(root, arguments, failure).split("\0") if name]
    if not plugin_files:
        paths = f"{', '.join(PLUGIN_PATHS[:-1])} or {PLUGIN_PATHS[-1]}"
        return f"The pull request changes nothing in {paths}: its notes of the next release are not checked."
    before = read_notes(read_changelog_at(root, merge_base), UNRELEASED)
    after = read_notes(read_changelog_at(root, head), UNRELEASED)
    if before != after:
        return "The pull request changes the plugin, and the notes of the next release."
    files = "".join(f"- {name}\n" for name in plugin_files)
    raise ReleaseError(
        f"The pull request changes the plugin, and not the notes of the next release. It changes:\n{files}"
        f'Describe the change for users under "{UNRELEASED}" in {CHANGELOG_FILE}. If users cannot notice it, add the '
        f"label {NO_CHANGELOG_LABEL} to the pull request instead."
    )


def main(argv: Optional[list[str]] = None) -> None:
    """Run the command of the command line, such as prepare, version or notes: `--help` lists them.

    :param argv: the arguments, without the name of the script. Default: those of `sys.argv`.
    :raises SystemExit: with the reason, if the release cannot go on
    """
    parser = argparse.ArgumentParser(
        description="Prepare a release, read a version, print notes, check a branch or a pull request. "
        "See docs/releasing.md."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_command = commands.add_parser(
        "prepare", help="Check that the version can be prepared, set it, and date the CHANGELOG."
    )
    prepare_command.add_argument("version", help="Such as 1.1.0, or 1.1.0-beta for a pre-release.")
    prepare_command.add_argument("--date", type=datetime.date.fromisoformat, help="Default: today, in UTC.")
    version_command = commands.add_parser("version", help="Print the version of the plugin, from plugin.json.")
    is_pre_release_command = commands.add_parser(
        "is-pre-release", help="Print true if the version is a pre-release, such as 1.1.0-beta, else false."
    )
    is_pre_release_command.add_argument("version", help="Such as 1.1.0, or 1.1.0-beta.")
    notes_command = commands.add_parser("notes", help="Print the notes of a version, with absolute links.")
    notes_command.add_argument("version", help="The version whose notes to print.")
    next_release_notes_command = commands.add_parser(
        "next-release-notes", help='Print the notes of the next release, "## Unreleased", with absolute links.'
    )
    for command in (notes_command, next_release_notes_command):
        command.add_argument("--ref", required=True, help="The tag, branch or commit the links point to.")
        command.add_argument("--repository", required=True, help="owner/name on GitHub.")
    check_branch_command = commands.add_parser(
        "check-branch", help="Fail if a release branch has notes of the next release. Any other branch passes."
    )
    check_branch_command.add_argument("branch", help="Such as release/1.1.0, or main.")
    check_pull_request_command = commands.add_parser(
        "check-pull-request", help="Fail if a pull request changes the plugin, and not the notes of the next release."
    )
    check_pull_request_command.add_argument("base", help="The branch it merges into, such as main, or a commit.")
    check_pull_request_command.add_argument("head", help="Its branch, or a commit, such as HEAD.")

    def run_prepare_command(args: argparse.Namespace) -> str:
        prepare(ROOT, args.version, args.date or datetime.datetime.now(datetime.timezone.utc).date())
        return f"Prepared {args.version}. Run `uv lock`, then commit.\n"

    # The function that runs each command, and returns what it prints. A command missing here fails with an
    # AttributeError, instead of running another one.
    runs: dict[argparse.ArgumentParser, Callable[[argparse.Namespace], str]] = {
        prepare_command: run_prepare_command,
        version_command: lambda _: f"{read_plugin_version(ROOT)}\n",
        # As the Release workflow passes it on: gh release create --prerelease=true.
        is_pre_release_command: lambda args: "true\n" if is_pre_release(args.version) else "false\n",
        notes_command: lambda args: release_notes(
            read_changelog(ROOT), args.version, LinkTarget(args.repository, args.ref)
        ),
        next_release_notes_command: lambda args: next_release_notes(
            read_changelog(ROOT), LinkTarget(args.repository, args.ref)
        ),
        check_branch_command: lambda args: f"{check_branch(read_changelog(ROOT), args.branch)}\n",
        check_pull_request_command: lambda args: f"{check_pull_request(ROOT, args.base, args.head)}\n",
    }
    for command, run in runs.items():
        command.set_defaults(run=run)
    args = parser.parse_args(argv)

    try:
        sys.stdout.write(args.run(args))
    except ReleaseError as error:
        raise SystemExit(f"error: {error}") from None


if __name__ == "__main__":
    main()
