# Sprint S3.3A.1 --- LED Physical Implementation

**Assignee:** DeepSeek\
**Architecture Owner:** ChatGPT\
**Milestone:** RC1 --- Interface + Physical Bring-up\
**Priority:** High\
**Prerequisite:** S3.3A CLOSED + board dummy-dispatch PASS

# Objective

Replace the current RobotAPI dummy behavior for the LED interfaces with
a real hardware implementation, while preserving the already-working
RoboSim → Adapter → Compiler → VM pipeline.

In scope:

``` text
rcu.Set3CLed(port, state)
rcu.SetLightSensorLed(port, state)
```

Do not change their frontend/compiler/opcode semantics unless required
to fix a proven bug.

# 1. First task: hardware/pin audit

Before writing the driver, inspect the current codebase for:

``` text
LED pin definitions
RGB/3C LED pin definitions
light-sensor LED pin
GPIO reuse/conflicts
Initialize()/pinMode()/ledcAttach()
sensor initialization
motor initialization
all writes to the selected GPIOs
```

This is mandatory because the project has previously had GPIO ownership
conflicts.

Create a small table in the implementation report:

  Function     GPIO(s) Owner   Other writer?   Safe?
  ---------- --------- ------- --------------- -------

Do not select or repurpose GPIOs silently.

If the hardware mapping is absent/ambiguous, STOP at the mapping
question and report it instead of inventing pins.

# 2. GPIO ownership rule

Each physical LED GPIO must have one clear owner.

Add/maintain pin definitions in the project's central pin/config layer
rather than scattering raw GPIO numbers through RobotAPI.

RobotAPI must not directly hard-code board pin numbers.

Preferred structure:

``` text
RobotAPI
   ↓
LED driver / HAL
   ↓
central pin definition
   ↓
ESP32 GPIO
```

If the existing architecture has an established HAL/device-driver
pattern, reuse it.

# 3. Set3CLed contract

Preserve the existing interface:

``` cpp
void Set3CLed(int port, int state);
```

Do not guess new RoboSim state meanings.

Inspect current RoboSim spec/examples/tests to determine only what is
evidenced about `port` and `state`.

If `state` mapping is explicitly documented, implement that mapping.

If the mapping is not evidenced, implement only the states that can be
proven and clearly report unsupported/unknown values.

Do not reinterpret `Set3CLed` into an RGB API unless RoboSim evidence
supports that interpretation.

# 4. SetLightSensorLed contract

Preserve:

``` cpp
void SetLightSensorLed(int port, int state);
```

Implement physical output only if the board has a known corresponding
LED output.

Do not confuse:

``` text
light sensor input
```

with:

``` text
light-sensor LED output
```

They must have separate ownership unless hardware documentation
explicitly shows otherwise.

# 5. Initialization

LED hardware initialization must occur through the normal hardware
initialization path.

Requirements:

``` text
pinMode/output setup happens once
known safe initial state
no visible unintended pulse where avoidable
does not overwrite motor/sensor GPIO configuration
```

Default boot state should preferably be OFF unless existing hardware
contract says otherwise.

# 6. Real vs dummy state

After physical acceptance:

``` text
Set3CLed           → REAL
SetLightSensorLed  → REAL
```

Remove `[DUMMY]` behavior only for APIs that have actually passed
physical test.

Keep useful debug logging, for example:

``` text
[LED] Set3CLed port=... state=...
```

but do not label real behavior as DUMMY.

# 7. Physical test programs

Create minimal tests, not one complex scenario.

Suggested:

``` text
examples/physical/015_led_3c_test.py
examples/physical/016_light_sensor_led_test.py
```

Each test should:

``` text
turn output ON
wait 1 second
turn output OFF
wait 1 second
repeat or terminate cleanly
```

Use RoboSim-facing APIs in the physical examples so the complete
pipeline is exercised.

Remember:

``` text
RoboSim SetWaitForTime uses seconds.
```

# 8. Serial evidence

Logs should make physical calls easy to correlate:

``` text
[LED] Set3CLed port=X state=Y
[LED] SetLightSensorLed port=X state=Y
```

Do not spam logs from low-level loops.

# 9. Regression

Run the complete existing test suite.

Verify specifically that LED initialization does not affect:

``` text
motors
ultrasonic
TCRT5000
VM startup
SerialCommandHandler
```

No existing GPIO may be unintentionally reconfigured.

# 10. Documentation

Update:

``` text
ROBOSIM_API_MASTER_INVENTORY.md
```

only after board acceptance.

Expected final state if both pass:

``` text
Set3CLed           REAL
SetLightSensorLed  REAL
```

Interface coverage remains:

``` text
14 / 29
```

because they were already interface-supported.

Physical implementation composition changes from:

``` text
REAL  = 9
DUMMY = 5
```

to:

``` text
REAL  = 11
DUMMY = 3
```

assuming both APIs pass.

Do not incorrectly increase interface coverage.

# 11. Non-goals

Do NOT:

``` text
implement buzzer yet
implement Query Transport
change line behavior
change servo implementation
implement arbitrary RGB/color semantics without evidence
modify _thread
redesign opcode numbering
```

# 12. Required report

Create:

``` text
robot-docs/robosim/S3_3A_1_LED_PHYSICAL_REPORT.md
```

Include:

``` text
GPIO ownership audit
pin mapping
RoboSim state evidence
driver/HAL architecture
changed files
physical test instructions
regression result
known limitations
```

# Acceptance criteria

-   [ ] Existing RoboSim LED calls still rewrite/compile.
-   [ ] VM reaches RobotAPI correctly.
-   [ ] GPIO ownership is audited.
-   [ ] No pin conflict exists.
-   [ ] LED initialization is deterministic.
-   [ ] `Set3CLed` physically changes the intended output for supported
    states.
-   [ ] `SetLightSensorLed` physically changes the intended output for
    supported states.
-   [ ] OFF state works.
-   [ ] Full regression passes.
-   [ ] Motor/sensor behavior is not disturbed.
-   [ ] No unsupported RoboSim state semantics are invented.
-   [ ] Report is created.
-   [ ] DeepSeek stops for board acceptance/review.

# Review gate

``` text
DeepSeek implementation
       ↓
Architecture/code review
       ↓
Product Owner board test
       ↓
LED physical PASS?
  ├── NO → diagnose/correct
  └── YES
        ↓
Set3CLed + SetLightSensorLed = REAL
        ↓
S3.3A.2 — Buzzer
```

DeepSeek must not start buzzer implementation automatically.
