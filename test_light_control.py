#!/usr/bin/env python3
"""
Elgato Key Light Control Test Script

Tests the HTTP API for controlling Elgato Key Lights.

Set ELGATO_LIGHTS environment variable or create a .env file.
Format: IP:BRIGHTNESS:TEMPERATURE (comma-separated)
Example: ELGATO_LIGHTS=192.168.1.100:50:4500,192.168.1.101:75:5000
"""

import json
import os
import urllib.request
import urllib.error
import sys
from dataclasses import dataclass


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


@dataclass
class LightConfig:
    """Configuration for a single Elgato Key Light."""
    ip: str
    brightness: int  # 0-100
    temperature: int  # Kelvin (2900-7000)

    @property
    def temperature_mireds(self) -> int:
        """Convert Kelvin to mireds for Elgato API."""
        mireds = int(1_000_000 / self.temperature)
        return max(143, min(344, mireds))


def parse_lights_config() -> list[LightConfig]:
    """Parse light configuration from environment variables."""
    lights_env = os.environ.get("ELGATO_LIGHTS", "")

    if not lights_env:
        return []

    lights = []
    for entry in lights_env.split(","):
        entry = entry.strip()
        if not entry:
            continue

        parts = entry.split(":")
        if len(parts) == 1:
            lights.append(LightConfig(ip=parts[0], brightness=100, temperature=5600))
        elif len(parts) == 3:
            lights.append(LightConfig(
                ip=parts[0],
                brightness=int(parts[1]),
                temperature=int(parts[2])
            ))
        else:
            print(f"Warning: Invalid config: {entry} (expected IP:BRIGHTNESS:TEMPERATURE)")

    return lights


# Configuration
LIGHTS = parse_lights_config()
PORT = int(os.environ.get("ELGATO_LIGHT_PORT", "9123"))


def set_light(light: LightConfig, on: bool) -> bool:
    """Turn a light on or off with its configured brightness/temperature."""
    url = f"http://{light.ip}:{PORT}/elgato/lights"

    if on:
        payload = {
            "lights": [{
                "on": 1,
                "brightness": light.brightness,
                "temperature": light.temperature_mireds
            }]
        }
    else:
        payload = {"lights": [{"on": 0}]}

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method="PUT",
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if on:
                print(f"  {light.ip}: ON (brightness={light.brightness}%, temp={light.temperature}K) - OK")
            else:
                print(f"  {light.ip}: OFF - OK")
            return True
    except urllib.error.URLError as e:
        print(f"  {light.ip}: FAILED - {e}")
        return False
    except Exception as e:
        print(f"  {light.ip}: FAILED - {e}")
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


def mireds_to_kelvin(mireds: int) -> int:
    """Convert mireds back to Kelvin for display."""
    return int(1_000_000 / mireds)


def main():
    if not LIGHTS:
        print("ERROR: No lights configured!")
        print("")
        print("Option 1: Create a .env file:")
        print("  cp .env.example .env")
        print("  # Edit .env with your light settings")
        print("")
        print("Option 2: Set environment variable:")
        print("  export ELGATO_LIGHTS='192.168.1.100:50:4500,192.168.1.101:75:5000'")
        print("")
        print("Format: IP:BRIGHTNESS:TEMPERATURE (temperature in Kelvin)")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python3 test_light_control.py [on|off|status]")
        sys.exit(1)

    action = sys.argv[1].lower()

    if action == "on":
        print("Turning lights ON with configured brightness/temperature...")
        for light in LIGHTS:
            set_light(light, on=True)

    elif action == "off":
        print("Turning lights OFF...")
        for light in LIGHTS:
            set_light(light, on=False)

    elif action == "status":
        print("Getting light status...")
        for light in LIGHTS:
            status = get_light_status(light.ip)
            if status:
                lights_data = status.get("lights", [])
                if lights_data:
                    data = lights_data[0]
                    on_state = "ON" if data.get("on") else "OFF"
                    brightness = data.get("brightness", "?")
                    temp_mireds = data.get("temperature", 0)
                    temp_kelvin = mireds_to_kelvin(temp_mireds) if temp_mireds else "?"
                    print(f"  {light.ip}: {on_state} (brightness={brightness}%, temp={temp_kelvin}K)")

    else:
        print(f"Unknown action: {action}")
        print("Usage: python3 test_light_control.py [on|off|status]")
        sys.exit(1)


if __name__ == "__main__":
    main()
