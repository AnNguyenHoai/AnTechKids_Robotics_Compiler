# Sprint S3.1A --- Safe RoboSim Compatibility Implementation

**Assignee:** DeepSeek\
**Epic:** RoboSim Compatibility\
**Milestone:** RC1 --- RoboSim Line Robot Compatibility\
**Priority:** Critical\
**Type:** Implementation\
**Prerequisite:** S3.0.1 Architecture Review\
**Contract:** RC1 API Contract Candidate v0.9 --- NOT FROZEN

------------------------------------------------------------------------

# 1. Objective

Implement only RoboSim capabilities whose semantics and/or required
platform behavior are sufficiently established by current evidence.

This sprint must improve the real RoboSim → Hardware vertical slice
without introducing guessed semantics.

Primary new feature:

``` text
rcu.SetMoveSpeed(left, right)
```

Also harden and regression-test the already established pipelines:

``` text
rcu.SetMoveRunSecond(...)
rcu.GetTraceV2I2CChxState(...)
rcu.GetLightSensor(...)
```

------------------------------------------------------------------------

# 2. Architecture Rule

The following principle is mandatory:

``` text
KNOWN semantics
      ↓
Implementation allowed

UNKNOWN / PARTIAL semantics
      ↓
Implementation forbidden
```

Do not increase compatibility coverage by guessing API behavior.

------------------------------------------------------------------------

# 3. Scope A --- Implement SetMoveSpeed

RoboSim input:

``` python
rcu.SetMoveSpeed(left, right)
```

Required semantic model:

``` text
left  = signed left-side motor speed
right = signed right-side motor speed
```

Target pipeline:

``` text
RoboSim
   ↓
Frontend Adapter
   ↓
set_motor_speed(left, right)
   ↓
Compiler
   ↓
SetMotorSpeed opcode
   ↓
VM
   ↓
RobotAPI
   ↓
setMotorsDirect(left, right)
   ↓
Motor Framework / HAL
   ↓
Physical motors
```

## 3.1 Frontend

Add explicit mapping/transform for:

``` python
rcu.SetMoveSpeed(left, right)
```

to a canonical Robot Language API, preferably:

``` python
set_motor_speed(left, right)
```

Do not rewrite it into `forward/backward/left/right`, because
independent signed left/right values must be preserved.

Examples:

``` text
(50, 50)    → forward
(-50, -50)  → backward
(-50, 50)   → rotate/turn one direction
(50, -50)   → rotate/turn opposite direction
(20, 70)    → differential steering
```

## 3.2 Compiler

Add canonical function support and emit a dedicated opcode.

Recommended:

``` text
Opcode::SetMotorSpeed
```

Operands must preserve both values independently.

No loss of sign.

## 3.3 VM

Add handler:

``` text
SetMotorSpeed(left, right)
```

that invokes RobotAPI.

## 3.4 RobotAPI

Expose a stable public API:

``` cpp
SetMotorSpeed(int left, int right)
```

or naming consistent with the existing RobotAPI convention.

Internally reuse the existing motor implementation such as:

``` cpp
setMotorsDirect(left, right)
```

Do not duplicate low-level motor direction/PWM logic.

## 3.5 Range

Use the platform's existing signed speed convention, expected:

``` text
-100 .. +100
```

Validate/constrain consistently with existing motion code.

------------------------------------------------------------------------

# 4. Scope B --- Harden SetMoveRunSecond

Do not redesign this API.

Existing verified transformation:

``` text
SetMoveRunSecond(direction, speed, seconds)
        ↓
motion(speed)
wait(seconds * 1000)
stop()
```

Required work:

-   Add/verify regression tests.
-   Verify all currently supported directions.
-   Verify fractional seconds such as `0.5`.
-   Verify negative/invalid speed handling follows existing contract.
-   Ensure generated rewrite remains deterministic.

Test at minimum:

``` python
rcu.SetMoveRunSecond("forward", 50, 1)
rcu.SetMoveRunSecond("backward", 50, 1)
rcu.SetMoveRunSecond("turnleft", 50, 0.5)
rcu.SetMoveRunSecond("turnright", 50, 0.5)
```

Do not change semantics merely to make tests pass.

------------------------------------------------------------------------

# 5. Scope C --- Harden GetTraceV2I2CChxState

Existing pipeline:

``` text
GetTraceV2I2CChxState(port, channel)
        ↓
read_line(channel)
        ↓
ReadLine
        ↓
RobotAPI::ReadLine(channel)
        ↓
TCRT5000
```

Required work:

-   Add frontend regression tests.
-   Add compiler regression tests.
-   Add VM/RobotAPI tests where existing test infrastructure allows.
-   Verify channel numbering used by the current physical driver.
-   Document the physical 3-eye limitation.

Important:

RoboSim Patrol Card may expose more channels than Robot v1.

Do not silently claim 8-channel FULL compatibility.

If current physical mapping is only:

``` text
Left
Center
Right
```

document exactly which logical channel numbers map to them.

Invalid/unavailable channels must have explicit behavior; do not
silently alias them to an existing eye.

------------------------------------------------------------------------

# 6. Scope D --- Harden GetLightSensor

Existing software pipeline:

``` text
GetLightSensor(port)
   ↓
read_light(port)
   ↓
ReadLight
   ↓
RobotAPI::ReadLight()
```

This sprint must only:

-   Preserve the existing mapping.
-   Add regression coverage.
-   Document hardware dependency.

Robot v1's current 3-eye TCRT5000 module is digital-only and must NOT be
used to fake an analog/raw light value.

If `ReadLight()` uses an ESP32 ADC pin intended for a separate analog
light sensor, document that clearly.

Do not change `GetLightSensor()` semantics.

------------------------------------------------------------------------

# 7. Explicitly Forbidden APIs

Do NOT implement or create mappings/opcodes for:

``` text
GetLightSensorData()
GetTraceV2I2CState()
GetTraceV2I2C()
SetMoveRunAngle()

line_set_initialize()
line_basis()
line_intersection_stop()
line_turn_encounterline()
line_for_bmp()
```

Reason:

``` text
Semantics UNKNOWN or PARTIAL
```

These APIs are handled by the parallel RoboSim behavioral investigation.

------------------------------------------------------------------------

# 8. Threading Is Out of Scope

Do NOT implement:

``` text
ThreadStart opcode
VM scheduler
ThreadContext
yielding Wait
```

in S3.1A.

Existing `_thread` behavior may remain unchanged for this sprint.

Scheduler work belongs to a later dedicated sprint after the RC1
execution model is approved.

------------------------------------------------------------------------

# 9. Tests

Add tests covering the complete safe scope.

## Frontend

At minimum:

``` text
SetMoveSpeed positive/positive
SetMoveSpeed negative/negative
SetMoveSpeed negative/positive
SetMoveSpeed positive/negative
SetMoveSpeed unequal speeds

SetMoveRunSecond directions + fractional duration

GetTraceV2I2CChxState mapping

GetLightSensor mapping
```

## Compiler

Verify canonical calls compile and opcode operands are correct.

For SetMoveSpeed, explicitly test signed values.

## VM / RobotAPI

Where possible verify:

``` text
SetMotorSpeed(50, 50)
SetMotorSpeed(-50, -50)
SetMotorSpeed(-50, 50)
SetMotorSpeed(50, -50)
SetMotorSpeed(20, 70)
SetMotorSpeed(0, 0)
```

## Regression

Run the complete existing test suite.

No previously passing test may regress.

------------------------------------------------------------------------

# 10. Physical Acceptance Program

Create a minimal physical example:

``` python
import rcu

rcu.SetMoveSpeed(50, 50)
# wait using currently supported RoboSim mechanism
rcu.SetMoveRunSecond("forward", 0, 0)  # DO NOT use this exact workaround if semantically invalid
```

The actual test program must use valid existing APIs and should exercise
signed differential motor commands safely.

Prefer a sequence equivalent to:

``` text
forward
stop
backward
stop
left differential
stop
right differential
stop
```

Do not introduce fake calls solely for testing.

Provide exact commands for building/flashing/running the example.

------------------------------------------------------------------------

# 11. Documentation Updates

Update the RC1 capability matrix after implementation.

Expected status direction:

``` text
SetMoveSpeed
Software Support: FULL
Hardware Support: FULL
Overall: FULL
```

Only mark FULL if tests and physical behavior support that claim.

Keep:

``` text
RC1 Contract Candidate v0.9
```

Do NOT rename/freeze it as v1.0 in this sprint.

------------------------------------------------------------------------

# 12. Deliverables

Provide:

``` text
1. Source changes
2. New/updated tests
3. Minimal physical SetMoveSpeed example
4. Updated capability matrix
5. S3.1A implementation report
6. Full test results
```

Create report:

``` text
robot-docs/robosim/S3_1A_IMPLEMENTATION_REPORT.md
```

The report must contain:

``` text
Changed files
Architecture mapping
New opcode/function IDs if applicable
Test results
Physical test instructions
Known limitations
No-regression statement
```

------------------------------------------------------------------------

# 13. Acceptance Criteria

S3.1A PASS requires:

-   [ ] `rcu.SetMoveSpeed(left, right)` is supported end-to-end.
-   [ ] Signed independent left/right speeds are preserved.
-   [ ] Implementation reuses existing motor control instead of
    duplicating it.
-   [ ] `SetMoveRunSecond()` regression tests pass.
-   [ ] `GetTraceV2I2CChxState()` regression tests pass.
-   [ ] Physical 3-eye channel limitation is documented.
-   [ ] `GetLightSensor()` existing pipeline is regression-tested.
-   [ ] No analog value is faked from digital TCRT5000.
-   [ ] No UNKNOWN API is implemented.
-   [ ] No VM threading/scheduler work is mixed into the sprint.
-   [ ] Existing full test suite passes.
-   [ ] Physical SetMoveSpeed test procedure is provided.
-   [ ] Capability matrix is updated.
-   [ ] Contract remains v0.9 and NOT FROZEN.

------------------------------------------------------------------------

# 14. Review Gate

After implementation:

``` text
S3.1A
  ↓
Architecture + Code Review
  ↓
Physical verification
  ↓
PASS?
 ├─ NO → correction task
 └─ YES → continue RC1
```

DeepSeek must not start the next sprint automatically.

------------------------------------------------------------------------

# Definition of Done

A RoboSim program containing:

``` python
rcu.SetMoveSpeed(left, right)
```

must successfully pass through:

``` text
RoboSim Python
→ Adapter
→ Compiler
→ Bytecode
→ VM
→ RobotAPI
→ Motor control
→ ESP32
→ Physical motors
```

with correct signed differential motor behavior, while all APIs with
unresolved semantics remain untouched.
