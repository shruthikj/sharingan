#!/bin/bash
#
# Sharingan v0.3 — Installer
#
# One-liner: curl -fsSL https://raw.githubusercontent.com/ctoapplymatic/sharingan/main/install.sh | bash
#
# What this does:
# 1. Clones the sharingan repo to ~/.sharingan/
# 2. Symlinks commands/*.md into ~/.claude/commands/
# 3. Verifies node + playwright are available (or warns)
#
# Sharingan is a pure Claude Code skill — no Python, no pip, no npm package.
# The slash commands live in your global ~/.claude/commands/ and work in any project.

set -e

REPO_URL="${SHARINGAN_REPO:-https://github.com/ctoapplymatic/sharingan.git}"
INSTALL_DIR="${SHARINGAN_INSTALL_DIR:-$HOME/.sharingan}"
CLAUDE_COMMANDS_DIR="${CLAUDE_COMMANDS_DIR:-$HOME/.claude/commands}"

cyan() { printf "\033[36m%s\033[0m\n" "$1"; }
green() { printf "\033[32m%s\033[0m\n" "$1"; }
yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
red() { printf "\033[31m%s\033[0m\n" "$1"; }

echo ""
cyan "  Sharingan v0.3 — installer"
cyan "  the eye that sees all bugs"
echo ""

# Check git
if ! command -v git >/dev/null 2>&1; then
  red "  git not found — install git first"
  exit 1
fi

# Clone or update
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "  → updating existing install at $INSTALL_DIR"
  git -C "$INSTALL_DIR" pull --quiet
else
  echo "  → cloning to $INSTALL_DIR"
  git clone --quiet "$REPO_URL" "$INSTALL_DIR"
fi

# Make scripts executable
chmod +x "$INSTALL_DIR/scripts/"*.js 2>/dev/null || true

# Symlink commands
mkdir -p "$CLAUDE_COMMANDS_DIR"
for cmd in "$INSTALL_DIR"/commands/*.md; do
  name=$(basename "$cmd")
  target="$CLAUDE_COMMANDS_DIR/$name"
  ln -sf "$cmd" "$target"
  echo "  → installed /$( basename "$name" .md)"
done

echo ""

# Check node
if command -v node >/dev/null 2>&1; then
  green "  ✓ node $(node --version)"
else
  yellow "  ! node not found — install Node 18+ before running /sharingan"
fi

# Check playwright (global or project-level)
if command -v npx >/dev/null 2>&1; then
  green "  ✓ npx available (Sharingan installs Playwright per-project as needed)"
else
  yellow "  ! npx not found — install Node + npm"
fi

echo ""
green "  Sharingan installed!"
echo ""
echo "  Get started:"
echo "    1. cd into your project (Next.js, FastAPI, Django, etc.)"
echo "    2. Make sure your dev server(s) are running"
echo "    3. In Claude Code, type: /sharingan"
echo ""
echo "  Other commands:"
echo "    /sharingan-scan      — discovery only (dry run)"
echo "    /sharingan-fix       — fix failures from last run"
echo "    /sharingan-report    — regenerate report"
echo "    /sharingan-resume    — resume after manual login"
echo ""
echo "  Sharingan lives at: $INSTALL_DIR"
echo "  Slash commands at:  $CLAUDE_COMMANDS_DIR"
echo ""
