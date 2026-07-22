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
| `wait(milliseconds)` | 1 | Wait milliseconds |
| `stop()` | 0 | Stop robot |

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