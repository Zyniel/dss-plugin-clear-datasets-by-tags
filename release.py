"""Release tools: prepare a version, and write the notes of its GitHub release. See docs/releasing.md.

- `uv run python release.py prepare 1.1.0` sets the version in plugin.json and pyproject.toml, and turns the
  "## Unreleased" section of the CHANGELOG into "## 1.1.0 - <today>". Run `uv lock` after it. The README holds no
  version: a release never changes it.
- `uv run python release.py notes 1.1.0 --ref 1.1.0 --repository owner/name` prints the CHANGELOG section of the
  version, with its relative links made absolute, so that they work on the release page. With `--unreleased-first`,
  it prints the "## Unreleased" section when it has changes: the notes of the next release, for a dry run.

The workflows of .github/workflows run them. Nothing here changes a file until every check has passed.
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple, Optional

ROOT = Path(__file__).resolve().parent
CHANGELOG_FILE = "CHANGELOG.md"
UNRELEASED = "## Unreleased"
# A version such as 1.1.0, or 1.1.0-beta for a pre-release.
VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.-]+)?$")
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


def parse_version(version: str) -> tuple[int, int, int]:
    """Return the three numbers of a version.

    :raises ReleaseError: if it is not a version
    """
    match = VERSION.match(version)
    if not match:
        raise ReleaseError(f"{version!r} is not a version such as 1.1.0, or 1.1.0-beta for a pre-release.")
    return int(match[1]), int(match[2]), int(match[3])


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

    :param root: the folder of the repository
    :param today: the date of the section of the version
    :raises ReleaseError: if the version is not one, is lower than the current one or already has a section, if
        the "## Unreleased" section is missing or empty, or if a file has no line or several lines that hold the
        version
    """
    current = json.loads((root / "plugin.json").read_text(encoding="utf-8"))["version"]
    if parse_version(version) < parse_version(current):
        raise ReleaseError(f"{version} is lower than the version of plugin.json, {current}.")

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
    prepare_command = commands.add_parser("prepare", help="Set the version, and date the CHANGELOG.")
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
