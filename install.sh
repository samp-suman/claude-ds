#!/usr/bin/env bash
# DataForge Install Script
# Copies all plugin files to ~/.claude/ (global) or <project>/.claude/ (project-level)
#
# Usage:
#   bash install.sh                          # Install globally (system python)
#   bash install.sh --venv                   # Install globally + create virtual env
#   bash install.sh --project [path]         # Install to <path>/.claude/ (default: current dir)
#   bash install.sh --project [path] --venv  # Project-level + virtual env
#   bash install.sh --uninstall              # Remove from ~/.claude/
#   bash install.sh --uninstall --project [path]  # Remove from <path>/.claude/
#   bash install.sh --reset-kb               # Wipe knowledge base and re-seed

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
PROJECT_MODE=false
USE_VENV=false
VENV_DIR="$HOME/.claude/dataforge/claude-ds-env"

# Parse arguments
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  case "${args[$i]}" in
    --project)
      PROJECT_MODE=true
      NEXT="${args[$((i+1))]:-}"
      if [[ -n "$NEXT" && "$NEXT" != --* ]]; then
        PROJECT_PATH="$NEXT"
        i=$((i+1))
      else
        PROJECT_PATH="$(pwd)"
      fi
      PROJECT_PATH="$(cd "$PROJECT_PATH" 2>/dev/null && pwd)" || {
        echo "Error: directory '$PROJECT_PATH' does not exist"
        exit 1
      }
      CLAUDE_DIR="$PROJECT_PATH/.claude"
      ;;
    --venv)
      USE_VENV=true
      ;;
  esac
done

# --- reset-kb ---------------------------------------------------------------
if [[ " ${args[*]} " == *" --reset-kb "* ]]; then
  KB_DIR="$HOME/.claude/dataforge/knowledge"
  echo "Resetting DataForge knowledge base..."
  if [[ -d "$KB_DIR" ]]; then
    rm -rf "$KB_DIR"
    echo "Cleared: $KB_DIR/"
  fi
  mkdir -p "$KB_DIR"
  # Use dfpython wrapper (respects venv if installed)
  DFPYTHON="$HOME/.claude/dataforge/dfpython"
  if [[ -x "$DFPYTHON" ]]; then
    PYCMD="bash $DFPYTHON"
  else
    PYCMD="python3"
  fi
  SCRIPT_DIR="$HOME/.claude/scripts"
  if [[ -f "$SCRIPT_DIR/seed_kb.py" ]]; then
    $PYCMD "$SCRIPT_DIR/seed_kb.py" --force || echo "(seed_kb.py failed)"
    $PYCMD "$SCRIPT_DIR/seed_sources.py" || echo "(seed_sources.py failed)"
    echo "Knowledge base re-seeded from baseline."
  else
    echo "Scripts not installed. Run 'bash install.sh' first, then 'bash install.sh --reset-kb'."
  fi
  exit 0
fi

# --- uninstall ---------------------------------------------------------------
if [[ " ${args[*]} " == *" --uninstall "* ]]; then
  echo "Uninstalling DataForge from $CLAUDE_DIR ..."
  for skill_dir in dataforge dataforge-preprocess dataforge-eda dataforge-modeling \
                   dataforge-experiment dataforge-deploy dataforge-report \
                   dataforge-analysis dataforge-pipeline \
                   dataforge-learn dataforge-knowledge; do
    rm -rf "$CLAUDE_DIR/skills/$skill_dir"
  done
  rm -f "$CLAUDE_DIR/agents/"df-*.md
  rm -rf "$CLAUDE_DIR/scripts"
  rm -rf "$CLAUDE_DIR/references"
  rm -rf "$CLAUDE_DIR/schema"
  rm -rf "$CLAUDE_DIR/hooks"
  rm -f "$HOME/.claude/dataforge/dfpython"
  if [[ "$PROJECT_MODE" == true ]]; then
    rmdir "$CLAUDE_DIR/skills" "$CLAUDE_DIR/agents" "$CLAUDE_DIR" 2>/dev/null || true
    echo "DataForge uninstalled from project: $PROJECT_PATH"
  else
    echo "Note: ~/.claude/dataforge/ preserved (live KB, config, venv). Delete manually if needed."
    echo "  To also remove the virtual env: rm -rf ~/.claude/dataforge/claude-ds-env"
    echo "DataForge uninstalled."
  fi
  exit 0
fi

# --- install -----------------------------------------------------------------
echo "Installing DataForge to $CLAUDE_DIR ..."
if [[ "$PROJECT_MODE" == true ]]; then
  echo "Mode: project-level (only available in $PROJECT_PATH)"
else
  echo "Mode: global (available in all projects)"
fi

# Create destination directories
mkdir -p "$CLAUDE_DIR/agents"
mkdir -p "$CLAUDE_DIR/scripts"
mkdir -p "$CLAUDE_DIR/references"
mkdir -p "$CLAUDE_DIR/schema"
mkdir -p "$CLAUDE_DIR/hooks"
mkdir -p "$HOME/.claude/dataforge"

# --- virtual env -------------------------------------------------------------
if [[ "$USE_VENV" == true ]]; then
  echo ""
  echo "Setting up virtual environment at $VENV_DIR ..."
  if [[ -d "$VENV_DIR" ]]; then
    echo "  Virtual env already exists — upgrading packages..."
  else
    python3 -m venv "$VENV_DIR"
    echo "  Created: $VENV_DIR"
  fi
  # Activate and install
  if [[ -f "$VENV_DIR/bin/pip" ]]; then
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    "$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt" -q
  elif [[ -f "$VENV_DIR/Scripts/pip.exe" ]]; then
    "$VENV_DIR/Scripts/pip.exe" install --upgrade pip -q
    "$VENV_DIR/Scripts/pip.exe" install -r "$REPO_DIR/requirements.txt" -q
  fi
  echo "  Dependencies installed into virtual env."
fi

# Install dfpython wrapper (always — falls back to system python3 if no venv)
cp "$REPO_DIR/scripts/dfpython" "$HOME/.claude/dataforge/dfpython"
chmod +x "$HOME/.claude/dataforge/dfpython"

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

# Bootstrap knowledge base (KB is always in ~/.claude/)
KB_DIR="$HOME/.claude/dataforge/knowledge"
mkdir -p "$KB_DIR"
# Use dfpython wrapper for seeding (picks up venv if just created)
DFPYTHON="$HOME/.claude/dataforge/dfpython"
bash "$DFPYTHON" "$CLAUDE_DIR/scripts/seed_kb.py" --quiet || echo "(seed_kb.py skipped)"
bash "$DFPYTHON" "$CLAUDE_DIR/scripts/seed_sources.py" >/dev/null || echo "(seed_sources.py skipped)"

# For project-level installs, add .claude/ to .gitignore if not already there
if [[ "$PROJECT_MODE" == true ]]; then
  GITIGNORE="$PROJECT_PATH/.gitignore"
  if [[ -f "$GITIGNORE" ]]; then
    if ! grep -qx '.claude/' "$GITIGNORE" 2>/dev/null; then
      echo '.claude/' >> "$GITIGNORE"
      echo "Added .claude/ to $GITIGNORE"
    fi
  else
    echo '.claude/' > "$GITIGNORE"
    echo "Created $GITIGNORE with .claude/ entry"
  fi
fi

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
echo "  Python:     $HOME/.claude/dataforge/dfpython"
if [[ "$USE_VENV" == true ]]; then
  echo "  Venv:       $VENV_DIR"
fi
echo ""
echo "Next steps:"
if [[ "$USE_VENV" == false ]]; then
  echo "  1. Install Python dependencies (or re-run with --venv):"
  echo "     pip install -r $REPO_DIR/requirements.txt"
  echo ""
fi
echo "  2. Restart Claude Code (or reload the window)"
echo ""
echo "  3. Use DataForge:"
echo "     /dataforge run <dataset.csv> <target_column>"
echo "     /dataforge analyze <dataset.csv>"
echo "     /dataforge eda <dataset.csv>"
echo ""
echo "  4. Refresh the knowledge base from whitelisted sources:"
echo "     /dataforge-learn all"
echo "     /dataforge-knowledge status"
