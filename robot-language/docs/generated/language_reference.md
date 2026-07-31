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
| `wait(milliseconds)` | 1 | Wait milliseconds |
| `stop()` | 0 | Stop robot |
| `read_ultrasonic()` | 0 | Read ultrasonic distance in cm |
| `read_touch(port)` | 1 | Read touch sensor state (0/1) |
| `read_light(channel)` | 1 | Read light sensor raw value (0-1023) |
| `read_color()` | 0 | Read color sensor (placeholder) |
| `read_line(channel)` | 1 | Read line sensor (0=white, 1=dark) |
| `set_servo(port, angle)` | 2 | Set servo angle |
| `set_3c_led(port, state)` | 2 | Set 3-color LED state |
| `set_light_sensor_led(port, state)` | 2 | Set light sensor LED state |
| `set_motor_straight_angle(left_port, right_port, speed, angle)` | 4 | Set motor straight angle |
| `line_intersection_stop(speed, type)` | 2 | Stop at line intersection |
| `set_mp3_play(index)` | 1 | Play MP3 track (adapted to active buzzer beep) |

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