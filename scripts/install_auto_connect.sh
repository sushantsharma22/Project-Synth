#!/bin/bash
# Install Brain Auto-Connect Service
# Sets up automatic connection on macOS startup

echo "🔧 Installing Project Synth Brain Auto-Connect"
echo "=============================================="
echo ""

# Create logs directory
mkdir -p "$HOME/Documents/project synth/logs"

# Copy plist to LaunchAgents
PLIST_SRC="$HOME/project-synth/com.projectsynth.brainconnection.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.projectsynth.brainconnection.plist"

echo "📋 Installing launch agent..."
cp "$PLIST_SRC" "$PLIST_DST"

# Load the service
echo "🚀 Starting service..."
launchctl unload "$PLIST_DST" 2>/dev/null  # Unload if already loaded
launchctl load "$PLIST_DST"

echo ""
echo "✅ Installation complete!"
echo ""
echo "The Brain connection will now:"
echo "  • Start automatically on macOS startup"
echo "  • Reconnect automatically if disconnected"
echo "  • Run in the background"
echo ""
echo "Management commands:"
echo "  Start:   launchctl start com.projectsynth.brainconnection"
echo "  Stop:    launchctl stop com.projectsynth.brainconnection"
echo "  Status:  launchctl list | grep projectsynth"
echo "  Logs:    tail -f ~/Documents/project\\ synth/logs/brain_connection.log"
echo ""
echo "To uninstall:"
echo "  ./uninstall_auto_connect.sh"
echo ""
