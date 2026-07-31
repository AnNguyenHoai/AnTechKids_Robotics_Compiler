# RoboSim Canonical Interface Contract — Corrected Candidate

**Version:** 0.9.1  
**Status:** Candidate for Interface Contract freeze after review

## Design principle

For known operations, existing stable canonical primitives may be reused.

For APIs with unresolved semantics:

> Canonicalize syntax and transport, **not guessed meaning**.

Therefore unknown RoboSim names remain recognizable at the canonical boundary.

## Canonical interfaces

| RoboSim API | Canonical interface | RoboSim arguments | Canonical arguments | Kind | Semantic status |
|---|---|---|---|---|---|
| SetMoveInitialize | `set_move_initialize` | `(left_motor, right_motor, reverse)` | same | COMMAND | PARTIAL |
| SetMoveRun | existing motion primitives / established mapping | `(direction, speed)` | established | COMMAND | KNOWN |
| SetMoveRunSecond | established expansion | `(direction, speed, second)` | motion + `wait(ms)` + stop | COMMAND | KNOWN |
| SetMoveRunAngle | `set_move_run_angle` | `(direction, speed, angle)` | same | COMMAND | PARTIAL |
| SetMoveSpeed | `set_motor_speed` | `(left_speed, right_speed)` | same | COMMAND | KNOWN |
| SetMoveStop | `stop` | `()` | `()` | COMMAND | KNOWN |
| GetLightSensorData | `get_light_sensor_data` | `(port)` | same | QUERY | UNKNOWN |
| GetLightSensor | existing `read_light` | `(port)` | `(port)` | QUERY | CURRENTLY ESTABLISHED |
| GetUltrasound | existing `read_ultrasonic` mapping | `(port)` | current established mapping | QUERY | KNOWN |
| GetTouch | existing `read_touch` | `(port)` | `(port)` | QUERY | KNOWN |
| GetTraceV2I2CState | `get_trace_v2_i2c_state` | `(arg0, arg1)` | same | QUERY | UNKNOWN |
| GetTraceV2I2C | `get_trace_v2_i2c` | `(arg0, arg1)` | same | QUERY | UNKNOWN |
| GetTraceV2I2CChxState | existing `read_line` mapping | `(port, channel)` | established channel mapping | QUERY | ESTABLISHED/ADAPTED |
| line_basis | `line_basis` | `(speed)` | same | COMMAND | UNKNOWN |
| line_millisecond | `line_millisecond` | `(speed, millisecond)` | same | COMMAND | UNKNOWN |
| line_intersection_stop | `line_intersection_stop` | `(speed, type)` | same | COMMAND | UNKNOWN |
| line_turn_encounterline | `line_turn_encounterline` | `(speed, angle, direction)` | same | COMMAND | UNKNOWN |
| line_for_bmp | `line_for_bmp` | `(speed, degree)` | same | COMMAND | UNKNOWN |
| line_set_initialize | `line_set_initialize` | `(arg0, arg1, arg2)` | same | COMMAND | UNKNOWN |
| SetMotor | `set_motor` | `(port, speed)` | same | COMMAND | PARTIAL |
| SetMotorServo | `set_motor_servo` | `(port, speed, angle)` | same | COMMAND | PARTIAL |
| SetMotorStraightAngle | `set_motor_straight_angle` | `(left_port, right_port, speed, angle)` | same | COMMAND | PARTIAL |
| SetServo | `set_servo` | `(port, angle)` | same | COMMAND | PARTIAL |
| SetSeeringEngine | `set_seering_engine` | `(port, angle)` | same | COMMAND | PARTIAL |
| SetSeeringEngineTime | `set_seering_engine_time` | `(port, angle, millisecond)` | same | COMMAND | PARTIAL |
| SetLightSensorLed | `set_light_sensor_led` | `(port, state)` | same | COMMAND | PARTIAL |
| Set3CLed | `set_3c_led` | `(port, state)` | same | COMMAND | PARTIAL |
| SetLizard | `set_lizard` | `(state)` | same | COMMAND | UNKNOWN |
| SetWaitForTime | `wait` | `(second:float)` | `(milliseconds:int)` | COMMAND | KNOWN |

## Time boundary

`SetWaitForTime` is intentionally not signature-identical across the boundary:

```text
RoboSim:
SetWaitForTime(second: float)

Adapter:
milliseconds = int(second * 1000)

Canonical:
wait(milliseconds: int)

VM/Firmware:
milliseconds
```

`SetMoveRunSecond` follows the same seconds → milliseconds boundary rule for its duration.

## QUERY return rule

A QUERY must preserve a real value path:

```text
RobotAPI return
→ VM destination
→ program variable/expression
```

For unresolved query semantics, the interface type may be provisionally `int32-compatible`, while the dummy RobotAPI implementation later returns a deterministic placeholder. The VM must not discard the query.

## Dummy rule

Dummy behavior is allowed **only behind RobotAPI**.

Forbidden:

```text
Adapter deletes call
Compiler ignores call
VM NOPs call
Query return path disappears
```

## String transport contract

Three current target interfaces require literal string transport if their signatures are preserved directly:

```text
SetMoveInitialize(..., reverse:string)
SetMoveRunAngle(direction:string, ...)
line_set_initialize(..., string, string)
```

The compiler's IR/ISA/binary subsystem contains string operand support and a string constant pool, but the **current physical embedded VM does not expose string values**:

```text
Instruction parameters: int32_t p1/p2/p3
VM variables: int32_t[]
```

Therefore physical VM string transport is currently **MISSING**.

S3.3 must not assume `const char*` can simply cross bytecode. Before implementing string-bearing interfaces, choose and document one transport strategy:

1. **Preferred for closed vocabularies:** lower verified string literals to stable enum/constant IDs before embedded VM.
2. **For arbitrary strings:** introduce a program string table and pass string IDs to VM/RobotAPI.
3. Do not encode raw host pointers.

Until that decision is implemented, string-bearing interfaces are `INTERFACE_DEFINED` but blocked at embedded transport.
