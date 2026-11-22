"""Release tools: prepare a version, and write the notes of its GitHub release. See docs/releasing.md.

- `uv run python release.py prepare 1.1.0` sets the version in plugin.json and pyproject.toml, and turns the
  "## Unreleased" section of the CHANGELOG into "## 1.1.0 - <today>". Run `uv lock` after it. The README holds no
  version: a release never changes it. It first checks that it can prepare the version: its form, that it comes
  after the version of plugin.json, that origin has neither its tag nor its release branch, and the CHANGELOG.
- `uv run python release.py notes 1.1.0 --ref 1.1.0 --repository owner/name` prints the CHANGELOG section of the
  version, with its relative links made absolute, so that they work on the release page. With `--unreleased-first`,
  it prints the "## Unreleased" section when it has changes: the notes of the next release, for a dry run.

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
UNRELEASED = "## Unreleased"
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
    ref: str  # A tag or a branch.

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

    branch = f"release/{version}"
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


def release_notes(changelog: str, version: str, links: LinkTarget, unreleased_first: bool = False) -> str:
    """Return the CHANGELOG section of a version, with its relative links pointing to the files of `links`.

    :param changelog: the text of the CHANGELOG
    :param unreleased_first: use the "## Unreleased" section when it has changes, else the section of the version.
        These are the notes of the next release, for a dry run: until the version is prepared, plugin.json still
        gives the last version released.
    :raises ReleaseError: if the CHANGELOG has no section for the version
    """
    unreleased = read_notes(changelog, UNRELEASED) if unreleased_first else None
    notes = unreleased or read_notes(changelog, f"## {version}")
    if notes is None:
        raise ReleaseError(f"{CHANGELOG_FILE} has no section for {version}.")
    return RELATIVE_LINK.sub(lambda match: f"]({links.url(match[1])})", notes)


def main(argv: Optional[list[str]] = None) -> None:
    """Run the command of the command line: prepare, or notes.

    :param argv: the arguments, without the name of the script. Default: those of `sys.argv`.
    :raises SystemExit: with the reason, if the release cannot go on
    """
    parser = argparse.ArgumentParser(description="Prepare a release, or write its notes. See docs/releasing.md.")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_command = commands.add_parser(
        "prepare", help="Check that the version can be prepared, set it, and date the CHANGELOG."
    )
    prepare_command.add_argument("version", help="Such as 1.1.0, or 1.1.0-beta for a pre-release.")
    prepare_command.add_argument("--date", type=datetime.date.fromisoformat, help="Default: today, in UTC.")
    notes_command = commands.add_parser("notes", help="Print the release notes of a version.")
    notes_command.add_argument("version", help="The version whose notes to print.")
    notes_command.add_argument("--ref", required=True, help="The tag or branch the links point to.")
    notes_command.add_argument("--repository", required=True, help="owner/name on GitHub.")
    notes_command.add_argument(
        "--unreleased-first", action="store_true", help='Use "## Unreleased" when it has changes: a dry run.'
    )
    args = parser.parse_args(argv)

    try:
        if args.command == "prepare":
            prepare(ROOT, args.version, args.date or datetime.datetime.now(datetime.timezone.utc).date())
            print(f"Prepared {args.version}. Run `uv lock`, then commit.")
        else:
            changelog = (ROOT / CHANGELOG_FILE).read_text(encoding="utf-8")
            links = LinkTarget(args.repository, args.ref)
            sys.stdout.write(release_notes(changelog, args.version, links, args.unreleased_first))
    except ReleaseError as error:
        raise SystemExit(f"error: {error}") from None


if __name__ == "__main__":
    main()
