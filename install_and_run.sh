#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  Next Slide — one-time setup + launcher
#  Run this script once to install dependencies, then any time
#  you want to launch the app.
# ─────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "🎙  Next Slide — Setup & Launch"
echo "================================"
echo ""

# ── 1. Check for Python 3 ────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "❌  Python 3 not found."
    echo "    Install it from https://www.python.org/downloads/ and re-run."
    exit 1
fi
PYTHON=$(command -v python3)
echo "✅  Python:  $($PYTHON --version)"

# ── 2. Check / install Homebrew (needed for PortAudio) ───────────
if ! command -v brew &>/dev/null; then
    echo ""
    echo "⚠️  Homebrew not found — installing it now (needed for PortAudio)..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# ── 3. Check / install PortAudio ─────────────────────────────────
if ! brew list portaudio &>/dev/null 2>&1; then
    echo "→  Installing PortAudio via Homebrew..."
    brew install portaudio
else
    echo "✅  PortAudio already installed."
fi

# ── 4. Install Python packages ────────────────────────────────────
echo "→  Installing Python packages (SpeechRecognition, PyAudio)..."
pip3 install --quiet SpeechRecognition PyAudio --break-system-packages 2>/dev/null \
  || pip3 install --quiet SpeechRecognition PyAudio
echo "✅  Python packages ready."

# ── 5. Permissions reminder ───────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ⚠️  First-time macOS permissions required:"
echo ""
echo "  1. Microphone  — allow when macOS prompts you"
echo "  2. Accessibility — to send keystrokes to Google Slides:"
echo "     System Settings → Privacy & Security → Accessibility"
echo "     → add Terminal (or your shell app) and enable it"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀  Launching Next Slide..."
echo ""

cd "$SCRIPT_DIR"
$PYTHON next_slide.py
