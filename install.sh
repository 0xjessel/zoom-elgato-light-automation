#!/bin/bash
# Install script for Zoom Elgato Light Automation

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_TEMPLATE="$SCRIPT_DIR/com.local.zoom-elgato-light.plist.template"
PLIST_NAME="com.local.zoom-elgato-light.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"
ENV_FILE="$SCRIPT_DIR/.env"

echo "Installing Zoom Elgato Light Automation..."

# Load environment variables from .env if it exists
if [[ -f "$ENV_FILE" ]]; then
    echo "  Loading configuration from .env"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo ""
    echo "ERROR: .env file not found!"
    echo ""
    echo "Please create a .env file with your light IPs:"
    echo "  cp .env.example .env"
    echo "  # Edit .env with your Elgato Key Light IP addresses"
    echo ""
    exit 1
fi

# Validate required environment variables
if [[ -z "$ELGATO_LIGHT_IPS" ]]; then
    echo ""
    echo "ERROR: ELGATO_LIGHT_IPS not set in .env"
    echo ""
    echo "Edit .env and add your light IPs, for example:"
    echo "  ELGATO_LIGHT_IPS=192.168.1.100,192.168.1.101"
    echo ""
    exit 1
fi

echo "  Light IPs: $ELGATO_LIGHT_IPS"

# Find Python path
PYTHON_PATH=$(which python3)
if [[ -z "$PYTHON_PATH" ]]; then
    echo "ERROR: python3 not found in PATH"
    exit 1
fi

# Generate plist from template
SCRIPT_PATH="$SCRIPT_DIR/zoom-elgato-light-automation.py"
LOG_PATH="$HOME/Library/Logs/zoom-elgato-light-automation.log"

echo "  Generating LaunchAgent plist..."
sed -e "s|__PYTHON_PATH__|$PYTHON_PATH|g" \
    -e "s|__SCRIPT_PATH__|$SCRIPT_PATH|g" \
    -e "s|__LIGHT_IPS__|$ELGATO_LIGHT_IPS|g" \
    -e "s|__LOG_PATH__|$LOG_PATH|g" \
    "$PLIST_TEMPLATE" > "$PLIST_DST"

# Unload if already loaded (ignore errors)
launchctl unload "$PLIST_DST" 2>/dev/null || true

# Load the agent
launchctl load -w "$PLIST_DST"
echo "  Loaded LaunchAgent"

# Verify it's running
sleep 1
if launchctl list | grep -q "com.local.zoom-elgato-light"; then
    echo ""
    echo "SUCCESS! Zoom Elgato Light Automation is now running."
    echo "It will start automatically at login."
    echo ""
    echo "To check status:  launchctl list | grep zoom-elgato-light"
    echo "To view logs:     tail -f ~/Library/Logs/zoom-elgato-light-automation.log"
    echo "To stop:          ./uninstall.sh"
else
    echo ""
    echo "Warning: Service may not have started correctly."
    echo "Check logs at: ~/Library/Logs/zoom-elgato-light-automation.log"
fi
