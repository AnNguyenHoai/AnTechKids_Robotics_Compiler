# C2 VM Dispatch Contract

## Scope

C2 closes the verified compiler → ESP32 VM dispatch gap without inventing semantics for compiler stubs.

## Verified live gap

### `LineMillisecond`

**Opcode:** `59` (`Opcode::LineMillisecond`)

**Compiler handler:**
`robot-compiler/compiler/handlers/line_handler.py`

The current handler emits:

```text
LineMillisecond(speed, millisecond, 0)
```

where `speed` and `millisecond` are variable indexes in the generated instruction.

**ESP32 VM contract:**

```cpp
RobotAPI::LineMillisecond(
    mContext.mVariables[instruction.p1],
    mContext.mVariables[instruction.p2]
);
```

The VM increments the program counter exactly once after the blocking RobotAPI operation.

**RobotAPI behavior:**

- reject execution if `g_robotReady` is false;
- non-positive duration stops immediately;
- sample the line sensor through `GetTraceRaw(1)`;
- update the existing `LineFollower`;
- apply the resulting motor output;
- continue until the requested elapsed milliseconds;
- stop the follower and motors at the end.

This follows the existing blocking semantics documented by the compiler registry and mirrors the execution style already used by `LineIntersectionStop`, `LineTurnEncounterLine`, and `LineForBmp`.

## Deliberately not dispatched in C2

The following generated opcode enum values exist, but their current compiler handlers do not emit the corresponding opcode:

| Opcode | Current compiler behavior | C2 status |
|---|---|---|
| `MoveInitialize` | NOP | Deferred |
| `MoveRunAngle` | NOP | Deferred |
| `GetLightSensorData` | `LoadConst(0)` | Deferred |
| `SetSeeringEngine` | NOP | Deferred |
| `SetSeeringEngineTime` | NOP | Deferred |
| `SetMotor` | NOP | Deferred |
| `SetMotorServo` | NOP | Deferred |
| `LineSetInitialize` | NOP | Deferred |
| `SetLizard` | NOP | Deferred |
| `UpdateVar` | no runtime bytecode | Deferred / GUI |
| `DisplayVariable` | no runtime bytecode | Deferred / GUI |

Adding VM cases for these now would be misleading because there is no active compiler execution path and, for some APIs, the current platform contract explicitly leaves semantics unresolved.

## Regression constraint

C2 must not change:

- opcode numbers;
- bytecode encoding;
- existing VM behavior;
- Ultrasonic/IMU/PWM behavior;
- existing movement/LED/sensor execution.

