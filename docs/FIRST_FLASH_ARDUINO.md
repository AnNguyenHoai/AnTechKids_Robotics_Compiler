# First Flash with Arduino IDE

RoboStudio prepares the first-flash Wi-Fi bootstrap for the ESP32. The bootstrap credentials are rendered into a local generated header that is consumed by the Arduino sketch and copied to NVS on the robot's first boot.

## Teacher workflow

1. Open RoboStudio → Robot → First-Flash Setup.
2. Enter the classroom Wi-Fi SSID and password.
3. Enter the OTA password used by the robot fleet.
4. Click **Generate First-Flash Config**.
5. Click **Flash New Robot via USB (Arduino IDE)**. RoboStudio opens `robot-platform/main/main.ino` in Arduino IDE when the IDE executable is discoverable; otherwise open that sketch manually.
6. In Arduino IDE select the ESP32 board used by the robot (currently **ESP32 Dev Module**) and the USB serial port, for example `COM4`.
7. Click **Upload** in Arduino IDE.
8. Wait for the robot to boot and connect to the configured Wi-Fi.
9. Return to RoboStudio and click **Discover Robots**.

Arduino IDE compiles `.cpp` files recursively from the sketch's `src` subfolder, so the existing `robot-platform/main` folder is the first-flash sketch root. See the Arduino sketch specification for the supported `src` layout.

## Generated files

RoboStudio creates these files locally:

- `.robostudio/bootstrap/robot_bootstrap.json`
- `robot-platform/main/include/generated/generated_bootstrap_config.h`

The generated C++ header contains the Wi-Fi and OTA credentials required for first boot and is Git-ignored. Do not commit it or paste its contents into student programs.

## Expected boot flow

```text
Arduino IDE Upload
       ↓
ESP32 boot
       ↓
RobotWiFiConfig::begin()
       ↓
first-flash macros → NVS
       ↓
Wi-Fi connect
       ↓
mDNS + ArduinoOTA + discovery
       ↓
RoboStudio Discover Robots
```

On later boots, the robot uses the persistent NVS configuration and does not require the generated header to be regenerated.

## Requirements

The Arduino IDE must have the Arduino-ESP32 board support installed and the correct ESP32 board selected. Espressif documents installation through Boards Manager and Arduino IDE support for ESP32 boards.
