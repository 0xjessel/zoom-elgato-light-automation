-- Hammerspoon Configuration
-- ~/.hammerspoon/init.lua

-- Elgato Key Light Automation
-- Automatically turns lights on/off when camera is activated/deactivated
local elgato = require("elgato-lights")
elgato.start()

-- Reload config shortcut: Cmd+Ctrl+R
hs.hotkey.bind({"cmd", "ctrl"}, "R", function()
    hs.reload()
end)

-- Notify on config load
hs.alert.show("Hammerspoon config loaded")
