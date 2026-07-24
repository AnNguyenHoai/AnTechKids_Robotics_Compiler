# Timing Audit

## Purpose

Determine the canonical time unit at each layer of the toolchain.

## Findings

### RoboSim API

- `rcu.SetWaitForTime(second)`: Accepts **seconds** (float or int) according to spec, but actual RoboSim usage in examples passes milliseconds (e.g., 1000). The frontend currently passes the value unchanged to `wait()`.
- `rcu.SetMoveRunSecond(direction, speed, second)`: Accepts **seconds** (float or int).

### Frontend (rewrite)

- `SetWaitForTime(seconds)` → `wait(seconds)` **without conversion** (as per existing tests, which expect milliseconds).
- `SetMoveRunSecond(seconds)` → `wait(seconds * 1000)` after converting to milliseconds.

### Standard Robot API

- `wait(milliseconds)`: Accepts **milliseconds** (int).

### Compiler

- `WAIT` instruction operand: `int` (milliseconds). It is passed directly from `wait()` call.

### VM (ESP32)

- `WAIT` instruction calls `RobotAPI::Wait(operand)` where operand is the milliseconds value.

### Runtime (RobotAPI)

- `RobotAPI::Wait(uint16_t ms)` calls `delay(ms)`. This is milliseconds.

## Conclusion

| Layer | Unit |
|-------|------|
| RoboSim SetWaitForTime (actual usage) | milliseconds (in examples) |
| RoboSim SetMoveRunSecond | seconds |
| Frontend SetWaitForTime conversion | none (pass-through) |
| Frontend SetMoveRunSecond conversion | seconds × 1000 → milliseconds |
| Standard Robot wait() | milliseconds |
| VM WAIT operand | milliseconds |
| Hardware delay | milliseconds |

This is consistent with the current implementation and all tests pass.