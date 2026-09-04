# H25-I — Runtime Capability Contract

## Purpose

H25-I defines one firmware-facing capability contract for the hardware selected in
RoboStudio. `generated_device_config.h` remains the build-time source of truth;
`HardwareCapability` is the single runtime query/diagnostic surface.

## Contract

Supported capabilities:

- `motor`
- `encoder`
- `line_sensor`
- `ultrasonic`
- `imu`
- `servo`
- `buzzer`

Each capability is represented by `HardwareCapability::Device` and is resolved
from the corresponding `ROBOT_FEATURE_*` macro.

## Disabled behavior

| Capability | Disabled runtime behavior |
|---|---|
| Motor | Motion output APIs become safe no-ops |
| Encoder | Queries remain callable and return neutral values (`0`) |
| Line Sensor | Line APIs stop motion and return neutral state (`0`) |
| Ultrasonic | Distance APIs return unavailable (`-1`) |
| IMU | IMU is not registered/updated; diagnostics report disabled |
| Servo | Servo API is a no-op |
| Buzzer | Buzzer API is a no-op |

`Stop()` remains callable independently of the motor feature so safety paths are
not made unavailable by the capability configuration.

## Runtime inspection

Firmware exposes:

```text
hardware status
```

which prints all capabilities and the 7-bit capability mask.

RobotAPI also exposes:

```cpp
bool isHardwareEnabled(HardwareCapability::Device device);
void printHardwareCapabilities();
```

## Boundary rule

Feature availability must be checked at the RobotAPI/runtime boundary. Higher
layers must not directly depend on individual feature macros when deciding
whether an API can be used.

The existing H25-F static validator remains responsible for rejecting programs
that require disabled hardware before compilation. H25-I complements that
validation with a stable firmware runtime contract.
