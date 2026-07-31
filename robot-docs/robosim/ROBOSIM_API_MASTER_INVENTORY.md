# RoboSim API Master Inventory — Architecture Corrected Baseline

**Version:** 1.1  
**Status:** Architecture-review candidate  
**Scope:** Interface Coverage milestone

## Source classes

- `SAMPLE_OBSERVED`: found in current Python examples/tests scanned in `examples/` and `robot-frontend-robosim/`.
- `RC1_OBSERVED`: present in the RC1 acceptance program but not found in the scanned Python sample corpus.
- `SPEC_ONLY`: present only in a trusted RoboSim spec and not observed in either of the above.

## Counting rule

There are **29 target RoboSim APIs** in the current interface surface:

- **26 SAMPLE_OBSERVED**
- **3 RC1_OBSERVED**
- **0 SPEC_ONLY additional APIs**

The three RC1-only APIs are:

```text
GetTraceV2I2CState
GetTraceV2I2C
line_set_initialize
```

`GetLightSensorData` is SAMPLE_OBSERVED in the current repository and must not be described as RC1-only.

## Master inventory

| RoboSim API | Source | Sample occurrences | Category | Observed/spec signature | Return used | Adapter | Compiler | VM | RobotAPI | Implementation |
|---|---|---:|---|---|---|---|---|---|---|---|
| SetMoveInitialize | SAMPLE_OBSERVED | 5 | MOTION | `(left_motor:int, right_motor:int, reverse:string)` | NO | NO | NO | NO | NO | MISSING |
| SetMoveRun | SAMPLE_OBSERVED | 6 | MOTION | `(direction:string, speed:int)` | NO | YES | YES | YES | YES | REAL |
| SetMoveRunSecond | SAMPLE_OBSERVED | 22 | MOTION | `(direction:string, speed:int, second:float)` | NO | YES | YES | YES | YES | REAL |
| SetMoveRunAngle | SAMPLE_OBSERVED | 3 | MOTION | `(direction:string, speed:int, angle:int)` | NO | NO | NO | NO | NO | MISSING |
| SetMoveSpeed | SAMPLE_OBSERVED | 16 | MOTION | `(left_speed:int, right_speed:int)` | NO | YES | YES | YES | YES | REAL |
| SetMoveStop | SAMPLE_OBSERVED | 13 | MOTION | `()` | NO | YES | YES | YES | YES | REAL |
| GetLightSensorData | SAMPLE_OBSERVED | 3 | SENSOR_LIGHT | `(port:int)` | YES | NO | NO | NO | NO | MISSING |
| GetLightSensor | SAMPLE_OBSERVED | 3 | SENSOR_LIGHT | `(port:int)` | YES | YES | YES | YES | YES | REAL |
| GetUltrasound | SAMPLE_OBSERVED | 4 | SENSOR_ULTRASONIC | `(port:int)` | YES | YES | YES | YES | YES | REAL |
| GetTouch | SAMPLE_OBSERVED | 4 | SENSOR_TOUCH | `(port:int)` | YES | YES | YES | YES | YES | REAL |
| GetTraceV2I2CState | RC1_OBSERVED | 0 | PATROL_LINE | `(arg0:int, arg1:int)` | YES | NO | NO | NO | NO | MISSING |
| GetTraceV2I2C | RC1_OBSERVED | 0 | PATROL_LINE | `(arg0:int, arg1:int)` | YES | NO | NO | NO | NO | MISSING |
| GetTraceV2I2CChxState | SAMPLE_OBSERVED | 8 | PATROL_LINE | `(port:int, channel:int)` | YES | YES | YES | YES | YES | REAL |
| line_basis | SAMPLE_OBSERVED | 3 | LINE_BEHAVIOR | `(speed:int)` | NO | NO | NO | NO | NO | MISSING |
| line_millisecond | SAMPLE_OBSERVED | 4 | LINE_BEHAVIOR | `(speed:int, millisecond:int)` | NO | NO | NO | NO | NO | MISSING |
| line_intersection_stop | SAMPLE_OBSERVED | 9 | LINE_BEHAVIOR | `(speed:int, type:int)` | NO | YES | YES | YES | YES | DUMMY |
| line_turn_encounterline | SAMPLE_OBSERVED | 6 | LINE_BEHAVIOR | `(speed:int, angle:int, direction:int)` | NO | NO | NO | NO | NO | MISSING |
| line_for_bmp | SAMPLE_OBSERVED | 2 | LINE_BEHAVIOR | `(speed:int, degree:int)` | NO | NO | NO | NO | NO | MISSING |
| line_set_initialize | RC1_OBSERVED | 0 | LINE_BEHAVIOR | `(arg0:int, arg1:string, arg2:string)` | NO | NO | NO | NO | NO | MISSING |
| SetMotor | SAMPLE_OBSERVED | 3 | MOTOR | `(port:int, speed:int)` | NO | NO | NO | NO | NO | MISSING |
| SetMotorServo | SAMPLE_OBSERVED | 3 | MOTOR | `(port:int, speed:int, angle:int)` | NO | NO | NO | NO | NO | MISSING |
| SetMotorStraightAngle | SAMPLE_OBSERVED | 10 | MOTOR | `(left_port:int, right_port:int, speed:int, angle:int)` | NO | YES | YES | YES | YES | DUMMY |
| SetServo | SAMPLE_OBSERVED | 11 | SERVO | `(port:int, angle:int)` | NO | YES | YES | YES | YES | DUMMY |
| SetSeeringEngine | SAMPLE_OBSERVED | 4 | STEERING | `(port:int, angle:int)` | NO | NO | NO | NO | NO | MISSING |
| SetSeeringEngineTime | SAMPLE_OBSERVED | 2 | STEERING | `(port:int, angle:int, millisecond:int)` | NO | NO | NO | NO | NO | MISSING |
| SetLightSensorLed | SAMPLE_OBSERVED | 8 | LED | `(port:int, state:int)` | NO | YES | YES | YES | YES | REAL  |
| Set3CLed | SAMPLE_OBSERVED | 10 | LED | `(port:int, state:int)` | NO | YES | YES | YES | YES | REAL  |
| SetLizard | SAMPLE_OBSERVED | 3 | PERIPHERAL | `(state:int)` | NO | NO | NO | NO | NO | MISSING |
| SetWaitForTime | SAMPLE_OBSERVED | 46 | SYSTEM | RoboSim `(second:float)` → canonical `wait(milliseconds:int)` | NO | YES | YES | YES | YES | REAL |
| SetMp3Play  | SAMPLE_OBSERVED | 19 | BUZZER | `(port:int, state:int)` | NO | YES | YES | YES | YES | REAL  
## Coverage baseline

Current established end-to-end supported set:

```text
SetMoveRun
SetMoveRunSecond
SetMoveSpeed
SetMoveStop
GetLightSensor
GetUltrasound
GetTouch
GetTraceV2I2CChxState
SetWaitForTime
```

Therefore:

| Layer | Count | Coverage |
|---|---:|---:|
| Interface target defined | 29 / 29 | 100.0% |
| Adapter supported | 14 / 29 | 48.3% |
| Compiler supported | 14 / 29 | 48.3% |
| VM dispatch supported | 14 / 29 | 48.3% |
| RobotAPI surface supported | 14 / 29 | 48.3% |
| REAL implementation | 11 / 29 | 31.0% |
| DUMMY implementation | 3 / 29 | 17.2% |
| Missing interface pipeline | 15 / 29 | 51.7% |

These are **interface coverage metrics**, not physical-compatibility claims.


## S3.3A update — interface-supported with DUMMY RobotAPI

The following APIs now traverse Adapter → Compiler → Opcode → VM → RobotAPI, but their physical behavior remains deliberately unimplemented:

```text
SetServo
Set3CLed
SetLightSensorLed
SetMotorStraightAngle
line_intersection_stop
```

Board acceptance has confirmed that each call reaches its RobotAPI dummy with the expected arguments, including all four arguments of `SetMotorStraightAngle`.

## Runtime/language features

Runtime constructs are not RobotAPI interfaces. `_thread.start_new_thread`, loops, functions, conditionals, `break`, `continue`, and globals remain tracked separately under Compiler/VM runtime capability.

## Semantic rule

A signature can be preserved without knowing physical semantics. Unknown meanings remain explicitly unknown. In particular, RC1 evidence only establishes that `GetTraceV2I2CState` and `GetTraceV2I2C` take two integer arguments and return numeric-compatible values; it does not establish that argument 2 is a channel.
