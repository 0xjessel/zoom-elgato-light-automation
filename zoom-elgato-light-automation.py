#!/usr/bin/env python3
"""
Zoom Elgato Light Automation

Monitors macOS camera activation and controls Elgato Key Lights.
When camera turns on → lights turn on
When camera turns off → lights turn off
"""

import json
import logging
import os
import subprocess
import urllib.request
import urllib.error
import sys
from pathlib import Path

# Configuration via environment variables
# ELGATO_LIGHT_IPS: comma-separated list of IP addresses (required)
# ELGATO_LIGHT_PORT: port number (optional, default 9123)
LIGHT_IPS_ENV = os.environ.get("ELGATO_LIGHT_IPS", "")
LIGHT_IPS = [ip.strip() for ip in LIGHT_IPS_ENV.split(",") if ip.strip()]
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


def set_lights(on: bool) -> None:
    """Turn all lights on or off."""
    state = "ON" if on else "OFF"
    log.info(f"Turning lights {state}")

    for ip in LIGHT_IPS:
        url = f"http://{ip}:{PORT}/elgato/lights"
        data = json.dumps({"lights": [{"on": 1 if on else 0}]}).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            method="PUT",
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                log.info(f"  {ip}: {state} - OK")
        except urllib.error.URLError as e:
            log.warning(f"  {ip}: FAILED - {e}")
        except Exception as e:
            log.warning(f"  {ip}: FAILED - {e}")


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

    if not LIGHT_IPS:
        log.error("No light IPs configured!")
        log.error("Set ELGATO_LIGHT_IPS environment variable (comma-separated)")
        log.error("Example: export ELGATO_LIGHT_IPS='192.168.1.100,192.168.1.101'")
        sys.exit(1)

    log.info(f"Monitoring lights: {', '.join(LIGHT_IPS)}")
    log.info("=" * 50)

    try:
        monitor_camera()
    except Exception as e:
        log.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
