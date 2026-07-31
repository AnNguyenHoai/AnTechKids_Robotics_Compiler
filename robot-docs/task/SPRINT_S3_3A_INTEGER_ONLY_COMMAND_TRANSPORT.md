# Sprint S3.3A --- Integer-Only Command Transport to RobotAPI Dummy

**Assignee:** DeepSeek\
**Architecture Owner:** ChatGPT\
**Epic:** RoboSim Compatibility\
**Milestone:** RC1 --- Interface Coverage\
**Priority:** Critical\
**Type:** Implementation\
**Prerequisite:** S3.2 corrected architecture baseline

------------------------------------------------------------------------

# 1. Objective

Implement the first scalable batch of missing RoboSim command interfaces
end-to-end:

``` text
RoboSim rcu.*
   ↓
RoboSim Adapter
   ↓
Canonical API
   ↓
Compiler
   ↓
Opcode / Bytecode
   ↓
Embedded VM dispatch
   ↓
RobotAPI
   ↓
DUMMY implementation
```

This sprint proves that new integer-only command interfaces can reach
the RobotAPI boundary without guessing physical behavior.

------------------------------------------------------------------------

# 2. APIs in Scope

Implement exactly these five APIs:

``` text
SetServo
Set3CLed
SetLightSensorLed
SetMotorStraightAngle
line_intersection_stop
```

Do not add other missing RoboSim APIs in this sprint.

## Required canonical mapping

``` text
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

`type` is retained from the existing RoboSim spec. Do not reinterpret
it.

------------------------------------------------------------------------

# 3. Architecture Rule

Every API must traverse the real infrastructure.

Forbidden:

``` text
Adapter removes call
Compiler silently ignores call
VM uses NOP
Frontend substitutes unrelated behavior
RobotAPI calls existing hardware with guessed semantics
```

Required:

``` text
real Adapter
real Compiler
real Opcode
real VM dispatch
real RobotAPI declaration/call
DUMMY only behind RobotAPI
```

------------------------------------------------------------------------

# 4. Canonical Function Registry

Add the five canonical functions to the Robot Language single source of
truth.

Follow the existing project generator architecture.

Do not manually maintain duplicate opcode definitions if the project
generator can produce them.

For each function define:

``` text
name
argument count
argument order
command/query classification
opcode
```

All five APIs are:

``` text
COMMAND
```

No return value is required.

------------------------------------------------------------------------

# 5. Argument Preservation

Arguments must survive end-to-end unchanged.

Required cases:

``` text
SetServo(1, 90)
→ RobotAPI receives 1, 90

Set3CLed(2, 1)
→ RobotAPI receives 2, 1

SetLightSensorLed(3, 0)
→ RobotAPI receives 3, 0

SetMotorStraightAngle(1, 2, 70, 360)
→ RobotAPI receives 1, 2, 70, 360

line_intersection_stop(70, 17)
→ RobotAPI receives 70, 17
```

Do not normalize, clamp, reinterpret, convert units, or reorder
parameters unless an already-frozen contract explicitly requires it.

------------------------------------------------------------------------

# 6. Four-Argument Transport --- Mandatory Architecture Check

`SetMotorStraightAngle` has four arguments.

Current instruction representation has limited direct operand slots.

Before implementation, inspect how existing compiler/VM calls transport
multiple arguments.

Do not silently drop the fourth argument.

Acceptable solutions include using existing variable/argument
conventions or a clean extension consistent with the VM architecture.

If the current bytecode format cannot safely carry four source operands,
document the issue and implement the smallest architecture-consistent
mechanism.

Do not encode two unrelated values into one integer without an explicit
reviewed contract.

The regression test must prove all four values reach RobotAPI.

------------------------------------------------------------------------

# 7. RoboSim Adapter

Update the RoboSim transformer/frontend.

Required transformations must preserve expressions where currently
supported.

Example:

``` python
rcu.SetServo(1, 90)
```

becomes canonical:

``` python
set_servo(1, 90)
```

Add frontend tests asserting exact rewritten canonical calls.

Unknown API validation behavior must remain unchanged.

------------------------------------------------------------------------

# 8. Compiler

Implement compiler handlers for the five canonical commands.

Requirements:

``` text
validate argument count
resolve arguments through normal compiler value path
emit the correct opcode
preserve argument order
produce actionable CompilerError on invalid calls
```

Do not special-case only literal constants if the existing compiler
architecture supports variables.

At minimum test both:

``` python
set_servo(1, 90)
```

and:

``` python
angle = 90
set_servo(1, angle)
```

------------------------------------------------------------------------

# 9. Opcode / Generated Artifacts

Add unique opcodes through the project's canonical
specification/generator flow.

Requirements:

``` text
no opcode collision
generated Python/C++/JSON artifacts synchronized
compiler and embedded VM use the same opcode values
```

Do not renumber existing released opcodes unless absolutely necessary.

Include opcode mapping in the implementation report.

------------------------------------------------------------------------

# 10. Embedded VM Dispatch

Add explicit dispatch cases.

Conceptually:

``` cpp
case Opcode::SetServo:
    RobotAPI::SetServo(...);
    pc++;
    break;
```

Each dispatch must call RobotAPI.

Do not implement behavior directly inside VM.

VM is transport/execution infrastructure, not hardware policy.

------------------------------------------------------------------------

# 11. RobotAPI Dummy Surface

Add declarations/implementations:

``` cpp
void SetServo(int port, int angle);

void Set3CLed(int port, int state);

void SetLightSensorLed(int port, int state);

void SetMotorStraightAngle(
    int leftPort,
    int rightPort,
    int speed,
    int angle
);

void LineIntersectionStop(
    int speed,
    int type
);
```

Implementation must be DUMMY.

Example:

``` cpp
void SetServo(int port, int angle) {
    Serial.printf(
        "[DUMMY][SetServo] port=%d angle=%d\n",
        port,
        angle
    );
}
```

Each dummy must log every received argument.

Do not drive physical hardware.

------------------------------------------------------------------------

# 12. Dummy Identification

Logs must clearly identify dummy behavior.

Required prefix:

``` text
[DUMMY]
```

This prevents interface support from being confused with physical
support.

Do not print:

``` text
Servo moved
Intersection detected
LED changed
```

because those claims would be false.

------------------------------------------------------------------------

# 13. End-to-End Test Program

Create:

``` text
examples/physical/014_interface_dummy_commands.py
```

Suggested content:

``` python
import rcu

rcu.SetServo(1, 90)
rcu.Set3CLed(2, 1)
rcu.SetLightSensorLed(3, 0)
rcu.SetMotorStraightAngle(1, 2, 70, 360)
rcu.line_intersection_stop(70, 17)
```

The program must:

``` text
rewrite
compile
generate program.h
run through VM
reach RobotAPI dummy calls
```

Expected serial evidence:

``` text
[DUMMY][SetServo] port=1 angle=90
[DUMMY][Set3CLed] port=2 state=1
[DUMMY][SetLightSensorLed] port=3 state=0
[DUMMY][SetMotorStraightAngle] leftPort=1 rightPort=2 speed=70 angle=360
[DUMMY][LineIntersectionStop] speed=70 type=17
```

Exact formatting may differ, but all arguments must be visible.

------------------------------------------------------------------------

# 14. Automated Tests

Add tests at multiple layers.

## Adapter tests

Assert:

``` text
RoboSim call → correct canonical call
```

for all five APIs.

## Compiler tests

Assert correct opcode and argument references.

Include variable-based arguments.

## VM/RobotAPI validation

Where host-side VM testing is available, verify dispatch.

Otherwise provide generated bytecode/program evidence plus physical
serial acceptance instructions.

## Regression

Run the full existing test suite.

No previously passing test may regress.

------------------------------------------------------------------------

# 15. Physical Acceptance

Physical hardware semantics are NOT under test.

Board acceptance only proves dispatch:

``` text
ESP32 VM
→ RobotAPI dummy
→ correct serial arguments
```

The Product Owner does not need to connect servo/LED hardware for this
sprint.

------------------------------------------------------------------------

# 16. Documentation Update

Update master inventory states for these five APIs after implementation:

``` text
INTERFACE_DEFINED = YES
ADAPTER_SUPPORTED = YES
COMPILER_SUPPORTED = YES
VM_SUPPORTED = YES
ROBOT_API_SUPPORTED = YES
IMPLEMENTATION_STATE = DUMMY
```

Do NOT mark:

``` text
PHYSICAL = REAL
FULL COMPATIBILITY
```

Update coverage metrics using denominator:

``` text
29
```

If all five pass, interface pipeline coverage should move from:

``` text
9 / 29 = 31.0%
```

to:

``` text
14 / 29 = 48.3%
```

Real physical implementations remain:

``` text
9 / 29
```

Dummy implementations become:

``` text
5 / 29
```

------------------------------------------------------------------------

# 17. Non-Goals

Do NOT implement:

``` text
GetLightSensorData
GetTraceV2I2CState
GetTraceV2I2C

SetMoveInitialize
SetMoveRunAngle
line_set_initialize

_thread

real servo control
real LED control
real encoder movement
real line intersection behavior
```

Do not solve string transport in this sprint.

------------------------------------------------------------------------

# 18. Required Report

Create:

``` text
robot-docs/robosim/S3_3A_INTEGER_COMMAND_TRANSPORT_REPORT.md
```

Include:

``` text
changed files
canonical mappings
opcode assignments
four-argument transport design
RobotAPI dummy declarations
test results
serial acceptance instructions
updated coverage
known limitations
```

Explicitly state:

``` text
Interface-supported does not mean physically implemented.
```

------------------------------------------------------------------------

# 19. Acceptance Criteria

S3.3A PASS requires:

-   [ ] All five RoboSim APIs rewrite correctly.
-   [ ] All five canonical APIs compile.
-   [ ] Unique opcodes are generated/synchronized.
-   [ ] VM has explicit dispatch for all five.
-   [ ] RobotAPI exposes all five interfaces.
-   [ ] All five RobotAPI implementations are clearly DUMMY.
-   [ ] Every argument reaches RobotAPI unchanged.
-   [ ] `SetMotorStraightAngle` preserves all four arguments.
-   [ ] Variable arguments work, not only literals.
-   [ ] Existing tests remain PASS.
-   [ ] End-to-end example builds successfully.
-   [ ] Board serial logs can prove VM → RobotAPI dispatch.
-   [ ] Inventory/coverage documentation is updated.
-   [ ] No physical semantics are guessed.
-   [ ] No string transport is introduced.

------------------------------------------------------------------------

# 20. Review Gate

``` text
S3.3A implementation
        ↓
Code + generated-artifact review
        ↓
Automated regression
        ↓
Board dummy-dispatch acceptance
        ↓
PASS?
 ├── NO → correction
 └── YES
        ↓
14/29 interface pipeline coverage
        ↓
S3.3B Query Transport
```

DeepSeek must stop after S3.3A and return the implementation for review.

------------------------------------------------------------------------

# Definition of Done

A RoboSim program containing the five selected integer-only commands can
be compiled and executed on the embedded VM, and each call arrives at
the correct RobotAPI dummy function with every argument preserved
exactly, while no physical behavior is falsely implemented or claimed.
