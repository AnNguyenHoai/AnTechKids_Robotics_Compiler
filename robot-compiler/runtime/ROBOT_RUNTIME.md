# Robot Runtime

## Overview

The Robot Runtime is the layer between the Virtual Machine and the robot hardware. It provides a hardware-independent API for controlling the robot.

## Components

### IRobot
Interface that the VM uses to control the robot. Provides methods for motion, sensors, and utilities.

### RobotRuntime
Main implementation of IRobot. Orchestrates MotionController and SensorManager.

### MotionController
Manages robot movement: forward, backward, left, right, stop, wait. Maintains state (IDLE, MOVING, TURNING, WAITING, STOPPED, ERROR) and emits events.

### SensorManager
Provides unified access to sensors: ultrasonic, line sensors, touch.

### IHardware
Abstraction for hardware peripherals: motors, delay, sensors.

### MockHardware
Mock implementation for testing. Logs motor commands, returns simulated sensor values.

## Architecture Flow

VirtualMachine -> Dispatcher -> Handlers -> RobotRuntime -> MotionController/SensorManager -> IHardware -> MockHardware/ESP32Hardware

## State Machine

- IDLE: no movement
- MOVING: moving forward/backward
- TURNING: turning left/right
- WAITING: in a wait delay
- STOPPED: recently stopped
- ERROR: error state

## Events

- MOVEMENT_STARTED: when forward/backward/left/right is called
- MOVEMENT_STOPPED: when stop() is called
- SENSOR_CHANGED: when sensor value changes (future)
- EXECUTION_FINISHED: when program ends

## Future ESP32 Integration

To replace MockHardware with ESP32Hardware, implement IHardware and pass it to RobotRuntime. No changes needed in VirtualMachine or handlers.