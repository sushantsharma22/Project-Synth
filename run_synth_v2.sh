#!/bin/bash
# 🚀 Run Synth with New UI

echo "🚀 Starting Synth Menu Bar (v2.0 - New Text Field)"
echo "=================================================="
echo ""

# Kill any existing instance
echo "🔄 Cleaning up old instances..."
pkill -9 -f synth_native 2>/dev/null
sleep 1

# Check Python
if [ ! -f "./venv/bin/python3" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: python3 -m venv venv"
    exit 1
fi

# Run Synth
echo "✅ Launching Synth..."
echo ""
echo "📋 New Features:"
echo "   • White cursor visible in text field"
echo "   • Scrolling works with trackpad"
echo "   • Multi-line input support"
echo "   • 6th Chat button with context memory"
echo ""
echo "🎯 Look for 'Synth' in your menu bar!"
echo ""

./venv/bin/python3 synth_native.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Synth exited normally"
else
    echo ""
    echo "❌ Synth exited with error code: $?"
fi
