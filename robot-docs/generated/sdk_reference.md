# SDK Reference (Python)

This document describes the Python SDK generated from the specification.

## Installation
The SDK is automatically installed as part of the `robot-language` build.

## API Reference

### Motion
#### `forward(speed)`
- Move robot forward

#### `backward(speed)`
- Move robot backward

#### `turn_left(speed)`
- Rotate robot left

#### `turn_right(speed)`
- Rotate robot right

#### `set_motor_speed(left_speed, right_speed)`
- Set motor speeds independently

### System
#### `wait(milliseconds)`
- Wait milliseconds

#### `stop()`
- Stop robot

### Sensor
#### `read_ultrasonic()`
- Read ultrasonic distance in cm

#### `read_touch(port)`
- Read touch sensor state (0/1)

#### `read_light(channel)`
- Read light sensor raw value (0-1023)

#### `read_color()`
- Read color sensor (placeholder)

#### `read_line(channel)`
- Read line sensor (0=white, 1=dark)

### Servo
#### `set_servo(port, angle)`
- Set servo angle

### Led
#### `set_3c_led(port, state)`
- Set 3-color LED state

#### `set_light_sensor_led(port, state)`
- Set light sensor LED state

### Motor
#### `set_motor_straight_angle(left_port, right_port, speed, angle)`
- Set motor straight angle

### Line
#### `line_intersection_stop(speed, type)`
- Stop at line intersection

### Peripheral
#### `set_mp3_play(index)`
- Play MP3 track (adapted to active buzzer beep)
