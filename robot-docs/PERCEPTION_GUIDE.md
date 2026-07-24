# Perception Guide

## Overview
This guide describes how to use sensors in robot programs and validate perception.

## Supported Sensors
- **Ultrasonic**: HC-SR04 (distance in cm)
- **Touch**: Digital touch sensors (0/1)
- **Line**: TCRT5000 (0/1)
- **Light**: Analog light sensor (0-4095)
- **Color**: Placeholder (for future)

## API
```python
dist = read_ultrasonic()          # returns int cm
state = read_touch(port)          # port 0 or 1
light = read_light(channel)       # channel 0
color = read_color()              # placeholder
line = read_line(channel)         # channel 0,1,2

Calibration
Use SensorConfig to adjust:

lightGain, lightOffset

lineInverted

ultrasonicTimeoutMs

Example Program
python
while True:
    if read_touch(0) == 1:
        stop()
        break
    forward(30)
    wait(100)