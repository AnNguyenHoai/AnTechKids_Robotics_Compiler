# H25-A — Hardware Configuration Domain

## Purpose

Create the RoboStudio domain layer that represents selectable robot hardware.
H25-A is intentionally UI-independent and does not yet generate firmware macros.

## Source of Truth

`robostudio/config/hardware.json`

The file stores one explicit enabled/disabled state for every registered device.

## Domain Model

- `DeviceDefinition`: immutable metadata for a supported device.
- `DeviceRegistry`: central list of supported devices and defaults.
- `DeviceConfig`: state of one device.
- `HardwareConfig`: aggregate root for all device selections.
- `HardwareConfigService`: JSON load/save boundary.

## Registered Devices

- `motor` — default enabled
- `encoder` — default disabled
- `line_sensor` — default enabled
- `ultrasonic` — default disabled
- `imu` — default disabled
- `servo` — default disabled
- `buzzer` — default disabled

## Contract for Later Tasks

### H25-B
A UI tab edits `HardwareConfig` through `HardwareConfigService`.

### H25-C
A generator converts `hardware.json` into firmware feature macros, for example:

```cpp
#define ROBOT_FEATURE_IMU 0
#define ROBOT_FEATURE_ENCODER 1
```

H25-A deliberately does not add feature guards to firmware. The domain is the
first step and remains the single source of truth for later UI and generation.
