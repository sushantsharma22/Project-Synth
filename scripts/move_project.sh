#!/bin/bash
# Move project out of ~/Documents to ~/project-synth to avoid macOS privacy restrictions
# Usage: ./move_project.sh

SRC="$HOME/Documents/project synth"
DST="$HOME/project-synth"

if [ ! -d "$SRC" ]; then
  echo "❌ Source directory not found: $SRC"
  exit 1
fi

if [ -d "$DST" ]; then
  echo "❌ Destination already exists: $DST"
  echo "If you really want to overwrite, remove $DST first."
  exit 1
fi

echo "📦 Moving project from: $SRC"
echo "           to: $DST"

# Use rsync to preserve permissions
rsync -av --progress "$SRC/" "$DST/"

if [ $? -ne 0 ]; then
  echo "❌ Failed to copy files"
  exit 1
fi

# Optionally remove source after successful copy
read -p "Remove original folder in Documents? [y/N]: " resp
if [[ "$resp" =~ ^[Yy]$ ]]; then
  rm -rf "$SRC"
  echo "✅ Original removed"
fi

# Fix LaunchAgent plist path if it exists
PLIST_DST="$HOME/Library/LaunchAgents/com.projectsynth.brainconnection.plist"
if [ -f "$PLIST_DST" ]; then
  echo "📋 Updating installed LaunchAgent to new path"
  launchctl unload "$PLIST_DST" 2>/dev/null || true
  cp "$DST/com.projectsynth.brainconnection.plist" "$PLIST_DST"
  launchctl load "$PLIST_DST"
  echo "✅ LaunchAgent updated and reloaded"
fi

# Make sure new scripts are executable
chmod +x "$DST"/*.sh

echo "\n✅ Move complete. New project path: $DST"
