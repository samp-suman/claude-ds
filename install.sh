#!/usr/bin/env bash
# DataForge Install Script
# Copies all plugin files from the claude-ds development repo to ~/.claude/
#
# Usage:
#   bash install.sh              # Install
#   bash install.sh --uninstall  # Remove DataForge from ~/.claude/
#   bash install.sh --reset-kb   # Wipe knowledge base and re-seed from baseline

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

if [[ "$1" == "--reset-kb" ]]; then
  echo "Resetting DataForge knowledge base..."
  if [[ -d "$CLAUDE_DIR/dataforge/knowledge" ]]; then
    rm -rf "$CLAUDE_DIR/dataforge/knowledge"
    echo "Cleared: $CLAUDE_DIR/dataforge/knowledge/"
  fi
  mkdir -p "$CLAUDE_DIR/dataforge/knowledge"
  if [[ -f "$CLAUDE_DIR/scripts/seed_kb.py" ]]; then
    python3 "$CLAUDE_DIR/scripts/seed_kb.py" --force || echo "(seed_kb.py failed)"
    python3 "$CLAUDE_DIR/scripts/seed_sources.py" || echo "(seed_sources.py failed)"
    echo "Knowledge base re-seeded from baseline."
  else
    echo "Scripts not installed. Run 'bash install.sh' first, then 'bash install.sh --reset-kb'."
  fi
  exit 0
fi

if [[ "$1" == "--uninstall" ]]; then
  echo "Uninstalling DataForge..."
  # Remove skills
  for skill_dir in dataforge dataforge-preprocess dataforge-eda dataforge-modeling \
                   dataforge-experiment dataforge-deploy dataforge-report \
                   dataforge-analysis dataforge-pipeline \
                   dataforge-learn dataforge-knowledge; do
    rm -rf "$CLAUDE_DIR/skills/$skill_dir"
  done
  # Preserve ~/.claude/dataforge/ (live knowledge base + config) across reinstalls.
  echo "Note: ~/.claude/dataforge/ preserved (live KB + config). Delete manually if needed."
  # Remove agents (only df-* to not touch other agents)
  rm -f "$CLAUDE_DIR/agents/"df-*.md
  # Remove shared resources
  rm -rf "$CLAUDE_DIR/scripts"
  rm -rf "$CLAUDE_DIR/references"
  rm -rf "$CLAUDE_DIR/schema"
  rm -rf "$CLAUDE_DIR/hooks"
  echo "DataForge uninstalled."
  exit 0
fi

echo "Installing DataForge to $CLAUDE_DIR ..."

# Create destination directories
mkdir -p "$CLAUDE_DIR/agents"
mkdir -p "$CLAUDE_DIR/scripts"
mkdir -p "$CLAUDE_DIR/references"
mkdir -p "$CLAUDE_DIR/schema"
mkdir -p "$CLAUDE_DIR/hooks"

# Copy all skill directories
for skill_dir in "$REPO_DIR"/skills/*/; do
  skill_name="$(basename "$skill_dir")"
  mkdir -p "$CLAUDE_DIR/skills/$skill_name"
  cp -r "$skill_dir"* "$CLAUDE_DIR/skills/$skill_name/"
done

# Copy agent files
cp "$REPO_DIR/agents/"df-*.md "$CLAUDE_DIR/agents/"

# Copy shared scripts
cp "$REPO_DIR/scripts/"*.py "$CLAUDE_DIR/scripts/"
cp "$REPO_DIR/scripts/README.md" "$CLAUDE_DIR/scripts/" 2>/dev/null || true

# Copy reference docs
cp "$REPO_DIR/references/"*.md "$CLAUDE_DIR/references/"

# Copy schema files
cp "$REPO_DIR/schema/"*.json "$CLAUDE_DIR/schema/"

# Copy hooks
cp "$REPO_DIR/hooks/"* "$CLAUDE_DIR/hooks/"

# Make scripts and hooks executable
chmod +x "$CLAUDE_DIR/scripts/"*.py 2>/dev/null || true
chmod +x "$CLAUDE_DIR/hooks/"*.py 2>/dev/null || true
chmod +x "$CLAUDE_DIR/hooks/"*.sh 2>/dev/null || true

# Bootstrap knowledge base (idempotent; preserves live KB across reinstalls)
mkdir -p "$CLAUDE_DIR/dataforge/knowledge"
python3 "$CLAUDE_DIR/scripts/seed_kb.py" --quiet || echo "(seed_kb.py skipped)"
python3 "$CLAUDE_DIR/scripts/seed_sources.py" >/dev/null || echo "(seed_sources.py skipped)"

echo ""
echo "DataForge installed successfully!"
echo ""
echo "Files installed:"
echo "  Skills:     $CLAUDE_DIR/skills/dataforge*/"
echo "  Agents:     $CLAUDE_DIR/agents/df-*.md"
echo "  Scripts:    $CLAUDE_DIR/scripts/*.py"
echo "  References: $CLAUDE_DIR/references/*.md"
echo "  Schema:     $CLAUDE_DIR/schema/*.json"
echo "  Hooks:      $CLAUDE_DIR/hooks/*"
echo ""
echo "Next steps:"
echo "  1. Install Python dependencies:"
echo "     pip install -r $REPO_DIR/requirements.txt"
echo ""
echo "  2. Restart Claude Code (or reload the window)"
echo ""
echo "  3. Use DataForge:"
echo "     /dataforge run <dataset.csv> <target_column>"
echo "     /dataforge analyze <dataset.csv>"
echo "     /dataforge eda <dataset.csv>"
echo "     /dataforge-preprocess features <dataset.csv> <target>"
echo "     /dataforge-modeling train <dataset.csv> <target>"
echo ""
echo "  4. Refresh the knowledge base from whitelisted sources:"
echo "     /dataforge-learn all"
echo "     /dataforge-knowledge status"
