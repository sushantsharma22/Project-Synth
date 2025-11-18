#!/bin/bash
# Uninstall Brain Auto-Connect Service

echo "🗑️  Uninstalling Project Synth Brain Auto-Connect"
echo "==============================================="
echo ""

PLIST_DST="$HOME/Library/LaunchAgents/com.projectsynth.brainconnection.plist"

if [ -f "$PLIST_DST" ]; then
    echo "Stopping service..."
    launchctl unload "$PLIST_DST"
    
    echo "Removing launch agent..."
    rm "$PLIST_DST"
    
    echo ""
    echo "✅ Uninstallation complete!"
    echo ""
    echo "The Brain connection will no longer auto-start."
    echo "You can still connect manually with:"
    echo "  ./connect_brain_auto.sh"
else
    echo "❌ Service not installed"
fi
echo ""
