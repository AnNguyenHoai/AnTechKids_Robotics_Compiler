# H25-C — Hardware Macro Generation

## Scope
Generate firmware build-time feature macros from RoboStudio's persisted hardware configuration.

## Source of truth
`robostudio/config/hardware.json`

The generator never owns device state. It consumes `HardwareConfig`, which is loaded through `HardwareConfigService`.

## Generated artifact
`robot-platform/main/include/generated/generated_device_config.h`

Example:

```cpp
#pragma once

#define ROBOT_FEATURE_MOTOR        1
#define ROBOT_FEATURE_ENCODER      0
#define ROBOT_FEATURE_LINE_SENSOR  1
#define ROBOT_FEATURE_IMU          0
```

Every device registered in `DeviceRegistry` receives an explicit `0` or `1` macro so the generated firmware configuration is deterministic.

## Runtime flow

```text
Hardware Tab
    ↓
Apply Configuration
    ↓
hardware.json
    ↓
HardwareMacroService
    ↓
generated_device_config.h
```

## Ownership
- `DeviceRegistry`: supported devices and stable IDs.
- `HardwareConfig`: device state.
- `HardwareConfigService`: persistence.
- `HardwareMacroGenerator`: deterministic C/C++ header generation.
- `HardwareMacroService`: orchestration from persisted config to firmware artifact.

## Explicitly out of scope
- Firmware source feature guards (`#if ROBOT_FEATURE_*`).
- Conditional device initialization.
- API fallback/degraded behavior.

Those are H25-D and later tasks.
