#!/usr/bin/env python3
"""
DataForge PostToolUse Hook — Python Code Linter

Fires after every Write or Edit tool call in Claude Code.
Checks if the written file is a Python file inside a DataForge project
(detected by presence of dataforge.config.json in any ancestor directory).
If so, runs pyflakes for syntax and undefined-name checks.

Usage (configured in ~/.claude/settings.json):
    {
      "hooks": {
        "PostToolUse": [{
          "matcher": "Write|Edit",
          "hooks": [{"type": "command", "command": "python3 ~/.claude/skills/dataforge/hooks/post-generate-lint.py \"$FILE_PATH\""}]
        }]
      }
    }

Exit codes:
    0 — Pass (or non-Python file, or non-DataForge project)
    2 — Lint errors found (Claude Code will show error to user)
"""
import subprocess
import sys
from pathlib import Path


def find_dataforge_root(start_path: Path) -> bool:
    """Check if any ancestor directory contains dataforge.config.json."""
    current = start_path.parent
    for _ in range(8):  # Max 8 levels up
        if (current / "dataforge.config.json").exists():
            return True
        parent = current.parent
        if parent == current:
            break
        current = parent
    return False


def main():
    if len(sys.argv) < 2:
        sys.exit(0)

    file_path = sys.argv[1]
    if not file_path:
        sys.exit(0)

    path = Path(file_path)

    # Only lint Python files
    if path.suffix != ".py":
        sys.exit(0)

    # Only lint files inside DataForge projects
    if not find_dataforge_root(path):
        sys.exit(0)

    # Skip DataForge's own scripts (they are already tested)
    if ".claude/skills/dataforge/scripts" in str(path).replace("\\", "/"):
        sys.exit(0)

    # Run pyflakes
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pyflakes", str(path)],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            output = result.stdout.strip() or result.stderr.strip()
            print(f"DataForge lint: Issues in {path.name}:\n{output}", file=sys.stderr)
            sys.exit(2)
    except subprocess.TimeoutExpired:
        # Don't block on timeout
        sys.exit(0)
    except FileNotFoundError:
        # pyflakes not installed — skip silently
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
