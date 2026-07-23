# Sensor Runtime Architecture

**Version:** 1.0  
**Status:** Ready  
**Owner:** Platform Team  

## Overview

The Sensor Runtime provides a unified infrastructure for all robot sensors. It decouples sensor hardware from robot logic, enabling easy addition of new sensors and consistent data access.

## Architecture
RobotRuntime
│
▼
SensorManager
│
├── LineSensor
├── UltrasonicSensor
├── TouchSensor
├── LightSensor
└── ColorSensor
│
▼
Hardware Interface (IHardware)
│
▼
ESP32Adapter / MockHardware

text

## Components

### ISensor
Base interface for all sensors:
- `initialize()`, `update()`, `read()`, `reset()`, `health()`, `shutdown()`
- Each sensor implementation must inherit.

### SensorValue
Encapsulates a reading with metadata:
- `raw`: raw value from hardware
- `normalized`: normalized to 0.0–1.0
- `timestamp`: time of reading
- `valid`: boolean
- `quality`: 0.0–1.0

### SensorEvent
Events emitted by sensors:
- `ACTIVATED`, `DEACTIVATED`, `CHANGED`, `ERROR`, `DISCONNECTED`
- Used for debugging and future event-driven programming.

### SensorManager
Central registry and lifecycle manager:
- Register sensors
- Initialize/update/shutdown all
- Read individual sensors
- Health monitoring

## Sensor Implementations

### LineSensor
- `is_on_line(threshold)`: returns True if over dark line
- `position()`: normalized position
- `confidence()`: confidence score

### UltrasonicSensor
- `distance()`: distance in cm
- `has_obstacle(threshold)`: obstacle detection

### TouchSensor
- `pressed()`, `released()`, `clicked()`
- Built-in debounce

### LightSensor
- `brightness()`: raw brightness
- `normalized()`: normalized brightness

### ColorSensor
- `color()`: RGB tuple
- `rgb()`: normalized RGB
- `confidence()`

## Filtering

Filters can be applied to sensor values:
- `MovingAverageFilter`: smooths noise
- `MedianFilter`: removes outliers
- `ThresholdFilter`: hysteresis thresholding

## Health Monitoring

Each sensor reports health status:
- `healthy`
- `disconnected`
- `timeout`
- `invalid`
- `calibration_required`

## Integration with RobotRuntime

`RobotRuntime` automatically registers a default set of sensors using the provided hardware. Sensor data can be accessed via `RobotRuntime.sensor_manager`.

## Future Extensions

- More sensors (gyroscope, accelerometer, GPS)
- Calibration framework
- Sensor fusion
- Event-driven callbacks
- Debugger integration

## Testing

Mock sensors are provided for deterministic testing. See `tests/test_sensors.py`.