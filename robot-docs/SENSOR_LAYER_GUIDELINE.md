# Sensor Layer Guideline

## Dependency Direction

All dependencies must be strictly one‑way, from top to bottom:
Application (user code / VM)
↓
RobotAPI (hardware‑agnostic robot control)
↓
Sensor Framework (SensorManager, ISensor, categories)
↓
Sensor Driver (TCRT5000, Ultrasonic, etc.)
↓
Hardware Abstraction Layer (GPIO, I2C, SPI, PWM)
↓
Physical Hardware (ESP32 pins, sensors, motors)

text

## Layer Responsibilities

| Layer | Responsibility | What It Knows | What It Must NOT Know |
|-------|----------------|---------------|----------------------|
| **Application** | Robot mission logic | RobotAPI functions | GPIO, pins, sensor internals |
| **RobotAPI** | Expose semantic robot APIs | SensorManager, abstract sensor types | Pin numbers, driver implementation details |
| **Sensor Framework** | Manage sensor lifecycle, provide base classes | `ISensor`, `SensorManager`, SensorID | GPIO, hardware specifics |
| **Sensor Driver** | Talk directly to hardware | HAL (GPIO, I2C, etc.) | RobotAPI, VM, application logic |
| **HAL** | Abstract hardware access | Microcontroller registers | Sensor semantics |

## Why Ultrasonic is a Driver

Ultrasonic uses:
- `pinMode()`, `digitalWrite()`, `pulseIn()` — all HAL functions.
- It does **not** call `RobotAPI::Forward()` or any business logic.
- It exposes only `distanceCm()`.

Therefore, it belongs in the **Driver** layer.

## Future Evolution

- New sensors (IMU, Encoder, GPS) will follow the same pattern.
- If a sensor uses I2C/SPI, the driver may depend on `Wire.h` or `SPI.h` — still HAL, still valid.
- **No sensor driver should ever include RobotAPI.h or SensorManager.h** (except for registration in `RobotAPI::Initialize()`).