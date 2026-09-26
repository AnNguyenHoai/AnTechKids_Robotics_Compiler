# Line-Mask Reactive Fast Path

Status: additive runtime/API contract for VM-RT #384.

## Canonical mask

The three line sensors are represented by one 3-bit mask:

| Mask | Meaning | LinePerception state |
|---|---|---|
| `000` | no line | `LOST` |
| `001` | right | `RIGHT` |
| `010` | center | `CENTER` |
| `011` | center + right | `CENTER_RIGHT` |
| `100` | left | `LEFT` |
| `101` | left + right without center | `UNKNOWN` (ambiguous) |
| `110` | left + center | `LEFT_CENTER` |
| `111` | all sensors | `INTERSECTION` |

Canonical bits are therefore:

- `LineMask::LEFT   = 0b100`
- `LineMask::CENTER = 0b010`
- `LineMask::RIGHT  = 0b001`

This matches `LineSensorSnapshot`, `RobotAPI::GetTraceRaw()`, and `LinePerception`.

## Reactive fast path

`RobotAPI::LineBasis(speed)` is the supported high-level fast path:

```text
one coherent L/C/R mask
        -> one LineFollower::update(mask, speed, left, right)
        -> one setMotorsDirect(left, right)
```

For custom logic, RoboSim/Python can explicitly request the existing raw mask API (`GetTraceV2I2CData` -> canonical `get_trace_raw` -> VM `GetTraceRaw`). This uses one sensor opcode instead of three independent `GetTraceState` opcodes before branch/actuator work.

## Compatibility rules

- Existing per-channel `GetTraceV2I2CState` / `GetTraceState` behavior remains unchanged.
- `GetTraceRaw` keeps opcode number `44`; no ISA renumbering is introduced by #384.
- The compiler must not pattern-match three per-channel getters into a line-follow special case.
- Hardware/domain semantics stay in the line/RobotAPI layer; the generic VM scheduler remains hardware-agnostic.
- One `LineBasis` invocation must issue at most one motor command from one mask decision.

## Physical qualification

This contract proves topology and dispatch reduction only. It does not approve a physical latency threshold. `docs/VM_RESPONSIVENESS_THRESHOLDS.json` remains `UNAPPROVED_PENDING_PHYSICAL_EVIDENCE` until the #312/#325 campaign is complete.
