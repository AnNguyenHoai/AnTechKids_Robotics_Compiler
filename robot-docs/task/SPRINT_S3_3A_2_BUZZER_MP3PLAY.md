# Sprint S3.3A.2 --- Active Buzzer / RoboSim SetMp3Play

**Assignee:** DeepSeek\
**Architecture Owner:** ChatGPT\
**Priority:** High\
**Prerequisite:** S3.3A closed; GPIO19 physically confirmed as active
buzzer

## 1. Objective

Add RoboSim API:

``` python
rcu.SetMp3Play(index)
```

end-to-end and adapt it to the robot's active buzzer:

``` text
RoboSim SetMp3Play(index)
→ Adapter
→ canonical set_mp3_play(index)
→ Compiler
→ Opcode
→ Embedded VM
→ RobotAPI::SetMp3Play(index)
→ Active buzzer GPIO19
→ fixed 200 ms beep
→ OFF
```

This is a compatibility adaptation. The robot does not contain an MP3
player and must not pretend to play track `index`.

## 2. Frozen hardware contract

``` text
GPIO19 → Active Buzzer
HIGH   → ON
LOW    → OFF
Default boot state → OFF
Beep duration → 200 ms
```

GPIO19 has exclusive buzzer ownership. Audit the codebase for every use
of GPIO19 before implementation. If another active owner exists, stop
and report the conflict.

## 3. RoboSim semantic preservation

Preserve the source signature:

``` text
SetMp3Play(index)
```

`index` must travel unchanged through Adapter → Compiler → VM →
RobotAPI.

At RobotAPI/hardware adaptation level:

``` text
index does NOT select a physical MP3 track
index does NOT select frequency
index does NOT select GPIO
```

For the current active-buzzer platform, any accepted `index` triggers
the same 200 ms beep.

Log the index so the semantic loss is explicit:

``` text
[BUZZER] SetMp3Play index=1 -> fixed beep 200ms
```

Do not log "playing MP3" or "playing track".

## 4. Canonical API

Add:

``` text
set_mp3_play(index)
```

Classification:

``` text
COMMAND
arguments: 1
return: none
```

Add it through the project's Robot Language/source-of-truth generator
architecture. Do not manually create inconsistent duplicate opcode
definitions.

## 5. RoboSim Adapter

Required transformation:

``` python
rcu.SetMp3Play(1)
```

→

``` python
set_mp3_play(1)
```

Variable arguments must also work:

``` python
track = 3
rcu.SetMp3Play(track)
```

→

``` python
track = 3
set_mp3_play(track)
```

Add exact rewrite tests.

## 6. Compiler and opcode

Add a unique opcode without renumbering existing opcodes.

Compiler must:

``` text
validate exactly 1 argument
use normal value/reference resolution
emit SetMp3Play opcode
preserve index
support literal and variable argument
```

Synchronize generated compiler/platform artifacts.

Document the assigned opcode in the implementation report.

## 7. Embedded VM

Add explicit dispatch:

``` cpp
case Opcode::SetMp3Play:
    RobotAPI::SetMp3Play(
        mContext.mVariables[instruction.p1]
    );
    ...
```

Follow the project's established PC/instruction advancement convention
exactly.

Do not implement GPIO behavior inside VM.

## 8. RobotAPI / HAL

Expose:

``` cpp
void SetMp3Play(int index);
```

Preferred separation:

``` text
RobotAPI::SetMp3Play(index)
        ↓
Buzzer HAL/driver
        ↓
GPIO19
```

Reuse the existing HAL/device-driver pattern if present.

Initialization:

``` cpp
pinMode(BUZZER_PIN, OUTPUT);
digitalWrite(BUZZER_PIN, LOW);
```

Physical execution:

``` cpp
void SetMp3Play(int index) {
    Serial.printf(
        "[BUZZER] SetMp3Play index=%d -> fixed beep 200ms\n",
        index
    );

    digitalWrite(BUZZER_PIN, HIGH);
    delay(200);
    digitalWrite(BUZZER_PIN, LOW);
}
```

Equivalent HAL-based implementation is preferred.

### Timing note

The 200 ms blocking delay is accepted for this first physical
compatibility implementation.

Do not introduce PWM, `tone()`, LEDC frequency generation, asynchronous
timers, or scheduler work in this sprint.

## 9. Safety behavior

Buzzer must be OFF:

``` text
after initialization
after each beep
after normal SetMp3Play completion
```

Do not leave GPIO19 HIGH.

If practical within the existing architecture, ensure Stop/reset
initialization returns buzzer to OFF. Do not redesign global
emergency-stop behavior in this sprint.

## 10. LED correction included in this sprint

Update the already-agreed `Set3CLed` port adaptation:

``` text
odd RoboSim port  → GPIO33
even RoboSim port → GPIO32
```

Examples:

``` text
P1 → GPIO33
P2 → GPIO32
P3 → GPIO33
P4 → GPIO32
P5 → GPIO33
P6 → GPIO32
```

Implementation rule:

``` cpp
int pin = (port % 2 == 0)
    ? OUTPUT_LED_LEFT_PIN   // GPIO32
    : OUTPUT_LED_RIGHT_PIN; // GPIO33
```

Do not reject P3/P4/etc.

Preserve `state` behavior already physically validated.

Do not modify `SetLightSensorLed`; it remains DUMMY until its semantics
are separately resolved.

## 11. Minimal physical tests

Create a minimal RoboSim-facing buzzer test, e.g.:

``` text
examples/physical/017_buzzer_mp3play_test.py
```

Content:

``` python
import rcu

rcu.SetMp3Play(1)
rcu.SetWaitForTime(1)
rcu.SetMp3Play(3)
rcu.SetWaitForTime(1)
rcu.SetMp3Play(8)
```

Expected physical behavior:

``` text
beep 200 ms
wait
beep 200 ms
wait
beep 200 ms
```

Expected logs preserve:

``` text
index=1
index=3
index=8
```

Do not use `_thread`.

Also add/update a minimal LED parity test proving at least:

``` text
P1 → GPIO33
P2 → GPIO32
P3 → GPIO33
P4 → GPIO32
```

## 12. Tests

Required automated tests:

-   Adapter literal rewrite.
-   Adapter variable rewrite.
-   Compiler literal argument.
-   Compiler variable argument.
-   Correct unique opcode.
-   Existing regression suite PASS.
-   LED parity mapping unit/host test where practical.

Board acceptance:

-   GPIO19 buzzer beeps for approximately 200 ms per call.
-   Different indices still trigger beep.
-   Buzzer returns OFF.
-   Existing motor/sensor boot remains stable.
-   LED P3/P4 mapping works if tested.

## 13. Inventory correction

`SetMp3Play` is a newly confirmed RoboSim API and must be added to the
master inventory.

Therefore target count changes:

``` text
29 → 30 APIs
```

After SetMp3Play is implemented physically and board-accepted:

``` text
Interface-supported = 15 / 30 = 50.0%
```

Assuming the currently frozen state before this sprint is:

``` text
REAL  = 10
DUMMY = 4
MISSING = 15
```

then after buzzer PASS:

``` text
REAL    = 11
DUMMY   = 4
MISSING = 15
TOTAL   = 30
```

Do not change `SetLightSensorLed` to REAL.

If the repository documentation currently contains stale LED
counts/states from the rejected LED revision, correct them to the frozen
architecture above.

## 14. Documentation

Create:

``` text
robot-docs/robosim/S3_3A_2_BUZZER_MP3PLAY_REPORT.md
```

Include:

``` text
GPIO19 ownership audit
SetMp3Play source evidence
canonical mapping
opcode
changed files
index preservation evidence
200 ms adaptation rule
LED odd/even correction
automated tests
board test procedure
inventory/count changes
limitations
```

Explicitly state:

> `SetMp3Play(index)` is interface-compatible but physically adapted to
> a fixed-duration active-buzzer beep; MP3 track semantics are not
> implemented.

## 15. Non-goals

Do NOT implement:

``` text
MP3 decoder/player
track storage
frequency selection
passive-buzzer tone generation
PWM buzzer
async beep
_thread
Query Transport
SetLightSensorLed physical semantics
```

## 16. Acceptance criteria

-   [ ] `SetMp3Play` added to RoboSim inventory.
-   [ ] Adapter rewrites it correctly.
-   [ ] Canonical API exists.
-   [ ] Compiler supports literal and variable index.
-   [ ] Unique opcode is synchronized.
-   [ ] VM dispatch reaches RobotAPI.
-   [ ] RobotAPI receives original index.
-   [ ] GPIO19 ownership is conflict-free.
-   [ ] Buzzer initializes OFF.
-   [ ] Each call produces one fixed 200 ms beep.
-   [ ] Buzzer returns OFF.
-   [ ] No MP3/frequency semantics are falsely claimed.
-   [ ] `Set3CLed`: odd → GPIO33, even → GPIO32.
-   [ ] P3/P4 are no longer rejected.
-   [ ] `SetLightSensorLed` remains DUMMY.
-   [ ] Full regression PASS.
-   [ ] Report created.
-   [ ] DeepSeek stops for architecture + board review.

## Review gate

``` text
DeepSeek implementation
        ↓
Architecture review
        ↓
Board test
        ↓
SetMp3Play PASS?
 ├── NO → correction
 └── YES
        ↓
15/30 interface-supported
11 REAL + 4 DUMMY
        ↓
S3.3B Query Transport
```
