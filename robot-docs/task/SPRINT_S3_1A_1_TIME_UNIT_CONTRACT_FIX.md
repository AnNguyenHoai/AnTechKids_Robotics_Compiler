# Sprint S3.1A.1 --- Time Unit Contract Fix

**Assignee:** DeepSeek\
**Epic:** RoboSim Compatibility\
**Milestone:** RC1 --- RoboSim Line Robot Compatibility\
**Priority:** High / Correction\
**Type:** Contract Fix + Implementation + Regression\
**Prerequisite:** S3.1A implementation and physical `SetMoveSpeed`
acceptance PASS

------------------------------------------------------------------------

# 1. Problem

RoboSim time APIs use **seconds**, while the internal Robot Platform
`wait()`/VM/Firmware convention is **milliseconds**.

The intended boundary is:

``` text
RoboSim API
seconds
   ↓ ×1000
RoboSim Adapter / Frontend Boundary
   ↓
Robot Language
milliseconds
   ↓
Compiler / Bytecode / VM
milliseconds
   ↓
RobotAPI / Runtime
milliseconds
```

`SetMoveRunSecond()` already follows this convention.

However, the RoboSim transformer path for:

``` python
rcu.SetWaitForTime(seconds)
```

currently rewrites the argument directly to:

``` python
wait(seconds)
```

without converting seconds → milliseconds.

Example of current incorrect behavior:

``` python
rcu.SetWaitForTime(2)
```

may become:

``` python
wait(2)
```

which the VM/Firmware interprets as **2 ms**, not **2 seconds**.

There is also a duration-width risk because some runtime APIs use
`uint16_t`, which overflows above 65,535 ms.

------------------------------------------------------------------------

# 2. Goal

Establish and enforce one official time-unit contract:

``` text
RoboSim public API       = seconds
Robot Platform internal  = milliseconds
Runtime duration type    = uint32_t
```

All conversion from seconds to milliseconds must occur at the RoboSim
boundary.

------------------------------------------------------------------------

# 3. Official Time Contract

Freeze the following convention for RC1:

## RoboSim-facing APIs

``` text
SetWaitForTime(seconds)
SetMoveRunSecond(direction, speed, seconds)
```

Their duration arguments are in:

``` text
SECONDS
```

Fractional seconds are allowed where RoboSim permits them.

Examples:

``` text
0.5 → 500 ms
1   → 1000 ms
2   → 2000 ms
60  → 60000 ms
120 → 120000 ms
```

## Canonical Robot Language

``` python
wait(milliseconds)
```

uses:

``` text
MILLISECONDS
```

## Compiler / Bytecode / VM / Firmware

All internal duration values use:

``` text
MILLISECONDS
```

No second-to-millisecond conversion should be repeated below the RoboSim
boundary.

------------------------------------------------------------------------

# 4. Fix RoboSim Transformer

Inspect:

``` text
robot-frontend-robosim/frontend/transformer.py
```

Correct:

``` python
rcu.SetWaitForTime(x)
```

so the rewritten canonical program receives milliseconds.

Expected:

``` python
rcu.SetWaitForTime(2)
```

→

``` python
wait(2000)
```

and:

``` python
rcu.SetWaitForTime(0.5)
```

→

``` python
wait(500)
```

Do not modify canonical `wait()` semantics.

------------------------------------------------------------------------

# 5. Verify SetMoveRunSecond

Do not redesign `SetMoveRunSecond()`.

Verify both supported frontend paths consistently produce:

``` text
seconds × 1000
```

before emitting canonical `wait(ms)`.

Examples:

``` python
rcu.SetMoveRunSecond("forward", 50, 0.5)
```

must ultimately contain:

``` text
wait(500)
```

and:

``` python
rcu.SetMoveRunSecond("forward", 50, 2)
```

must contain:

``` text
wait(2000)
```

If multiple compilation paths exist, ensure their observable semantics
are identical.

------------------------------------------------------------------------

# 6. Runtime Duration Width

Audit time-duration types across:

``` text
Compiler representation
Generated instruction parameters/constants
VM
RobotAPI::Wait
WaitBehavior
Scheduler-related structures if already present
```

Any duration storage that can legitimately hold RoboSim wait durations
must not truncate at 16 bits.

Preferred runtime type:

``` cpp
uint32_t
```

At minimum correct:

``` cpp
RobotAPI::Wait(uint32_t ms)
```

if it is currently `uint16_t`.

Also inspect any:

``` cpp
uint16_t durationMs
```

used for wait duration and migrate to `uint32_t` where appropriate.

Do not perform unrelated scheduler implementation.

------------------------------------------------------------------------

# 7. Important Compiler/Bytecode Audit

Do not assume changing `RobotAPI::Wait()` to `uint32_t` alone solves
long waits.

Verify that:

``` text
120 seconds
→ 120000 milliseconds
```

can survive the entire path:

``` text
Frontend
→ Constant representation
→ Instruction / bytecode
→ VM variable/value storage
→ RobotAPI
```

without truncation.

If an existing bytecode operand is too small but the VM stores constants
in a wider variable representation, document how the value is preserved.

If the current bytecode architecture fundamentally cannot represent
`120000`, report the blocker instead of silently clamping.

------------------------------------------------------------------------

# 8. Regression Tests

Add explicit automated tests for:

## SetWaitForTime

``` text
0.5 s  → 500 ms
1 s    → 1000 ms
2 s    → 2000 ms
60 s   → 60000 ms
120 s  → 120000 ms
```

## SetMoveRunSecond

At minimum:

``` text
0.5 s → 500 ms
2 s   → 2000 ms
```

Test the generated rewrite/IR/instructions at the deepest practical
layer.

Do not only test that compilation succeeds; assert the actual converted
duration.

------------------------------------------------------------------------

# 9. Fractional Conversion Rule

Use a deterministic conversion rule equivalent to:

``` text
milliseconds = int(seconds * 1000)
```

unless existing RoboSim evidence defines different rounding semantics.

Examples:

``` text
0.5   → 500
1.25  → 1250
0.001 → 1
```

Do not introduce floating-point time units into VM/Firmware.

------------------------------------------------------------------------

# 10. Invalid Inputs

Preserve existing compiler validation where possible.

Document behavior for:

``` text
negative duration
zero duration
non-numeric duration
```

Do not invent new RoboSim semantics without evidence.

At minimum, negative duration must not become an unsigned wraparound
such as a huge positive wait.

------------------------------------------------------------------------

# 11. Documentation

Update relevant specification/documentation so the unit is explicit.

Required contract wording:

``` text
RoboSim time API unit: seconds
Canonical wait unit: milliseconds
VM/Firmware wait unit: milliseconds
```

Remove or correct examples that incorrectly imply:

``` python
rcu.SetWaitForTime(1000)
```

means 1000 milliseconds.

If an old example is intentionally a 1000-second wait, document that
explicitly; otherwise correct it.

------------------------------------------------------------------------

# 12. Scope Restrictions

Do NOT implement:

``` text
_thread scheduler
cooperative wait/yield
line_* behaviors
unknown Patrol APIs
GetLightSensorData
SetMoveRunAngle
```

This sprint fixes **time units and duration representation only**.

Current blocking `delay(ms)` behavior may remain until the dedicated
scheduler sprint.

------------------------------------------------------------------------

# 13. Deliverables

Provide:

``` text
1. Source changes
2. Regression tests
3. Updated time-unit documentation/spec
4. Full existing test-suite results
5. S3.1A.1 correction report
```

Create:

``` text
robot-docs/robosim/S3_1A_1_TIME_UNIT_FIX_REPORT.md
```

Report must include:

-   Root cause
-   Changed files
-   Final unit contract
-   Duration type audit
-   Evidence that 120000 ms survives end-to-end
-   Regression results
-   Known limitations

------------------------------------------------------------------------

# 14. Acceptance Criteria

Sprint PASS requires:

-   [ ] `SetWaitForTime(0.5)` produces 500 ms.
-   [ ] `SetWaitForTime(2)` produces 2000 ms.
-   [ ] `SetWaitForTime(120)` can represent 120000 ms without
    truncation.
-   [ ] `SetMoveRunSecond(..., 0.5)` still produces 500 ms.
-   [ ] `SetMoveRunSecond(..., 2)` produces 2000 ms.
-   [ ] Canonical `wait()` remains milliseconds.
-   [ ] VM/Firmware wait remains milliseconds.
-   [ ] Runtime duration width is audited and corrected where necessary.
-   [ ] Negative duration cannot wrap into a huge unsigned delay.
-   [ ] Existing test suite has no regression.
-   [ ] No unrelated scheduler or unknown RoboSim API implementation is
    introduced.

------------------------------------------------------------------------

# 15. Review Gate

After completion:

``` text
S3.1A.1
   ↓
Code + Contract Review
   ↓
PASS?
 ├── NO → correction
 └── YES
       ↓
Time Contract CLOSED
       ↓
Continue S3.1B Behavioral Experiments
```

DeepSeek must not automatically begin the next sprint.

------------------------------------------------------------------------

# Definition of Done

The following two RoboSim programs:

``` python
rcu.SetWaitForTime(2)
```

and:

``` python
rcu.SetMoveRunSecond("forward", 50, 2)
```

must both represent **2 seconds** at the RoboSim level and exactly
**2000 milliseconds** inside the Robot Platform, with no truncation or
double conversion anywhere in the pipeline.
