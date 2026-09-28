# LINE-REG-07 — Release_4 Consumer-Fresh Qualification

## Purpose

Determine whether the physical line-follow regression introduced after `Release_4_0_0` is caused by line-sensor freshness semantics rather than by the current VM scheduler, compiler, motor path, PID, or recovery logic.

Reference release:

```text
Release_4_0_0
094e7e550d49ba71d1584730e5dfe8771bb15432
```

In Release_4, each `GetTraceState()` / `GetTraceRaw()` consumer ultimately refreshed the TCRT GPIO immediately at the getter. Current production firmware instead owns one coherent `LineSensorSnapshot` per firmware cycle and consumers reuse that snapshot.

## Qualification principle

Keep all current runtime behavior unchanged except the acquisition freshness boundary.

Unchanged:

```text
compiler / bytecode
VM RunSlice
pending Wait lifecycle
firmware scheduler
motor output path
LineFollower / PID / recovery
hardware mapping
network stack
```

Changed only for qualification:

```text
TCRT5000::update()
  snapshot mode       -> reuse active cycle snapshot
  Release_4 fresh mode -> SampleHardwareDirect() at consumer time
```

The implementation reuses the existing `LINE_REGRESSION_LEGACY_ACQUISITION=1` path. No duplicate sensor algorithm is introduced.

## Profiles

Current snapshot baseline:

```text
esp32dev_line_snapshot_qualification
```

Release_4-style consumer-fresh profile:

```text
esp32dev_line_release4_fresh_qualification
```

The Release_4-style profile extends `esp32dev_line_legacy_qualification`; it adds no VM, motor, or compiler build flags.

## Physical A/B procedure

Use the same robot, battery, track, line width, sensor height, potentiometer settings, wiring, and generated student program for both runs.

### A — Current snapshot semantics

From `robot-platform`:

```powershell
python -m platformio run -e esp32dev_line_snapshot_qualification -t upload
```

From repository root:

```powershell
python tools/line_reg_udp_receiver.py --output release4_ab_snapshot.log
```

Run the target program and record whether the robot reacts immediately, overshoots the line, or loses the line.

### B — Release_4 consumer-fresh semantics

From `robot-platform`:

```powershell
python -m platformio run -e esp32dev_line_release4_fresh_qualification -t upload
```

From repository root:

```powershell
python tools/line_reg_udp_receiver.py --output release4_ab_fresh.log
```

Run the exact same program without changing sensor calibration.

## Primary student program

Use the exact program that reproduces the regression on current firmware:

```python
import rcu


def task1():
    last_turn = 0
    rcu.Set3CLed(1, 1)
    while True:
        left = rcu.GetTraceV2I2CState(1, 1)
        center = rcu.GetTraceV2I2CState(1, 2)
        right = rcu.GetTraceV2I2CState(1, 3)

        if (center and not left and not right) or (left and center and right):
            rcu.SetMoveSpeed(50, 50)
        elif left and center:
            rcu.SetMoveSpeed(20, 50)
            last_turn = 1
        elif right and center:
            rcu.SetMoveSpeed(50, 20)
            last_turn = 2
        elif left:
            rcu.SetMoveSpeed(-10, 50)
            last_turn = 1
        elif right:
            rcu.SetMoveSpeed(50, -10)
            last_turn = 2
        else:
            if last_turn == 1:
                rcu.SetMoveSpeed(-30, 40)
            elif last_turn == 2:
                rcu.SetMoveSpeed(40, -30)
            else:
                rcu.SetMoveSpeed(-30, 30)

        rcu.wait(0.01)
```

Use the repository's normal entry-point convention when compiling the program; do not otherwise modify its logic between A and B.

## Secondary basic_line check

Repeat the same A/B using the current `basic_line` program. This is secondary evidence because the custom program above bypasses `LineFollower` and therefore isolates the sensor/VM/motor reaction path more directly.

## Interpretation

### Snapshot fails, Release_4 fresh passes

Strong evidence that the regression is caused by the current snapshot freshness policy or its firmware-cycle ownership boundary.

Next scope:

```text
LineSensorSnapshot ownership
consumer freshness contract
firmware-cycle sample timing
snapshot-vs-reactive-control policy
```

Do not tune PID/recovery to compensate for this result.

### Both fail

Snapshot reuse is not sufficient to explain the regression. Move the investigation to common post-Release_4 runtime changes, especially:

```text
RunSlice scheduling
pending Wait behavior under RunSlice
source-loop transaction boundaries
sample -> decision -> SetMotorSpeed latency
```

### Both pass

The reproduced failure depends on some other qualification/build/program condition. Reconfirm generated-program identity, wiring, power, and exact firmware commit.

## Evidence to retain

For both runs record:

- firmware commit SHA
- PlatformIO environment
- generated program instruction count/hash
- exact student source
- hardware unchanged confirmation
- sensor calibration unchanged confirmation
- UDP log
- short physical observation: immediate / delayed / overshoot / lost

Do not change production snapshot behavior based on host tests alone. Physical A/B evidence is the decision gate for LINE-REG-07.
