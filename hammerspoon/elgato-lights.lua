-- Elgato Key Light Automation for Hammerspoon
-- Monitors camera usage and controls Elgato Key Lights
--
-- When any camera turns on (video calls, etc.) -> lights turn on
-- When all cameras turn off -> lights turn off

local M = {}

-- Logger
local log = hs.logger.new("elgato", "info")

--------------------------------------------------------------------------------
-- Configuration
--------------------------------------------------------------------------------

-- Light settings: IP, brightness (0-100), temperature (Kelvin 2900-7000)
-- TODO: Update these with your Elgato Key Light IP addresses
local lights = {
    { ip = "192.168.1.100", brightness = 50, temperature = 4500 },
    { ip = "192.168.1.101", brightness = 75, temperature = 5000 },
}

local PORT = 9123
local HTTP_TIMEOUT = 3  -- seconds

--------------------------------------------------------------------------------
-- State
--------------------------------------------------------------------------------

local cameraWatchers = {}  -- table of camera -> watcher
local anyCameraInUse = false
local turnOffTimer = nil   -- debounce timer for turning off lights

--------------------------------------------------------------------------------
-- Helpers
--------------------------------------------------------------------------------

-- Convert Kelvin to mireds (Elgato API uses mireds)
-- Valid range: 143 (7000K) to 344 (2900K)
local function kelvinToMireds(kelvin)
    local mireds = math.floor(1000000 / kelvin)
    return math.max(143, math.min(344, mireds))
end

--------------------------------------------------------------------------------
-- Light Control
--------------------------------------------------------------------------------

-- Set a single light on or off
local function setLight(light, on)
    local url = string.format("http://%s:%d/elgato/lights", light.ip, PORT)
    local payload

    if on then
        payload = hs.json.encode({
            lights = {{
                on = 1,
                brightness = light.brightness,
                temperature = kelvinToMireds(light.temperature)
            }}
        })
    else
        payload = hs.json.encode({
            lights = {{ on = 0 }}
        })
    end

    local headers = { ["Content-Type"] = "application/json" }

    hs.http.asyncPut(url, payload, headers, function(code, body, respHeaders)
        if code >= 200 and code < 300 then
            if on then
                log.i(string.format("Light %s: ON (brightness=%d%%, temp=%dK)",
                    light.ip, light.brightness, light.temperature))
            else
                log.i(string.format("Light %s: OFF", light.ip))
            end
        elseif code == 0 then
            -- Connection failed - light is unreachable (probably not at home)
            log.d(string.format("Light %s: unreachable (not on network)", light.ip))
        else
            log.w(string.format("Light %s: failed with code %d", light.ip, code))
        end
    end)
end

-- Set all lights on or off
local function setAllLights(on)
    local state = on and "ON" or "OFF"
    log.i(string.format("Setting all lights %s", state))

    for _, light in ipairs(lights) do
        setLight(light, on)
    end
end

--------------------------------------------------------------------------------
-- Camera Monitoring
--------------------------------------------------------------------------------

-- Check if any camera is currently in use
local function checkAnyCameraInUse()
    local cameras = hs.camera.allCameras()
    for _, camera in ipairs(cameras) do
        if camera:isInUse() then
            return true
        end
    end
    return false
end

-- Handle camera state change
local function onCameraStateChange(camera, property, scope, element)
    local wasInUse = anyCameraInUse
    local nowInUse = checkAnyCameraInUse()

    if nowInUse and not wasInUse then
        -- Transitioned from no cameras in use to at least one in use
        -- Cancel any pending turn-off timer
        if turnOffTimer then
            turnOffTimer:stop()
            turnOffTimer = nil
            log.i("Cancelled pending light turn-off")
        end
        log.i(string.format("Camera activated: %s", camera:name()))
        anyCameraInUse = true
        setAllLights(true)
    elseif not nowInUse and wasInUse then
        -- Transitioned from cameras in use to none in use
        -- Use a 1-second delay to avoid flickering from brief camera state changes
        log.i(string.format("Camera deactivated: %s (waiting 1s before turning off lights)", camera:name()))
        anyCameraInUse = false
        if turnOffTimer then
            turnOffTimer:stop()
        end
        turnOffTimer = hs.timer.doAfter(1, function()
            -- Double-check no camera is in use before turning off
            if not checkAnyCameraInUse() then
                setAllLights(false)
            end
            turnOffTimer = nil
        end)
    end
end

-- Set up watcher for a single camera
local function watchCamera(camera)
    if cameraWatchers[camera:uid()] then
        return  -- Already watching this camera
    end

    camera:setPropertyWatcherCallback(onCameraStateChange)
    camera:startPropertyWatcher()
    cameraWatchers[camera:uid()] = camera
    log.i(string.format("Watching camera: %s", camera:name()))
end

-- Stop watching a camera
local function unwatchCamera(camera)
    if cameraWatchers[camera:uid()] then
        camera:stopPropertyWatcher()
        cameraWatchers[camera:uid()] = nil
        log.i(string.format("Stopped watching camera: %s", camera:name()))
    end
end

-- Handle camera added/removed events
local function onCameraAddedOrRemoved(camera, event)
    if event == "Added" then
        log.i(string.format("Camera connected: %s", camera:name()))
        watchCamera(camera)
    elseif event == "Removed" then
        log.i(string.format("Camera disconnected: %s", camera:name()))
        unwatchCamera(camera)

        -- Check if we need to turn off lights (in case the removed camera was in use)
        if anyCameraInUse and not checkAnyCameraInUse() then
            anyCameraInUse = false
            -- Use same 1-second delay for consistency
            if turnOffTimer then
                turnOffTimer:stop()
            end
            turnOffTimer = hs.timer.doAfter(1, function()
                if not checkAnyCameraInUse() then
                    setAllLights(false)
                end
                turnOffTimer = nil
            end)
        end
    end
end

--------------------------------------------------------------------------------
-- Public API
--------------------------------------------------------------------------------

-- Start monitoring cameras
function M.start()
    log.i("=================================================")
    log.i("Elgato Light Automation starting")
    log.i(string.format("Configured lights: %d", #lights))
    for _, light in ipairs(lights) do
        log.i(string.format("  - %s (brightness=%d%%, temp=%dK)",
            light.ip, light.brightness, light.temperature))
    end
    log.i("=================================================")

    -- Watch for camera add/remove events
    hs.camera.setWatcherCallback(onCameraAddedOrRemoved)
    hs.camera.startWatcher()

    -- Set up watchers for all existing cameras
    local cameras = hs.camera.allCameras()
    if #cameras == 0 then
        log.i("No cameras detected")
    else
        for _, camera in ipairs(cameras) do
            watchCamera(camera)
        end
    end

    -- Check initial state
    anyCameraInUse = checkAnyCameraInUse()
    if anyCameraInUse then
        log.i("Camera already in use - turning lights on")
        setAllLights(true)
    end

    log.i("Elgato Light Automation ready")
end

-- Stop monitoring cameras
function M.stop()
    log.i("Stopping Elgato Light Automation")

    -- Cancel any pending turn-off timer
    if turnOffTimer then
        turnOffTimer:stop()
        turnOffTimer = nil
    end

    hs.camera.stopWatcher()

    for uid, camera in pairs(cameraWatchers) do
        camera:stopPropertyWatcher()
    end
    cameraWatchers = {}

    log.i("Elgato Light Automation stopped")
end

-- Manually turn lights on
function M.lightsOn()
    setAllLights(true)
end

-- Manually turn lights off
function M.lightsOff()
    setAllLights(false)
end

-- Get current status
function M.status()
    local cameras = hs.camera.allCameras()
    print("=== Elgato Light Automation Status ===")
    print(string.format("Cameras detected: %d", #cameras))
    for _, camera in ipairs(cameras) do
        local inUse = camera:isInUse() and "IN USE" or "idle"
        print(string.format("  - %s: %s", camera:name(), inUse))
    end
    print(string.format("Lights configured: %d", #lights))
    for _, light in ipairs(lights) do
        print(string.format("  - %s (brightness=%d%%, temp=%dK)",
            light.ip, light.brightness, light.temperature))
    end
    print(string.format("Any camera in use: %s", anyCameraInUse and "yes" or "no"))
end

return M
