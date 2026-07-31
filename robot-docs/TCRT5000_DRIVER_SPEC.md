# TCRT5000 Driver Specification

## Purpose

Provide a clean, reusable driver for the TCRT5000 infrared line sensor.

## Hardware Interface

- **GPIO**: Digital input pin.
- **Logic**: Outputs `HIGH` when detecting a dark (black) line, `LOW` otherwise (depending on module circuit).

## Class: `TCRT5000`

Inherits from `ISensor`.

### Constructor

```cpp
TCRT5000(int pin, const char* sensorName);
Methods
Method	Description
initialize()	Sets pin mode to INPUT.
update()	Reads and stores current pin state.
healthy()	Always returns true (simple version).
name()	Returns the user‑provided name.
read()	Returns the last stored reading (HIGH/LOW).
Usage Example
cpp
TCRT5000 leftSensor(SENSOR_TRCT5000_L_PIN, "line_left");
leftSensor.initialize();
leftSensor.update();
if (leftSensor.read() == HIGH) {
    // line detected
}
Integration with RobotAPI
In RobotAPI::Initialize(), three TCRT5000 instances are registered with SensorManager:

"line_left" – left channel

"line_center" – center channel

"line_right" – right channel

RobotAPI::ReadLine(channel) uses SensorManager::getSensor() and returns 1 if read() == HIGH