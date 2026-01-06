#!/bin/bash
# Uninstall script for Zoom Elgato Light Automation

PLIST_DST="$HOME/Library/LaunchAgents/com.local.zoom-elgato-light.plist"

echo "Uninstalling Zoom Elgato Light Automation..."

# Unload the agent
launchctl unload "$PLIST_DST" 2>/dev/null || true
echo "  Unloaded LaunchAgent"

# Remove the plist
rm -f "$PLIST_DST"
echo "  Removed plist"

echo ""
echo "Done. The automation has been stopped and removed from login items."
echo "The script files remain intact. To reinstall, run ./install.sh"
