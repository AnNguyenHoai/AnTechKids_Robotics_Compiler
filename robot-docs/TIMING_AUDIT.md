# Timing Audit

## Purpose

Determine the canonical time unit at each layer of the toolchain.

## Findings

### RoboSim API

- `rcu.SetWaitForTime(second)`: accepts **seconds** (float/int). The RoboSim boundary converts with `int(second * 1000)` before canonical `wait(milliseconds)`.
- `rcu.SetMoveRunSecond(direction, speed, second)`: Accepts **seconds** (float or int).

### Frontend (rewrite)

- `SetWaitForTime(seconds)` → `wait(int(seconds * 1000))`; canonical `wait()` uses **milliseconds**.
- `SetMoveRunSecond(seconds)` → `wait(seconds * 1000)` after converting to milliseconds.

### Standard Robot API

- `wait(milliseconds)`: Accepts **milliseconds** (int).

### Compiler

- `WAIT` instruction operand: `int` (milliseconds). It is passed directly from `wait()` call.

### VM (ESP32)

- `WAIT` instruction calls `RobotAPI::Wait(operand)` where operand is the milliseconds value.

### Runtime (RobotAPI)

- `RobotAPI::Wait(uint32_t ms)` calls `delay(ms)`. This is milliseconds.

## Conclusion

| Layer | Unit |
|-------|------|
| RoboSim SetWaitForTime | seconds |
| RoboSim SetMoveRunSecond | seconds |
| Frontend SetWaitForTime conversion | seconds × 1000 → milliseconds |
| Frontend SetMoveRunSecond conversion | seconds × 1000 → milliseconds |
| Standard Robot wait() | milliseconds |
| VM WAIT operand | milliseconds |
| Hardware delay | milliseconds |

This is consistent with the current implementation and all tests pass.