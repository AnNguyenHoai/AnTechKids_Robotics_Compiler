# Sprint S3.1B --- RoboSim Behavioral Experiments

**Assignee:** DeepSeek + Product Owner for RoboSim execution\
**Epic:** RoboSim Compatibility\
**Milestone:** RC1 --- RoboSim Line Robot Compatibility\
**Priority:** Critical\
**Type:** Controlled Experiment / Semantic Verification\
**Prerequisite:** S3.1A + S3.1A.1 CLOSED\
**Implementation:** Forbidden except experiment/test assets

------------------------------------------------------------------------

# 1. Objective

Determine the real semantics of the remaining RoboSim APIs by controlled
RoboSim experiments.

Target APIs:

``` text
GetLightSensorData()
GetLightSensor()

GetTraceV2I2CState()
GetTraceV2I2C()
GetTraceV2I2CChxState()

SetMoveRunAngle()

line_set_initialize()
line_basis()
line_intersection_stop()
line_turn_encounterline()
line_for_bmp()
```

The result will be used to freeze:

``` text
ROBOSIM_RC1_API_CONTRACT v1.0
```

Do not infer behavior from API names.

------------------------------------------------------------------------

# 2. Working Model

DeepSeek prepares minimal experiments.

Product Owner runs them in RoboSim and records:

``` text
Generated Python
Observed sensor values
Observed robot motion
Blocking/non-blocking behavior
Termination condition
Parameter-dependent differences
```

Then evidence is incorporated into the contract.

------------------------------------------------------------------------

# 3. Rule --- One Unknown at a Time

Each experiment must isolate one semantic question.

Bad:

``` python
if rcu.GetTraceV2I2CState(...):
    rcu.line_basis(...)
```

This mixes sensor and behavior semantics.

Good:

``` python
value = rcu.GetTraceV2I2CState(...)
```

and inspect only that API.

Do not use complex multi-thread programs for semantic discovery.

------------------------------------------------------------------------

# 4. Experiment Group A --- Light Sensor

## A1 --- GetLightSensorData

Create the smallest RoboSim project using:

``` python
rcu.GetLightSensorData(1)
```

Test the sensor over at least:

``` text
black surface
white surface
intermediate/gray surface if RoboSim permits
```

Record returned values.

Questions:

``` text
Is return digital?
Is return boolean?
What values represent black/white?
Does distance/light intensity affect it?
What does port mean?
```

## A2 --- GetLightSensor

Repeat with:

``` python
rcu.GetLightSensor(1)
```

Record multiple values while changing the same environmental condition.

Compare A1 and A2 directly.

Required conclusion:

``` text
GetLightSensorData vs GetLightSensor
```

must be based on observed behavior.

------------------------------------------------------------------------

# 5. Experiment Group B --- Patrol Card Read APIs

Use a simple line map and position the Patrol Card in controlled
locations.

Test positions:

``` text
P1 — centered on line
P2 — slightly left
P3 — strongly left
P4 — slightly right
P5 — strongly right
P6 — completely off line
P7 — intersection / wide black region
```

## B1 --- GetTraceV2I2CChxState

Read multiple channel indices.

At minimum:

``` text
channel 1
channel 2
channel 4
channel 8
```

If numbering differs, record it.

Determine:

``` text
channel range
left-to-right ordering
black/white return convention
return type
```

## B2 --- GetTraceV2I2CState

Run the same P1--P7 positions.

Vary the second argument independently if applicable.

Determine whether it represents:

``` text
channel
state type
threshold
mode
something else
```

Do not map it to `read_line()` until verified.

## B3 --- GetTraceV2I2C

Run the same P1--P7 positions.

Record exact returned values.

Determine whether output represents:

``` text
raw reflectance
line position
percentage
error
bit mask
other
```

Special attention:

The existing acceptance program contains:

``` python
rcu.GetTraceV2I2C(1, 1) == 50
```

Determine under what physical/simulation condition value `50` occurs.

------------------------------------------------------------------------

# 6. Experiment Group C --- SetMoveRunAngle

Create isolated tests such as:

``` python
rcu.SetMoveRunAngle("forward", 50, 50)
```

Then vary one parameter at a time.

Suggested angle values:

``` text
10
50
90
180
360
```

Suggested directions:

``` text
forward
backward
turnleft
turnright
```

Questions:

``` text
What physically rotates?
What does angle measure?
What is the unit?
Does function block until completion?
Does speed affect final displacement or only execution rate?
Does 360 correspond to one wheel revolution?
Does turnright 90 mean chassis rotates 90 degrees?
```

Do not implement time approximation during this sprint.

------------------------------------------------------------------------

# 7. Experiment Group D --- line_set_initialize

Isolate:

``` python
rcu.line_set_initialize(1, "black", "wheeledchassis")
```

Vary:

``` text
port/device index
"black" / other available color option
"wheeledchassis" / other available mode if UI permits
```

Observe:

``` text
Does robot move?
Does it return immediately?
Does it change subsequent Patrol behavior?
Is it configuration-only?
```

This experiment may need to be paired with a subsequent read/line
behavior to observe state changes, but initialization itself must remain
isolated.

------------------------------------------------------------------------

# 8. Experiment Group E --- line_basis

Run:

``` python
rcu.line_basis(70)
```

on a map with a curved or displaced line.

Observe:

``` text
Does robot start following the line?
Does it block?
When does it return?
Does it run indefinitely?
How does speed parameter affect behavior?
What happens when line is lost?
```

Test at least two speeds.

------------------------------------------------------------------------

# 9. Experiment Group F --- line_intersection_stop

Run:

``` python
rcu.line_intersection_stop(70, 17)
```

on a path containing an intersection.

Vary the second parameter:

``` text
1
2
10
17
20
```

if RoboSim accepts these values.

Determine:

``` text
What causes termination?
Does robot line-follow before intersection?
What does parameter 2 mean?
Distance?
sensor threshold?
intersection type?
offset?
```

Record motion from call start until return.

------------------------------------------------------------------------

# 10. Experiment Group G --- line_turn_encounterline

Run:

``` python
rcu.line_turn_encounterline(70, 20, 1)
```

with controlled initial orientation.

Vary one parameter at a time.

Determine:

``` text
Does robot rotate until detecting line?
Which direction?
Meaning of parameter 20?
Meaning of parameter 1?
Does it stop after detecting line?
Does it align with line or only detect it?
Blocking behavior?
```

------------------------------------------------------------------------

# 11. Experiment Group H --- line_for_bmp

Run:

``` python
rcu.line_for_bmp(70, 360)
```

Test second argument:

``` text
90
180
360
720
```

Determine whether it represents:

``` text
encoder angle
distance
wheel rotation
time
line travel amount
other
```

Record:

``` text
distance traveled
wheel/chassis behavior
termination
relationship between parameter and movement
```

------------------------------------------------------------------------

# 12. Evidence Format

Create:

``` text
robot-docs/robosim/ROBOSIM_RC1_BEHAVIORAL_EXPERIMENTS.md
```

For every experiment:

``` text
## Experiment ID

API:
Question:

Input:
Environment/setup:

Generated Python:
...

Observed result:
...

Returned values:
...

Blocking:
YES / NO / UNKNOWN

Parameter observations:
...

Conclusion:
...

Confidence:
HIGH / MEDIUM / LOW

Remaining unknowns:
...
```

Do not write a conclusion before recording observations.

------------------------------------------------------------------------

# 13. Product Owner Test Sheet

Also create:

``` text
robot-docs/robosim/ROBOSIM_RC1_MANUAL_TEST_SHEET.md
```

This must be optimized for quick manual execution.

Use a table:

  ID   API   Setup   Action   What to Record
  ---- ----- ------- -------- ----------------

The Product Owner should be able to execute experiments without reading
implementation details.

------------------------------------------------------------------------

# 14. Experiment Assets

Where useful, create minimal source examples under:

``` text
examples/robosim_semantics/
```

One file per API/question.

Example naming:

``` text
001_light_sensor_data.py
002_light_sensor.py
003_trace_ch_state.py
004_trace_state.py
005_trace_value.py
006_move_angle.py
007_line_initialize.py
008_line_basis.py
009_line_intersection_stop.py
010_line_turn_encounterline.py
011_line_for_bmp.py
```

These are experiment assets, not production compatibility
implementation.

------------------------------------------------------------------------

# 15. No Implementation Rule

Do NOT modify:

``` text
Compiler opcode behavior
VM behavior
RobotAPI behavior
Sensor Framework
HAL
Motor Framework
```

to support an unknown API during this sprint.

If an experiment reveals semantics clearly, document it first.

Implementation happens only after Architecture Review.

------------------------------------------------------------------------

# 16. Documentation Cleanup

While preparing this sprint, correct the known stale statements in:

``` text
robot-docs/TIMING_AUDIT.md
robot-docs/PHYSICAL_TOOLCHAIN_VALIDATION.md
```

They must reflect the frozen contract:

``` text
RoboSim time APIs = seconds
Canonical wait    = milliseconds
VM/Firmware wait  = milliseconds
```

This is documentation cleanup only.

------------------------------------------------------------------------

# 17. Expected Contract Outcomes

At completion, every target API should be classified as:

``` text
KNOWN + FULL candidate
KNOWN + ADAPTED candidate
KNOWN + UNSUPPORTED
PARTIAL
UNKNOWN
```

Do not force every API to KNOWN if RoboSim cannot provide sufficient
evidence.

------------------------------------------------------------------------

# 18. Acceptance Criteria

S3.1B PASS requires:

-   [ ] Minimal experiments exist for all target APIs.
-   [ ] Light Sensor Data vs Light Sensor is empirically compared.
-   [ ] Patrol channel ordering/convention is investigated.
-   [ ] `GetTraceV2I2CState()` semantics are investigated independently.
-   [ ] `GetTraceV2I2C()` returned values are recorded across controlled
    positions.
-   [ ] Meaning of value `50` is specifically investigated.
-   [ ] `SetMoveRunAngle()` angle semantics are investigated.
-   [ ] Every `line_*` API has an isolated behavioral experiment.
-   [ ] Blocking/non-blocking behavior is recorded.
-   [ ] Parameter effects are recorded.
-   [ ] Manual test sheet is produced.
-   [ ] Behavioral evidence document is produced.
-   [ ] No unknown API is implemented.
-   [ ] Timing documentation debt is corrected.

------------------------------------------------------------------------

# 19. Review Gate

After DeepSeek prepares the experiment package:

``` text
S3.1B Preparation
       ↓
Architecture Review
       ↓
Product Owner executes RoboSim tests
       ↓
Observed evidence returned
       ↓
Semantic Review
       ↓
RC1 API Contract v1.0
       ↓
FREEZE
```

DeepSeek must not begin compatibility implementation automatically.

------------------------------------------------------------------------

# Definition of Done

S3.1B is complete when the team can explain the behavior of the
remaining RC1 RoboSim APIs using **observations from RoboSim itself**,
rather than assumptions derived from function names or current Robot
Platform limitations.
