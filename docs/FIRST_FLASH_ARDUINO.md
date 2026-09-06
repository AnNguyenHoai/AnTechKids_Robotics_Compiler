# First Flash with PlatformIO

RoboStudio prepares the first-flash Wi-Fi bootstrap for the ESP32. The bootstrap credentials are rendered into a local generated header and consumed by the PlatformIO bootstrap environment. On the robot's first boot, the firmware persists the values into NVS.

## Teacher workflow

1. Open RoboStudio → Robot → First-Flash Setup.
2. Enter the classroom Wi-Fi SSID and password.
3. Enter the OTA password used by the robot fleet.
4. Click **Generate First-Flash Config**.
5. Connect the new ESP32 robot by USB.
6. Select the USB port in RoboStudio, for example `COM4`.
7. Click **Flash New Robot via USB (PlatformIO)**.
8. RoboStudio invokes `python -m platformio` and uploads the `esp32dev_bootstrap` environment.
9. Wait for the robot to boot and connect to the configured Wi-Fi.
10. Return to RoboStudio and click **Discover Robots**.

No Arduino IDE interaction is required for the first-flash path. PlatformIO is the canonical build and upload engine. The Arduino sketch layout remains supported by the firmware source tree, but it is not part of the RoboStudio deployment flow.

## Generated files

RoboStudio creates these files locally:

- `.robostudio/bootstrap/robot_bootstrap.json`
- `robot-platform/main/include/generated/generated_bootstrap_config.h`

The generated C++ header contains the Wi-Fi and OTA credentials required for first boot and is Git-ignored. Do not commit it or paste its contents into student programs.

## Expected boot flow

```text
RoboStudio Generate Config
       ↓
PlatformIO esp32dev_bootstrap
       ↓
USB Upload
       ↓
ESP32 boot
       ↓
RobotWiFiConfig::begin()
       ↓
first-flash macros → NVS
       ↓
Wi-Fi connect
       ↓
mDNS + discovery + OTA
       ↓
RoboStudio Discover Robots
```

On later boots, the robot uses the persistent NVS configuration and does not require the generated header to be regenerated.

## Requirements

PlatformIO must be installed in the Python environment used by RoboStudio. RoboStudio invokes it as `python -m platformio`, so a standalone `pio` command in PATH is not required. The USB ESP32 board must be connected and available on the selected serial port.
