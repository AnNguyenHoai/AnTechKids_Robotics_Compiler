# ESP32 Hardware Adapter

**Version:** 1.0  
**Status:** Ready  
**Owner:** Platform Team  

## Overview

The ESP32 Hardware Adapter is a concrete implementation of `IHardware` that translates abstract robot operations into Arduino-compatible calls. It is designed to run on the ESP32 platform (in the future) but currently serves as a Python stub for testing and architecture validation.

## Architecture

The adapter follows a layered design to keep the Robot Runtime hardware-independent.
VirtualMachine
│
▼
RobotRuntime
│
▼
IHardware
│
▼
ESP32Hardware
│
├── MotorDriver (IMotorDriver)
├── Timer (ITimer)
├── Logger (ILogger)
└── Capabilities (HardwareCapabilities)

text

## Components

### BoardConfiguration
Data class containing all pin mappings and hardware parameters:
- Motor pins (left/right) and PWM channels
- PWM frequency and resolution
- Sensor pin placeholders (ultrasonic, line, touch)
- UART/I2C/SPI configuration (future)

### HardwareCapabilities
Exposes the hardware's feature set:
- PWM, ADC, GPIO, UART, I2C, SPI support
- Maximum number of PWM/ADC channels

### ESP32MotorDriver
Implements `IMotorDriver`:
- `set_motor(left, right)`: sets PWM values (clamped to -100..100)
- `stop()`: sets motors to 0
- `brake()`: placeholder for future implementation

### ESP32Timer
Implements `ITimer`:
- `delay(ms)`: blocking delay using `time.sleep`
- `millis()`: current time in milliseconds
- `micros()`: current time in microseconds

### ESP32Logger
Implements `ILogger`:
- Logs messages with levels: INFO, WARN, ERROR, DEBUG
- Outputs to stdout (can be redirected)

### ESP32Hardware
Main adapter class that implements `IHardware`:
- Uses the above components to fulfill the interface
- Provides test helpers (`set_ultrasonic_value`, etc.) for mocking sensor data

## Integration with VM

The Virtual Machine can be instantiated with `ESP32Hardware` instead of `MockHardware`:

```python
from runtime import VirtualMachine, ESP32Hardware, BoardConfiguration

config = BoardConfiguration(left_motor_pin=25, right_motor_pin=26,
                            pwm_channel_left=0, pwm_channel_right=1)
hw = ESP32Hardware(config)
vm = VirtualMachine(hardware=hw)
vm.load(runtime_program)
vm.run()
Testing
Smoke Tests
Board configuration loading

Hardware initialization

Motor setting

Timing

Sensor reading

Logging levels

Integration Tests
VM execution with ESP32Hardware

Program with MOVE_RUN and MOVE_STOP

Program with WAIT

Step-by-step execution verification

Out of Scope
Line Sensor

Ultrasonic (real reading)

Touch

Encoders

Gyroscope

Bluetooth/WiFi

OTA

Scheduler

Power Management

These will be added in future sprints.

Future Extensions
Real PWM output via pyfirmata or pyserial

Hardware-specific sensor drivers

Interrupt support

RTOS integration

text

---

### 15. (Tùy chọn) Cập nhật `robot-compiler/runtime/__init__.py` để chạy tests

Không cần thiết nhưng có thể thêm entry point.

---

Tất cả các thay đổi trên đã hoàn thành các task từ TASK-001 đến TASK-010. Mỗi file đều có chú thích rõ ràng, đúng với kiến trúc hiện tại và chỉ tập trung vào phần adapter mà không ảnh hưởng đến VM hay Runtime logic.