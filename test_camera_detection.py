#!/usr/bin/env python3
"""
Camera Detection Test Script

Monitors macOS camera activation/deactivation events using log stream.
Detects CMIODeviceStartStream and CMIODeviceStopStream events.
"""

import subprocess
import sys


def monitor_camera():
    """Monitor camera events using macOS log stream."""
    print("Starting camera monitor...")
    print("Turn your camera ON and OFF to test detection.")
    print("Press Ctrl+C to stop.\n")

    camera_on = False

    # Use log stream to watch for camera-related events
    cmd = [
        "log", "stream",
        "--predicate", 'subsystem == "com.apple.cmio"',
        "--style", "compact"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        for line in process.stdout:
            # Detect camera start
            if "CMIODeviceStartStream" in line:
                if not camera_on:
                    camera_on = True
                    print(">>> CAMERA ON - Would turn lights ON")

            # Detect camera stop
            elif "CMIODeviceStopStream" in line:
                if camera_on:
                    camera_on = False
                    print(">>> CAMERA OFF - Would turn lights OFF")

    except KeyboardInterrupt:
        print("\nStopping camera monitor...")
        process.terminate()
        process.wait()


if __name__ == "__main__":
    monitor_camera()
