# S3.3A — Integer-Only Command Transport Report

**Status:** CLOSED  
**Board acceptance:** PASS  
**Physical semantics:** NOT IMPLEMENTED; RobotAPI implementations remain DUMMY.

## Scope completed

The following five RoboSim APIs now traverse the complete software interface pipeline:

```text
SetServo
Set3CLed
SetLightSensorLed
SetMotorStraightAngle
line_intersection_stop
```

Pipeline:

```text
RoboSim
→ Adapter
→ Canonical Robot Language API
→ Compiler
→ Opcode
→ Embedded VM
→ RobotAPI
→ [DUMMY]
```

## Canonical mappings

```text
rcu.SetServo(port, angle)
→ set_servo(port, angle)

rcu.Set3CLed(port, state)
→ set_3c_led(port, state)

rcu.SetLightSensorLed(port, state)
→ set_light_sensor_led(port, state)

rcu.SetMotorStraightAngle(left_port, right_port, speed, angle)
→ set_motor_straight_angle(left_port, right_port, speed, angle)

rcu.line_intersection_stop(speed, type)
→ line_intersection_stop(speed, type)
```

## Opcode assignments

```text
SetServo               = 36
Set3CLed                = 37
SetLightSensorLed       = 38
SetMotorStraightAngle   = 39
LineIntersectionStop    = 40
```

## Four-argument transport

`SetMotorStraightAngle` required four independent argument references.

The instruction representation was extended from:

```text
opcode + p1 + p2 + p3
```

to:

```text
opcode + p1 + p2 + p3 + p4
```

The compiler emits all four references and the embedded VM forwards:

```text
p1 → leftPort
p2 → rightPort
p3 → speed
p4 → angle
```

Board acceptance confirmed the expected four values reach RobotAPI.

### ABI note

Adding `p4` changes the generated/embedded instruction ABI. The current `program.h` physical flow is confirmed working. Binary/serializer paths that may independently assume three operands should remain on the architecture audit list before those paths become release-critical.

## RobotAPI implementation state

All five new functions are deliberately DUMMY and visibly log with `[DUMMY]`.

This sprint proves interface dispatch only.

It does **not** claim:

```text
servo hardware support
LED hardware support
motor-angle physical semantics
line-intersection physical behavior
```

## Test result

Automated regression reviewed for S3.3A:

```text
Compiler tests       PASS
RoboSim frontend     PASS
Integration tests    PASS
```

The Product Owner additionally built/flashed the physical test and confirmed the board produced correct RobotAPI dummy behavior.

Therefore:

```text
VM → RobotAPI dummy dispatch = PHYSICAL BOARD ACCEPTANCE PASS
```

## Coverage after S3.3A

Total target RoboSim interfaces:

```text
29
```

State:

```text
Interface pipeline supported = 14 / 29 = 48.3%
REAL implementations         = 9 / 29  = 31.0%
DUMMY implementations        = 5 / 29  = 17.2%
Missing pipeline             = 15 / 29 = 51.7%
```

`REAL + DUMMY` is the interface-coverage numerator.

DUMMY must never be counted as physical compatibility.

## Known limitations

1. The five new APIs have no real physical behavior yet.
2. String-bearing APIs remain blocked pending embedded string transport/lowering design.
3. QUERY interfaces such as `GetTraceV2I2C` are not part of S3.3A.
4. `_thread` remains a runtime/scheduler concern.
5. The expanded `p4` instruction representation should be audited against any independent binary encoder/serializer path before that path is relied upon.

## Final decision

**S3.3A CLOSED.**

The next interface milestone is **S3.3B — Query Transport**, whose key requirement is preserving:

```text
RobotAPI return value
→ VM destination
→ program expression / condition
```

without inventing sensor semantics.
