#!/bin/bash
# Repo Explainer Installer
# One-click install for the Claude Code skill

set -e

SKILL_DIR="$HOME/.claude/skills/repo-explainer"
REPO_URL="https://raw.githubusercontent.com/johnpsasser/repo-explainer/main"

echo "Installing Repo Explainer skill for Claude Code..."
echo ""

# Create skill directory
mkdir -p "$SKILL_DIR"

# Download skill files
echo "Downloading skill files..."
curl -sL "$REPO_URL/SKILL.md" -o "$SKILL_DIR/SKILL.md"
curl -sL "$REPO_URL/generate.py" -o "$SKILL_DIR/generate.py"
curl -sL "$REPO_URL/requirements.txt" -o "$SKILL_DIR/requirements.txt"
chmod +x "$SKILL_DIR/generate.py"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q -r "$SKILL_DIR/requirements.txt"

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo ""
    echo "Warning: ffmpeg not found."
    echo "Install it with: brew install ffmpeg (macOS) or sudo apt install ffmpeg (Linux)"
    echo ""
fi

# Check for API keys
MISSING_KEYS=false

if [ -z "$GEMINI_API_KEY" ]; then
    MISSING_KEYS=true
fi

if [ -z "$ELEVENLABS_API_KEY" ]; then
    MISSING_KEYS=true
fi

if [ "$MISSING_KEYS" = true ]; then
    echo ""
    echo "---"
    echo "Almost done! You need to set your API keys."
    echo ""

    if [ -z "$GEMINI_API_KEY" ]; then
        echo "1. Get your Gemini API key at: https://aistudio.google.com/apikey"
        echo "   Add this to your ~/.zshrc or ~/.bashrc:"
        echo "   export GEMINI_API_KEY=\"your-gemini-key-here\""
        echo ""
    fi

    if [ -z "$ELEVENLABS_API_KEY" ]; then
        echo "2. Get your ElevenLabs API key at: https://elevenlabs.io"
        echo "   Add this to your ~/.zshrc or ~/.bashrc:"
        echo "   export ELEVENLABS_API_KEY=\"your-elevenlabs-key-here\""
        echo ""
    fi

    echo "3. Then run: source ~/.zshrc"
    echo "---"
else
    echo "API keys are already set."
fi

echo ""
echo "Installation complete!"
echo "Restart Claude Code to use the /repo-explainer skill."
echo ""
echo "Usage:"
echo "  /repo-explainer https://github.com/username/repo"
echo "  /repo-explainer ~/path/to/local/repo --preview"
echo ""
