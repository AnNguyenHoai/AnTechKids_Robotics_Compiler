# Ultrasonic Review Fix

## Changes Made

### 1. Removed Duplicate Implementation
- **Deleted**: `Devices/Ultrasonic.h` and `Devices/Ultrasonic.cpp`.
- **Reason**: There were two implementations of the same driver. The `Sensor/` version follows the new Sensor Framework and is the single source of truth.
- **Impact**: All code now uses `#include "../../Sensor/Ultrasonic.h"`.

### 2. Improved Health Model
- **Added**: `_consecutiveTimeouts` counter.
- **Logic**: If `pulseIn` times out for 3 consecutive reads, the sensor is marked `unhealthy`.
- **Recovery**: A single successful reading resets the counter and restores `healthy` status.
- **Rationale**: This distinguishes between "no obstacle" (normal) and "sensor disconnected/faulty" (unhealthy).

### 3. Simplified DistanceSensor API
- Kept `distanceCm()`, `maxRangeCm()`, `unit()`.
- `maxRangeCm()` returns a compile-time constant `400.0f`.
- `unit()` returns constant `"cm"`.
- No changes to ISensor or SensorManager.

## Layer Boundary Verification
- **Application**: Calls RobotAPI only.
- **RobotAPI**: Calls `SensorManager::getSensor()` and casts to `Ultrasonic*`.
- **Sensor Framework**: Manages lifecycle via `ISensor` pointers.
- **Driver (`Ultrasonic`)**: Uses `Arduino.h` (GPIO, `pulseIn`). Knows nothing about RobotAPI or VM.
- **HAL**: `Arduino.h` is the hardware abstraction.

**Conclusion**: Ultrasonic respects the one‑way dependency rule.