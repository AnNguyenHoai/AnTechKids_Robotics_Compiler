# Robot Bring‑up Guide (M1)

## Hardware Requirements
- ESP32 development board (e.g., ESP32-WROOM)
- Motor driver (L298N or similar) with 2 DC motors
- Power source (battery or USB) providing stable 5V/7.4V
- USB cable for programming

## Wiring
Refer to `robot-platform/main/src/HardwareAbstraction/GPIO.h` for pin definitions:
- Motor Left IN1 → GPIO25
- Motor Left IN2 → GPIO26
- Motor Right IN3 → GPIO27
- Motor Right IN4 → GPIO14

## Software Setup
1. Install PlatformIO (recommended) or Arduino IDE with ESP32 support.
2. Install Python dependencies: `pip install pyserial` (for deploy script).

## Build & Deploy
1. Write your robot program in `robot-platform/deploy_program.py`.
2. Run `python robot-platform/deploy.py`.
   - This compiles the program to `generated_program.h`.
   - Builds the firmware.
   - Uploads to the ESP32.
3. Open Serial Monitor (115200 baud) to see boot logs.

## Validation
- The robot should move forward for 1 second and stop.
- Serial output should show `[EXEC] Execution Finished`.