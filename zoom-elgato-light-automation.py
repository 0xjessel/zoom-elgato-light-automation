#!/usr/bin/env python3
"""
Zoom Elgato Light Automation

Monitors macOS camera activation and controls Elgato Key Lights.
When camera turns on → lights turn on (with configured brightness/temperature)
When camera turns off → lights turn off
"""

import json
import logging
import os
import subprocess
import urllib.request
import urllib.error
import sys
from dataclasses import dataclass
from pathlib import Path

# Configuration via environment variables
# ELGATO_LIGHTS: comma-separated list of IP:BRIGHTNESS:TEMPERATURE
#   Example: 192.168.1.100:15:4200,192.168.1.101:10:4200
# ELGATO_LIGHT_PORT: port number (optional, default 9123)
PORT = int(os.environ.get("ELGATO_LIGHT_PORT", "9123"))

# Set up logging
LOG_FILE = Path.home() / "Library" / "Logs" / "zoom-elgato-light-automation.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


@dataclass
class LightConfig:
    """Configuration for a single Elgato Key Light."""
    ip: str
    brightness: int  # 0-100
    temperature: int  # Kelvin (2900-7000)

    @property
    def temperature_mireds(self) -> int:
        """Convert Kelvin to mireds for Elgato API."""
        # Elgato API uses mireds = 1,000,000 / Kelvin
        # Clamp to valid range (143-344 mireds = 7000K-2900K)
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
            # Just IP, use defaults
            lights.append(LightConfig(ip=parts[0], brightness=100, temperature=5600))
        elif len(parts) == 3:
            # IP:BRIGHTNESS:TEMPERATURE
            lights.append(LightConfig(
                ip=parts[0],
                brightness=int(parts[1]),
                temperature=int(parts[2])
            ))
        else:
            log.warning(f"Invalid light config: {entry} (expected IP:BRIGHTNESS:TEMPERATURE)")

    return lights


# Parse configuration at startup
LIGHTS = parse_lights_config()


def set_lights(on: bool) -> None:
    """Turn all lights on or off with their configured brightness/temperature."""
    state = "ON" if on else "OFF"
    log.info(f"Turning lights {state}")

    for light in LIGHTS:
        url = f"http://{light.ip}:{PORT}/elgato/lights"

        if on:
            # Turn on with brightness and temperature
            payload = {
                "lights": [{
                    "on": 1,
                    "brightness": light.brightness,
                    "temperature": light.temperature_mireds
                }]
            }
        else:
            # Just turn off
            payload = {"lights": [{"on": 0}]}

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            method="PUT",
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if on:
                    log.info(f"  {light.ip}: {state} (brightness={light.brightness}%, temp={light.temperature}K) - OK")
                else:
                    log.info(f"  {light.ip}: {state} - OK")
        except urllib.error.URLError as e:
            log.warning(f"  {light.ip}: FAILED - {e}")
        except Exception as e:
            log.warning(f"  {light.ip}: FAILED - {e}")


def monitor_camera() -> None:
    """Monitor camera events and control lights."""
    log.info("Starting camera monitor...")

    camera_on = False

    cmd = [
        "log", "stream",
        "--predicate", 'subsystem == "com.apple.cmio"',
        "--style", "compact",
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    try:
        for line in process.stdout:
            # Detect camera start
            if "CMIODeviceStartStream" in line:
                if not camera_on:
                    camera_on = True
                    log.info("Camera ON detected")
                    set_lights(on=True)

            # Detect camera stop
            elif "CMIODeviceStopStream" in line:
                if camera_on:
                    camera_on = False
                    log.info("Camera OFF detected")
                    set_lights(on=False)

    except KeyboardInterrupt:
        log.info("Received interrupt, shutting down...")
    except Exception as e:
        log.error(f"Error in monitor loop: {e}")
    finally:
        process.terminate()
        process.wait()
        log.info("Camera monitor stopped")


def main():
    log.info("=" * 50)
    log.info("Zoom Elgato Light Automation starting")

    if not LIGHTS:
        log.error("No lights configured!")
        log.error("Set ELGATO_LIGHTS environment variable")
        log.error("Format: IP:BRIGHTNESS:TEMPERATURE (comma-separated)")
        log.error("Example: ELGATO_LIGHTS='192.168.1.100:50:4500,192.168.1.101:75:5000'")
        sys.exit(1)

    for light in LIGHTS:
        log.info(f"  Light: {light.ip} (brightness={light.brightness}%, temp={light.temperature}K)")
    log.info("=" * 50)

    try:
        monitor_camera()
    except Exception as e:
        log.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
