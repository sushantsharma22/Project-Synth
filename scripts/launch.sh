#!/bin/bash

# Kill any existing Synth processes
pkill -9 -f synth 2>/dev/null

# Wait a moment
sleep 1

# Launch Synth from the correct directory
cd /Users/sushant-sharma/project-synth
/Users/sushant-sharma/project-synth/venv/bin/python3 /Users/sushant-sharma/project-synth/synth_native.py

echo "🚀 Synth started! Look for 'Synth' in your menu bar."
