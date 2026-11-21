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
from typing import Optional

ROOT = Path(__file__).resolve().parent
UNRELEASED = "## Unreleased"
# A version such as 1.1.0, or 1.1.0-beta for a pre-release.
VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.-]+)?$")
# A relative Markdown link: not a URL, and not an anchor of the same page.
RELATIVE_LINK = re.compile(r"\]\((?!https?://|mailto:|#)([^)\s]+)\)")
# The line that holds the version in each file, and how to write it.
VERSION_LINES = {
    "plugin.json": (r'^    "version": "[^"]*",$', '    "version": "{}",'),
    "pyproject.toml": (r'^version = "[^"]*"$', 'version = "{}"'),
}


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


def replace_line(text: str, pattern: str, line: str, file_name: str) -> str:
    """Replace the one line of a text that matches `pattern`.

    :raises ReleaseError: if no line or several lines match
    """
    new_text, count = re.subn(pattern, lambda _: line, text, flags=re.M)
    if count != 1:
        raise ReleaseError(f"{file_name}: expected one line that matches {pattern}, found {count}.")
    return new_text


def prepare(root: Path, version: str, today: datetime.date) -> None:
    """Set the version in every file, and date the "## Unreleased" section of the CHANGELOG with it.

    :raises ReleaseError: if the version is not one, is lower than the current one or already has a section, or
        if the "## Unreleased" section is missing or empty
    """
    current = json.loads((root / "plugin.json").read_text(encoding="utf-8"))["version"]
    if parse_version(version) < parse_version(current):
        raise ReleaseError(f"{version} is lower than the version of plugin.json, {current}.")

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if changelog_section(changelog, f"## {version}") is not None:
        raise ReleaseError(f"CHANGELOG.md already has a section for {version}: choose a new version.")
    unreleased = changelog_section(changelog, UNRELEASED)
    if unreleased is None or not unreleased.strip():
        raise ReleaseError(f'CHANGELOG.md has no "{UNRELEASED}" section, or it is empty: describe the changes there.')

    new_texts = {"CHANGELOG.md": replace_line(changelog, rf"^{UNRELEASED}$", f"## {version} - {today}", "CHANGELOG.md")}
    for file_name, (pattern, line) in VERSION_LINES.items():
        text = (root / file_name).read_text(encoding="utf-8")
        new_texts[file_name] = replace_line(text, pattern, line.format(version), file_name)
    for file_name, text in new_texts.items():
        (root / file_name).write_text(text, encoding="utf-8")


def release_notes(changelog: str, version: str, ref: str, repository: str, unreleased_first: bool = False) -> str:
    """Return the CHANGELOG section of a version, with its relative links pointing to the files at `ref` on GitHub.

    :param unreleased_first: use the "## Unreleased" section when it has changes, else the section of the version.
        These are the notes of the next release, for a dry run: until the version is prepared, plugin.json still
        gives the last version released.
    :raises ReleaseError: if the CHANGELOG has no section for the version
    """
    unreleased = changelog_section(changelog, UNRELEASED) if unreleased_first else None
    section = unreleased if unreleased and unreleased.strip() else changelog_section(changelog, f"## {version}")
    if section is None or not section.strip():
        raise ReleaseError(f"CHANGELOG.md has no section for {version}.")
    base = f"https://github.com/{repository}/blob/{ref}/"
    return RELATIVE_LINK.sub(lambda match: f"]({base}{match[1]})", section)


def main(argv: Optional[list[str]] = None) -> None:
    """Run the command of the command line: prepare, or notes.

    :raises SystemExit: with the reason, if the release cannot go on
    """
    parser = argparse.ArgumentParser(description="Prepare a release, or write its notes. See docs/releasing.md.")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_command = commands.add_parser("prepare", help="Set the version, and date the CHANGELOG.")
    prepare_command.add_argument("version", help="Such as 1.1.0, or 1.1.0-beta for a pre-release.")
    prepare_command.add_argument("--date", type=datetime.date.fromisoformat, help="Default: today, in UTC.")
    notes_command = commands.add_parser("notes", help="Print the release notes of a version.")
    notes_command.add_argument("version")
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
            changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
            sys.stdout.write(release_notes(changelog, args.version, args.ref, args.repository, args.unreleased_first))
    except ReleaseError as error:
        raise SystemExit(f"error: {error}") from None


if __name__ == "__main__":
    main()
