# Zoom Elgato Light Automation

A macOS automation that turns Elgato Key Lights on/off based on camera usage.

## Project Overview

This Python daemon monitors macOS camera activation events and controls Elgato Key Lights via their HTTP API. When the camera turns on (e.g., joining a Zoom video call), the lights turn on. When the camera turns off, the lights turn off.

## Key Components

- **Camera Detection**: Uses macOS `log stream` to monitor camera activation events (event-driven, not polling)
- **Light Control**: HTTP API calls to Elgato Key Light endpoints on port 9123
- **LaunchAgent**: Keeps the daemon running at login and auto-restarts on failure

## Configuration

Light IPs are configured via environment variables in `.env`:

```bash
ELGATO_LIGHT_IPS=192.168.1.100,192.168.1.101
```

## Files

| File | Purpose |
|------|---------|
| `zoom-elgato-light-automation.py` | Main daemon script |
| `com.local.zoom-elgato-light.plist.template` | LaunchAgent template |
| `.env.example` | Example configuration |
| `install.sh` / `uninstall.sh` | Installation scripts |

## Limitations

- Only activates for video calls (camera must be on)
- Audio-only calls will NOT trigger the lights

## Dependencies

- Python 3 (standard library only)
- No pip installs required
