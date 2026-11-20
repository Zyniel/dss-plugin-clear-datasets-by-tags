"""Check a Python file with ruff right after Claude Code edits it: a PostToolUse hook of .claude/settings.json.

It reads the input of the hook on stdin. When the edited file is a Python file of the repository, it runs
ruff check and ruff format --check on it. If one fails, it prints their output and exits with 2: Claude Code
then shows it to Claude, which fixes the file before it goes on. check.py runs the same checks on every file.
"""

import json
import subprocess
import sys
from pathlib import Path

# This file is .claude/hooks/ruff_after_edit.py.
ROOT = Path(__file__).resolve().parents[2]


def run_ruff(arguments: list[str], path: Path) -> subprocess.CompletedProcess[str]:
    """Run ruff on the file, with the settings of the repository and its excluded files."""
    command = [sys.executable, "-m", "ruff", *arguments, "--force-exclude", str(path)]
    return subprocess.run(command, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")


def main() -> int:
    """Check the edited file, and return 2 if ruff finds a problem."""
    hook_input = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    file_path = hook_input.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return 0
    path = Path(file_path).resolve()
    if path.suffix != ".py" or not path.is_relative_to(ROOT) or not path.is_file():
        return 0

    problems = []
    lint = run_ruff(["check", "--quiet"], path)
    if lint.returncode != 0:
        problems.append(lint.stdout + lint.stderr)
    if run_ruff(["format", "--check", "--quiet"], path).returncode != 0:
        problems.append(f"Not formatted: run `uv run ruff format {path.relative_to(ROOT).as_posix()}`.")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
