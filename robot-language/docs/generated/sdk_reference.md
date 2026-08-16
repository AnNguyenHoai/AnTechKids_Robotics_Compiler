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

#### `set_move_initialize(left_motor, right_motor, reverse)`
- Configure drive motors (left/right ports and reverse mode)

#### `set_move_run_angle(direction, speed, angle)`
- Move for a specified angle (wheel rotation or chassis turn)

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

#### `get_trace_value(port, channel)`
- Get trace sensor value (0/50/100 based on line detection)

#### `get_trace_state(port, channel)`
- Get trace sensor state (boolean)

#### `get_trace_raw(port)`
- Get raw bitmask of all 3 trace sensors

#### `get_light_sensor_data(port)`
- Read light sensor digital state (0/1)

### Led
#### `set_3c_led(port, state)`
- Set 3-color LED state

#### `set_light_sensor_led(port, state)`
- Set light sensor LED state

### Servo
#### `set_servo(port, angle)`
- Set servo angle

#### `set_seering_engine(port, angle)`
- Set steering engine angle

#### `set_seering_engine_time(port, angle, millisecond)`
- Set steering engine angle and hold for time

### Motor
#### `set_motor(port, speed)`
- Set speed of a DC motor on given port

#### `set_motor_servo(port, speed, angle)`
- Set motor+servo combination

#### `set_motor_straight_angle(left_port, right_port, speed, angle)`
- Move both motors for a given angle

### Line
#### `line_basis(speed)`
- Basic line following step (adjust motors based on sensor mask)

#### `line_follow(speed)`
- Follow line continuously until lost

#### `line_stop()`
- Stop line following (stop motors)

#### `line_millisecond(speed, millisecond)`
- Line follow for a specified time (ms), blocking

#### `line_intersection_stop(speed, type)`
- Follow line until intersection, then stop

#### `line_turn_encounterline(speed, angle, direction)`
- Turn until a line is encountered

#### `line_for_bmp(speed, degree)`
- Follow line for a given degree (time-based)

#### `line_set_initialize(port, color, chassis_type)`
- Initialize line sensor parameters

### Peripheral
#### `set_mp3_play(index)`
- Play MP3 track (adapted to active buzzer beep)

#### `set_lizard(state)`
- Control peripheral lizard (unknown)

### Gui
#### `update_var(name, value)`
- Update variable display in GUI

#### `display_variable(name)`
- Display variable value in GUI
