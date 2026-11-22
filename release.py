"""Release tools: prepare a version, print notes, and check a release branch. See docs/releasing.md.

- `uv run python release.py prepare 1.1.0` sets the version in plugin.json and pyproject.toml, and turns the
  "## Unreleased" section of the CHANGELOG into "## 1.1.0 - <today>". Run `uv lock` after it. The README holds no
  version: a release never changes it. It first checks that it can prepare the version: its form, that it comes
  after the version of plugin.json, that origin has neither its tag nor its release branch, and the CHANGELOG.
- `uv run python release.py notes 1.1.0 --ref 1.1.0 --repository owner/name` prints the notes of the version: its
  section of the CHANGELOG, with its relative links made absolute, so that they work on the release page.
- `uv run python release.py next-notes --ref main --repository owner/name` prints the notes of the next release, the
  "## Unreleased" section, the same way, or says that they are empty. The CI writes them to the summary of each run.
- `uv run python release.py check-branch release/1.1.0` fails when a release branch has notes of the next release:
  changes that reached it after Prepare release dated the notes. Any other branch passes.

The workflows of .github/workflows run them. Nothing here changes a file until every check has passed.
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, Optional

ROOT = Path(__file__).resolve().parent
CHANGELOG_FILE = "CHANGELOG.md"
# The heading of the notes of the next release.
UNRELEASED = "## Unreleased"
# The branch of a release pull request is this prefix and the version, such as release/1.1.0.
RELEASE_BRANCH_PREFIX = "release/"
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


class ReleaseError(Exception):
    """The release cannot go on. The message says why, and what to do."""


def parse_version(version: str) -> tuple[int, int, int, int]:
    """Return the key that orders versions: the three numbers, then 0 for a pre-release and 1 for a release.

    So 1.0.2-beta comes before 1.0.2, which comes before 1.0.3-beta.

    :raises ReleaseError: if it is not a version
    """
    match = VERSION.fullmatch(version)
    if not match:
        raise ReleaseError(f"{version!r} is not a version such as 1.1.0, or 1.1.0-beta for a pre-release.")
    return int(match[1]), int(match[2]), int(match[3]), 0 if match[4] else 1


def read_remote_refs(root: Path, refs: list[str]) -> set[str]:
    """Return those of `refs`, such as refs/tags/1.1.0, that the remote origin of the repository has.

    :param root: the folder of the repository
    :raises ReleaseError: if git cannot read the refs of origin
    """
    command = ["git", "ls-remote", "origin", *refs]
    result = subprocess.run(command, cwd=root, capture_output=True, encoding="utf-8", check=False)
    if result.returncode != 0:
        raise ReleaseError(f"Cannot read the tags and branches of origin: {result.stderr.strip()}")
    # Each line is "<commit>\t<ref>". git matches the end of a ref, so keep only the refs asked for.
    return {line.partition("\t")[2] for line in result.stdout.splitlines()} & set(refs)


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
    current = json.loads((root / "plugin.json").read_text(encoding="utf-8"))["version"]
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

    changelog = (root / CHANGELOG_FILE).read_text(encoding="utf-8")
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


def make_links_absolute(notes: str, links: LinkTarget) -> str:
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
    return make_links_absolute(notes, links)


def next_release_notes(changelog: str, links: LinkTarget) -> str:
    """Return the notes of the next release with their relative links made absolute, or a sentence if they are empty.

    They are empty when nothing changed since the last release, and on a release branch, whose notes Prepare release
    dated.

    :param changelog: the text of the CHANGELOG
    """
    notes = read_notes(changelog, UNRELEASED)
    if notes is None:
        return f'The notes of the next release are empty: {CHANGELOG_FILE} has nothing under "{UNRELEASED}".\n'
    return make_links_absolute(notes, links)


def check_branch(changelog: str, branch: str) -> str:
    """Check that a release branch has no notes of the next release, and return what the check found.

    Prepare release dated them: notes of the next release on its branch are changes that reached it later, such as a
    pull request merged into main during the release. Any other branch passes.

    :param changelog: the text of the CHANGELOG of the branch
    :param branch: such as release/1.1.0, or main
    :raises ReleaseError: if it is a release branch, and its notes of the next release are not empty
    """
    if not branch.startswith(RELEASE_BRANCH_PREFIX):
        return f"{branch} is not a release branch: its notes of the next release are not checked."
    if read_notes(changelog, UNRELEASED) is not None:
        version = branch[len(RELEASE_BRANCH_PREFIX) :]
        raise ReleaseError(
            f"The branch {branch} has notes of the next release: changes that {version} would ship untested, and "
            f"missing from its notes. Close its release pull request, delete the branch, and prepare {version} again."
        )
    return f"{branch} has no notes of the next release."


def main(argv: Optional[list[str]] = None) -> None:
    """Run the command of the command line: prepare, notes, next-notes or check-branch.

    :param argv: the arguments, without the name of the script. Default: those of `sys.argv`.
    :raises SystemExit: with the reason, if the release cannot go on
    """
    parser = argparse.ArgumentParser(
        description="Prepare a release, print notes, or check a release branch. See docs/releasing.md."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_command = commands.add_parser(
        "prepare", help="Check that the version can be prepared, set it, and date the CHANGELOG."
    )
    prepare_command.add_argument("version", help="Such as 1.1.0, or 1.1.0-beta for a pre-release.")
    prepare_command.add_argument("--date", type=datetime.date.fromisoformat, help="Default: today, in UTC.")
    notes_command = commands.add_parser("notes", help="Print the notes of a version, with absolute links.")
    notes_command.add_argument("version", help="The version whose notes to print.")
    next_notes_command = commands.add_parser(
        "next-notes", help='Print the notes of the next release, "## Unreleased", with absolute links.'
    )
    for command in (notes_command, next_notes_command):
        command.add_argument("--ref", required=True, help="The tag, branch or commit the links point to.")
        command.add_argument("--repository", required=True, help="owner/name on GitHub.")
    check_branch_command = commands.add_parser(
        "check-branch", help="Fail if a release branch has notes of the next release. Any other branch passes."
    )
    check_branch_command.add_argument("branch", help="Such as release/1.1.0, or main.")
    args = parser.parse_args(argv)

    try:
        if args.command == "prepare":
            prepare(ROOT, args.version, args.date or datetime.datetime.now(datetime.timezone.utc).date())
            print(f"Prepared {args.version}. Run `uv lock`, then commit.")
            return
        changelog = (ROOT / CHANGELOG_FILE).read_text(encoding="utf-8")
        if args.command == "notes":
            sys.stdout.write(release_notes(changelog, args.version, LinkTarget(args.repository, args.ref)))
        elif args.command == "next-notes":
            sys.stdout.write(next_release_notes(changelog, LinkTarget(args.repository, args.ref)))
        else:
            print(check_branch(changelog, args.branch))
    except ReleaseError as error:
        raise SystemExit(f"error: {error}") from None


if __name__ == "__main__":
    main()
