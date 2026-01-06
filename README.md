# Zoom Elgato Light Automation

Automatically turn your Elgato Key Lights on when you join a video call, and off when you leave.

## How It Works

This macOS daemon monitors camera activation events using the system log stream. When any application (Zoom, Google Meet, FaceTime, etc.) turns on your camera, your Elgato Key Lights automatically turn on. When the camera turns off, the lights turn off.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  macOS Camera   │────▶│  Python Daemon   │────▶│  Key Light API  │
│  (log stream)   │     │  (event-driven)  │     │  (HTTP :9123)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Features

- **Event-driven**: No polling. Uses macOS `log stream` to detect camera events instantly
- **Works with any app**: Zoom, Google Meet, FaceTime, Photo Booth, etc.
- **Multiple lights**: Controls multiple Elgato Key Lights simultaneously
- **Auto-start**: Runs automatically at login via LaunchAgent
- **Resilient**: Auto-restarts if the process crashes
- **Zero dependencies**: Uses only Python standard library

## Requirements

- macOS (tested on macOS Sequoia)
- Python 3
- Elgato Key Light or Key Light Air (connected to your network)
- Elgato Control Center app (for initial light setup / finding IPs)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/0xjessel/zoom-elgato-light-automation.git
cd zoom-elgato-light-automation
```

### 2. Configure your light IPs

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your Elgato Key Light IP addresses
# Find IPs in Elgato Control Center app under light settings
```

Example `.env`:
```bash
ELGATO_LIGHT_IPS=192.168.1.100,192.168.1.101
```

### 3. Test the lights

```bash
# Check if lights are reachable
python3 test_light_control.py status

# Test turning lights on/off
python3 test_light_control.py on
python3 test_light_control.py off
```

### 4. Test camera detection

```bash
python3 test_camera_detection.py
# Then turn your camera on/off to verify detection works
```

### 5. Install the daemon

```bash
./install.sh
```

This generates the LaunchAgent plist from your `.env` config and starts the automation.

## Usage

Once installed, the automation runs automatically. Just join a video call with your camera on, and your lights will turn on. Leave the call (or turn off your camera), and the lights will turn off.

### Useful Commands

```bash
# View live logs
tail -f ~/Library/Logs/zoom-elgato-light-automation.log

# Check if the service is running
launchctl list | grep zoom-elgato-light

# Uninstall
./uninstall.sh

# Reinstall (after changing .env)
./uninstall.sh && ./install.sh
```

## How Camera Detection Works

The script monitors macOS's CoreMediaIO subsystem via `log stream`:

```bash
log stream --predicate 'subsystem == "com.apple.cmio"' --style compact
```

It watches for these specific events:
- `CMIODeviceStartStream` → Camera turned ON
- `CMIODeviceStopStream` → Camera turned OFF

This approach is event-driven (not polling) and works with any application that uses the camera.

## Elgato Key Light API

The Key Lights expose a simple REST API on port 9123:

```bash
# Get light status
curl http://<light-ip>:9123/elgato/lights

# Turn light on
curl -X PUT http://<light-ip>:9123/elgato/lights \
  -H "Content-Type: application/json" \
  -d '{"lights":[{"on":1}]}'

# Turn light off
curl -X PUT http://<light-ip>:9123/elgato/lights \
  -H "Content-Type: application/json" \
  -d '{"lights":[{"on":0}]}'
```

## Configuration

All configuration is done via environment variables in `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `ELGATO_LIGHT_IPS` | Yes | Comma-separated list of light IP addresses |
| `ELGATO_LIGHT_PORT` | No | Port number (default: 9123) |

## Limitations

- **Video calls only**: Only triggers when the camera is active. Audio-only calls won't turn on the lights.
- **macOS only**: Uses macOS-specific APIs (`log stream`, LaunchAgent)
- **Static IPs**: If your lights get new IPs via DHCP, update `.env` and reinstall

## Troubleshooting

### Lights don't turn on/off

1. Check if the service is running:
   ```bash
   launchctl list | grep zoom-elgato-light
   ```

2. Check the logs:
   ```bash
   tail -50 ~/Library/Logs/zoom-elgato-light-automation.log
   ```

3. Verify lights are reachable:
   ```bash
   python3 test_light_control.py status
   ```

### Service won't start

1. Verify `.env` is configured:
   ```bash
   cat .env
   ```

2. Try reinstalling:
   ```bash
   ./uninstall.sh
   ./install.sh
   ```

## Files

| File | Description |
|------|-------------|
| `zoom-elgato-light-automation.py` | Main daemon script |
| `com.local.zoom-elgato-light.plist.template` | LaunchAgent template |
| `.env.example` | Example configuration file |
| `install.sh` | Installation script |
| `uninstall.sh` | Uninstallation script |
| `test_camera_detection.py` | Test script for camera detection |
| `test_light_control.py` | Test script for light control |

## License

MIT License - feel free to use, modify, and distribute.

## Acknowledgments

- Built with [Claude Code](https://claude.ai/code)
