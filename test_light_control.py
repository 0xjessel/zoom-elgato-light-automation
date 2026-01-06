#!/usr/bin/env python3
"""
Elgato Key Light Control Test Script

Tests the HTTP API for controlling Elgato Key Lights.

Set ELGATO_LIGHT_IPS environment variable or create a .env file.
"""

import json
import os
import urllib.request
import urllib.error
import sys

# Load from .env file if it exists
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

# Configuration from environment
LIGHT_IPS_ENV = os.environ.get("ELGATO_LIGHT_IPS", "")
LIGHT_IPS = [ip.strip() for ip in LIGHT_IPS_ENV.split(",") if ip.strip()]
PORT = int(os.environ.get("ELGATO_LIGHT_PORT", "9123"))


def set_light(ip: str, on: bool) -> bool:
    """Turn a light on or off."""
    url = f"http://{ip}:{PORT}/elgato/lights"
    data = json.dumps({"lights": [{"on": 1 if on else 0}]}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method="PUT",
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"  {ip}: {'ON' if on else 'OFF'} - OK")
            return True
    except urllib.error.URLError as e:
        print(f"  {ip}: FAILED - {e}")
        return False
    except Exception as e:
        print(f"  {ip}: FAILED - {e}")
        return False


def get_light_status(ip: str) -> dict | None:
    """Get current light status."""
    url = f"http://{ip}:{PORT}/elgato/lights"

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"  {ip}: Could not get status - {e}")
        return None


def main():
    if not LIGHT_IPS:
        print("ERROR: No light IPs configured!")
        print("")
        print("Option 1: Create a .env file:")
        print("  cp .env.example .env")
        print("  # Edit .env with your light IPs")
        print("")
        print("Option 2: Set environment variable:")
        print("  export ELGATO_LIGHT_IPS='192.168.1.100,192.168.1.101'")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python3 test_light_control.py [on|off|status]")
        sys.exit(1)

    action = sys.argv[1].lower()

    if action == "on":
        print("Turning lights ON...")
        for ip in LIGHT_IPS:
            set_light(ip, on=True)

    elif action == "off":
        print("Turning lights OFF...")
        for ip in LIGHT_IPS:
            set_light(ip, on=False)

    elif action == "status":
        print("Getting light status...")
        for ip in LIGHT_IPS:
            status = get_light_status(ip)
            if status:
                lights = status.get("lights", [])
                if lights:
                    light = lights[0]
                    on_state = "ON" if light.get("on") else "OFF"
                    brightness = light.get("brightness", "?")
                    temp = light.get("temperature", "?")
                    print(f"  {ip}: {on_state} (brightness={brightness}, temp={temp})")

    else:
        print(f"Unknown action: {action}")
        print("Usage: python3 test_light_control.py [on|off|status]")
        sys.exit(1)


if __name__ == "__main__":
    main()
