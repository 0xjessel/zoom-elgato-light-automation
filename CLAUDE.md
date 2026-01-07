# Zoom Elgato Light Automation

A macOS automation that turns Elgato Key Lights on/off based on camera usage.

## Project Overview

This project provides two implementations for monitoring camera events and controlling Elgato Key Lights:

1. **Python daemon** - Uses `log stream` to monitor camera events, runs via LaunchAgent
2. **Hammerspoon module** (recommended) - Native `hs.camera` API, runs within Hammerspoon

When the camera turns on (e.g., joining a Zoom video call), the lights turn on with configured brightness/temperature. When the camera turns off, the lights turn off.

## Implementations

### Hammerspoon (Recommended)

Located in `hammerspoon/` directory. Uses native `hs.camera` module for cleaner integration.

- **elgato-lights.lua**: Main module with camera watching and light control
- **init.lua**: Example config that loads the module

Key features:
- Native camera add/remove event handling
- Silent failures when lights are unreachable (works on the go)
- No LaunchAgent needed

### Python

Original implementation using `log stream` to parse CoreMediaIO events.

- **zoom-elgato-light-automation.py**: Main daemon script
- **com.local.zoom-elgato-light.plist.template**: LaunchAgent template
- **install.sh / uninstall.sh**: Installation scripts

## Configuration

### Hammerspoon

Edit `~/.hammerspoon/elgato-lights.lua`:
```lua
local lights = {
    { ip = "192.168.1.100", brightness = 50, temperature = 4500 },
    { ip = "192.168.1.101", brightness = 75, temperature = 5000 },
}
```

### Python

Environment variables in `.env`:
```bash
ELGATO_LIGHTS=192.168.1.100:50:4500,192.168.1.101:75:5000
```

## Technical Notes

- **Elgato API**: HTTP PUT to port 9123, uses "mireds" for temperature
- **Mireds conversion**: `mireds = 1,000,000 / kelvin`
- **Valid range**: 143 (7000K) to 344 (2900K)

## Limitations

- Only activates for video calls (camera must be on)
- Audio-only calls will NOT trigger the lights
