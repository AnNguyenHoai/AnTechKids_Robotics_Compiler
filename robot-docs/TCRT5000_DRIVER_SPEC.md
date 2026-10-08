# TCRT5000 Driver Specification

## Purpose

Provide a clean, reusable driver for the TCRT5000 infrared line sensor.

## Hardware Interface

- **GPIO**: Digital input pin.
- **Logic (V1 Line5 real hardware evidence)**: the digital module is **active-low** for a dark/black line: `LOW` = line detected, `HIGH` = background/no line.
- The driver semantic default therefore uses `threshold = LOW`. `rawLevel()` still exposes the electrical GPIO level unchanged.

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
if (leftSensor.isLineDetected()) {
    // active-low hardware: raw LOW means black line detected
}
Integration with RobotAPI
In RobotAPI::Initialize(), five TCRT5000 instances are registered with SensorManager:

"line_far_left" – far-left channel

"line_left" – left channel

"line_center" – center channel

"line_right" – right channel

"line_far_right" – far-right channel

RobotAPI::ReadLine(channel), GetTraceState(), GetTraceValue() and GetTraceRaw() use isLineDetected(), so semantic line detection is LOW-active while raw GPIO diagnostics remain unmodified.