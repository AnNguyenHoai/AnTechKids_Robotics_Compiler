# Robot Language Reference

**Language:** Robot Language
**Version:** 1.0.0

## Overview
Robot Language is a simple, Python-like language for programming robots. It compiles to bytecode and runs on the Robot VM.

## Syntax

### Variables
```python
speed = 80
```

### Functions (built-in)
Robot Language provides several built-in functions:
| Function | Arguments | Description |
|----------|-----------|-------------|
| `forward(speed)` | 1 | Move robot forward |
| `backward(speed)` | 1 | Move robot backward |
| `turn_left(speed)` | 1 | Rotate robot left |
| `turn_right(speed)` | 1 | Rotate robot right |
| `set_motor_speed(left_speed, right_speed)` | 2 | Set motor speeds independently |
| `set_move_initialize(left_motor, right_motor, reverse)` | 3 | Configure drive motors (left/right ports and reverse mode) |
| `set_move_run_angle(direction, speed, angle)` | 3 | Move for a specified angle (wheel rotation or chassis turn) |
| `wait(milliseconds)` | 1 | Wait milliseconds |
| `stop()` | 0 | Stop robot |
| `read_ultrasonic()` | 0 | Read ultrasonic distance in cm |
| `read_touch(port)` | 1 | Read touch sensor state (0/1) |
| `read_light(channel)` | 1 | Read light sensor raw value (0-1023) |
| `read_color()` | 0 | Read color sensor (placeholder) |
| `read_line(channel)` | 1 | Read line sensor (0=white, 1=dark) |
| `get_trace_value(port, channel)` | 2 | Get trace sensor value (0/50/100 based on line detection) |
| `get_trace_state(port, channel)` | 2 | Get trace sensor state (boolean) |
| `get_trace_raw(port)` | 1 | Get raw bitmask of all 3 trace sensors |
| `get_light_sensor_data(port)` | 1 | Read light sensor digital state (0/1) |
| `set_3c_led(port, state)` | 2 | Set 3-color LED state |
| `set_light_sensor_led(port, state)` | 2 | Set light sensor LED state |
| `set_servo(port, angle)` | 2 | Set servo angle |
| `set_seering_engine(port, angle)` | 2 | Set steering engine angle |
| `set_seering_engine_time(port, angle, millisecond)` | 3 | Set steering engine angle and hold for time |
| `set_motor(port, speed)` | 2 | Set speed of a DC motor on given port |
| `set_motor_servo(port, speed, angle)` | 3 | Set motor+servo combination |
| `set_motor_straight_angle(left_port, right_port, speed, angle)` | 4 | Move both motors for a given angle |
| `line_basis(speed)` | 1 | Basic line following step (adjust motors based on sensor mask) |
| `line_follow(speed)` | 1 | Follow line continuously until lost |
| `line_stop()` | 0 | Stop line following (stop motors) |
| `line_millisecond(speed, millisecond)` | 2 | Line follow for a specified time (ms), blocking |
| `line_intersection_stop(speed, type)` | 2 | Follow line until intersection, then stop |
| `line_turn_encounterline(speed, angle, direction)` | 3 | Turn until a line is encountered |
| `line_for_bmp(speed, degree)` | 2 | Follow line for a given degree (time-based) |
| `line_set_initialize(port, color, chassis_type)` | 3 | Initialize line sensor parameters |
| `set_mp3_play(index)` | 1 | Play MP3 track (adapted to active buzzer beep) |
| `set_lizard(state)` | 1 | Control peripheral lizard (unknown) |
| `update_var(name, value)` | 2 | Update variable display in GUI |
| `display_variable(name)` | 1 | Display variable value in GUI |

### User-Defined Functions
```python
def my_function(param1, param2):
    # function body
    return value
```

### Control Flow
- `if condition:` ... `else:` ...
- `while condition:` ...
- `break` and `continue`

### Scope Rules
- Variables defined outside functions are global.
- Variables defined inside functions are local.
- Local variables shadow globals.

---
*For a complete specification, see `api.yaml`*.