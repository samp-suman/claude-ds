#!/usr/bin/env bash
# DataForge Install Script
# Copies skill files and agents from the claude-ds development repo to ~/.claude/
#
# Usage:
#   bash install.sh           # Install
#   bash install.sh --uninstall   # Remove DataForge from ~/.claude/

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SKILLS_DEST="$CLAUDE_DIR/skills/dataforge"
AGENTS_DEST="$CLAUDE_DIR/agents"

if [[ "$1" == "--uninstall" ]]; then
  echo "Uninstalling DataForge..."
  rm -rf "$SKILLS_DEST"
  # Remove only df-* agents (don't touch other agents)
  rm -f "$AGENTS_DEST"/df-*.md
  echo "DataForge uninstalled."
  exit 0
fi

echo "Installing DataForge to $CLAUDE_DIR ..."

# Create destination directories
mkdir -p "$SKILLS_DEST"
mkdir -p "$AGENTS_DEST"

# Copy skill files
cp -r "$REPO_DIR/skills/dataforge/"* "$SKILLS_DEST/"

# Copy agent files
cp "$REPO_DIR/agents/"df-*.md "$AGENTS_DEST/"

# Make scripts executable
chmod +x "$SKILLS_DEST/scripts/"*.py 2>/dev/null || true
chmod +x "$SKILLS_DEST/hooks/"*.py 2>/dev/null || true
chmod +x "$SKILLS_DEST/hooks/"*.sh 2>/dev/null || true

echo ""
echo "DataForge installed successfully!"
echo ""
echo "Files installed:"
echo "  Skills:  $SKILLS_DEST/"
echo "  Agents:  $AGENTS_DEST/df-*.md"
echo ""
echo "Next steps:"
echo "  1. Install Python dependencies:"
echo "     pip install -r $SKILLS_DEST/requirements.txt"
echo ""
echo "  2. Restart Claude Code (or reload the window)"
echo ""
echo "  3. Use DataForge:"
echo "     /dataforge run <dataset.csv> <target_column>"
echo "     /dataforge eda <dataset.csv>"
echo "     /dataforge validate <dataset.csv>"
