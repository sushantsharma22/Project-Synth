#!/bin/bash
# Start Project Synth with Gemini AI + Tavily
# Run this to launch the autonomous menu bar app

echo "🚀 Starting Project Synth with Gemini AI..."
cd /Users/sushant-sharma/project-synth

# Kill any existing instances
pkill -9 -f synth_native 2>/dev/null

# Start the app in background
./venv/bin/python3 synth_native.py > /tmp/synth.log 2>&1 &

sleep 3

# Check if running
if pgrep -f synth_native > /dev/null; then
    echo "✅ Project Synth is running!"
    echo "🎯 Look for 'Synth' in your menu bar"
    echo ""
    echo "Try these commands:"
    echo "  - What's the weather today?"
    echo "  - Explain quantum computing"
    echo "  - Clean temporary files"
    echo "  - Latest AI news"
    echo ""
    echo "📝 Logs: tail -f /tmp/synth.log"
else
    echo "❌ Failed to start. Check logs:"
    echo "   tail /tmp/synth.log"
fi
