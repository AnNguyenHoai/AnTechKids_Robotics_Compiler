# S3.3A Status Update

S3.3A is physically accepted at the **dummy-dispatch boundary**.

Implemented end-to-end with `IMPLEMENTATION_STATE = DUMMY`:

```text
SetServo
Set3CLed
SetLightSensorLed
SetMotorStraightAngle
line_intersection_stop
```

These APIs must be removed from the missing-interface implementation queue. They remain future physical-implementation work.

Current interface pipeline coverage:

```text
14 / 29 = 48.3%
REAL  = 9
DUMMY = 5
MISSING pipeline = 15
```


# RoboSim Interface Coverage Backlog — Evidence Prioritized

**Version:** 1.1

## Frequency evidence

Counts below are literal `rcu.<API>` occurrences in the current scanned Python corpus; they are a prioritization signal, not semantic evidence.

| API | Sample occurrences |
|---|---:|
| `SetWaitForTime` | 46 |
| `SetMoveRunSecond` | 22 |
| `SetMoveSpeed` | 16 |
| `SetMoveStop` | 13 |
| `SetServo` | 11 |
| `Set3CLed` | 10 |
| `SetMotorStraightAngle` | 10 |
| `line_intersection_stop` | 9 |
| `GetTraceV2I2CChxState` | 8 |
| `SetLightSensorLed` | 8 |
| `SetMoveRun` | 6 |
| `line_turn_encounterline` | 6 |
| `SetMoveInitialize` | 5 |
| `GetTouch` | 4 |
| `GetUltrasound` | 4 |
| `SetSeeringEngine` | 4 |
| `line_millisecond` | 4 |
| `GetLightSensor` | 3 |
| `GetLightSensorData` | 3 |
| `SetLizard` | 3 |
| `SetMotor` | 3 |
| `SetMotorServo` | 3 |
| `SetMoveRunAngle` | 3 |
| `line_basis` | 3 |
| `SetSeeringEngineTime` | 2 |
| `line_for_bmp` | 2 |

RC1-only calls not found in that sample corpus:

```text
GetTraceV2I2CState
GetTraceV2I2C
line_set_initialize
```

## Priority model

Priority considers:

1. observed frequency,
2. number of samples blocked,
3. transport dependencies,
4. whether infrastructure can be reused,
5. implementation risk.

## P0 — Already established real pipeline

```text
SetWaitForTime
SetMoveRunSecond
SetMoveSpeed
SetMoveStop
SetMoveRun
GetTraceV2I2CChxState
GetUltrasound
GetTouch
GetLightSensor
```

No dummy replacement is allowed.

## P1 — High-frequency, integer-only transport

Good first implementation batch because they avoid the unresolved embedded string transport:

```text
SetServo                 (11)
SetMotorStraightAngle    (10)
Set3CLed                  (10)
line_intersection_stop    (9)
SetLightSensorLed         (8)
line_turn_encounterline   (6)
line_millisecond          (4)
SetSeeringEngine          (4)
SetMotor                  (3)
SetMotorServo             (3)
line_basis                (3)
SetLizard                 (3)
SetSeeringEngineTime      (2)
line_for_bmp              (2)
```

Unknown semantics are acceptable only because implementation stops at a clearly marked RobotAPI dummy.

## P1-BLOCKED — String transport required

```text
SetMoveInitialize
SetMoveRunAngle
line_set_initialize
```

Before these go end-to-end, S3.3 must define embedded string transport/lowering.

## P2 — Missing query interfaces

```text
GetLightSensorData
GetTraceV2I2CState
GetTraceV2I2C
```

These require correct QUERY result transport and deterministic dummy returns. The two Trace APIs are RC1-only in the current sample corpus.

## Recommended implementation decomposition

### S3.3A — Integer-only command transport

Implement a small representative batch first:

```text
SetServo
Set3CLed
SetLightSensorLed
SetMotorStraightAngle
line_intersection_stop
```

Goal: prove scalable command opcode generation/dispatch to RobotAPI dummy.

### S3.3B — Query transport

```text
GetLightSensorData
GetTraceV2I2CState
GetTraceV2I2C
```

Goal: prove RobotAPI dummy return → VM destination → expression/condition.

### S3.3C — Remaining integer-only commands

Implement remaining P1 integer-only interfaces.

### S3.3D — String transport + string-bearing APIs

First freeze enum/string-table transport, then implement:

```text
SetMoveInitialize
SetMoveRunAngle
line_set_initialize
```

### S3.4 — Sample compile campaign

Measure sample compile/dispatch coverage after interface batches.

### Later — Runtime

`_thread` remains a VM runtime/scheduler concern and is not a RobotAPI dummy interface.
