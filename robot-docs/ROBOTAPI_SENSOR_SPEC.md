# RobotAPI Sensor Specification

## Overview

RobotAPI provides high‑level sensor access for the VM. It delegates all hardware interaction to SensorManager.

## Line Sensor API

### `int16_t ReadLine(int channel)`

- **channel**: 0 = left, 1 = center, 2 = right
- **Returns**: 1 if line (black) is detected, 0 otherwise.

**Implementation**:

```cpp
int16_t ReadLine(int channel) {
    const char* name = ...;
    auto sensor = SensorManager::instance().getSensor(name);
    return (sensor && sensor->read() == HIGH) ? 1 : 0;
}
Other Sensor APIs (temporarily unchanged)
ReadUltrasonic() – direct call to Ultrasonic driver.

ReadTouch(int port) – direct call to Touch driver.

ReadLight(int channel) – direct call to LightSensor driver.

ReadColor() – direct call to ColorSensor driver.