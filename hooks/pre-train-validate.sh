#!/usr/bin/env bash
# DataForge PreToolUse Hook — Training Guard
#
# Fires before every Bash tool call in Claude Code.
# If the command invokes train.py, checks that data validation has been
# completed (sentinel file .validation_passed must exist).
#
# Configured in ~/.claude/settings.json:
#   "PreToolUse": [{"matcher": "Bash",
#     "hooks": [{"type": "command",
#       "command": "bash ~/.claude/hooks/pre-train-validate.sh"}]}]
#
# The COMMAND environment variable is set by Claude Code to the full Bash command.
#
# Exit codes:
#   0 — Allow command to proceed
#   2 — Block command (Claude Code shows error to user)

COMMAND="${COMMAND:-$1}"

# Only intercept commands that invoke train.py
if [[ "$COMMAND" != *"train.py"* ]]; then
  exit 0
fi

# Extract --output-dir from the command
OUTPUT_DIR=$(echo "$COMMAND" | grep -oP '(?<=--output-dir\s)[\S]+' | head -1)
if [[ -z "$OUTPUT_DIR" ]]; then
  # Can't determine output dir — allow (fail open)
  exit 0
fi

SENTINEL="$OUTPUT_DIR/data/interim/.validation_passed"
if [[ ! -f "$SENTINEL" ]]; then
  echo "DataForge Safety: Cannot train — validation has not been completed." >&2
  echo "Run validation first: /dataforge validate <dataset>" >&2
  echo "Or rerun the full pipeline: /dataforge run <dataset> <target>" >&2
  exit 2
fi

exit 0
