#!/bin/bash
# Sharingan — Autonomous Testing Agent for Claude Code
# Install: curl -fsSL https://raw.githubusercontent.com/ctoapplymatic/sharingan/main/install.sh | bash

set -e

echo ""
echo "  SHARINGAN — The eye that sees all bugs"
echo "  Autonomous Testing Agent for Claude Code"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    echo "Install Python 3.10+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python version: $PYTHON_VERSION"

# Install the package
echo ""
echo "  Installing Sharingan..."

if command -v uv &> /dev/null; then
    echo "  Using uv..."
    uv pip install sharingan-autotest
elif command -v pip3 &> /dev/null; then
    pip3 install sharingan
elif command -v pip &> /dev/null; then
    pip install sharingan-autotest
else
    echo "Error: pip not found. Install pip or uv first."
    exit 1
fi

# Install Playwright browsers
echo ""
echo "  Installing Playwright browsers..."
if command -v npx &> /dev/null; then
    npx playwright install chromium
else
    echo "  Warning: npx not found. You'll need to install Playwright browsers manually:"
    echo "    npx playwright install chromium"
fi

# Copy slash commands to project
echo ""
echo "  Installing Claude Code slash commands..."

COMMANDS_DIR=".claude/commands"
mkdir -p "$COMMANDS_DIR"

# Try to find the installed package location
SHARINGAN_DIR=$(python3 -c "import sharingan; import os; print(os.path.dirname(os.path.dirname(sharingan.__file__)))" 2>/dev/null || echo "")

if [ -n "$SHARINGAN_DIR" ] && [ -d "$SHARINGAN_DIR/commands" ]; then
    cp "$SHARINGAN_DIR/commands/"*.md "$COMMANDS_DIR/" 2>/dev/null || true
    echo "  Slash commands installed to $COMMANDS_DIR/"
else
    echo "  Note: Run 'sharingan init' in your project directory to install slash commands."
fi

echo ""
echo "  Sharingan installed successfully!"
echo ""
echo "  Quick start:"
echo "    1. cd your-project"
echo "    2. sharingan init"
echo "    3. Type /sharingan in Claude Code"
echo ""
