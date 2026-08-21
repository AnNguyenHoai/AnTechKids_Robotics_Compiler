# C2 Result — VM Dispatch Completion

## Scope completed

C2 traced the C1-reported VM dispatch gaps against the **actual compiler handlers** and ESP32 platform surface.

### Verified live gap fixed

`LineMillisecond` was the only C1-listed capability whose compiler handler actively emitted `Opcode::LineMillisecond` while `robot-platform/main/src/Services/VM/VM.cpp` had no dispatch case.

Implemented:

```text
line_millisecond(speed, milliseconds)
    ↓
Opcode::LineMillisecond (59)
    ↓
ESP32 VM
    ↓
RobotAPI::LineMillisecond(speed, milliseconds)
    ↓
LineFollower + motor output
```

### C1 over-count correction

The remaining 11 names from the C1 list are not active compiler → opcode paths today:

- `MoveInitialize` → compiler emits `NOP`
- `MoveRunAngle` → compiler emits `NOP`
- `GetLightSensorData` → compiler emits `LoadConst(0)` stub
- `SetSeeringEngine` → compiler emits `NOP`
- `SetSeeringEngineTime` → compiler emits `NOP`
- `SetMotor` → compiler emits `NOP`
- `SetMotorServo` → compiler emits `NOP`
- `LineSetInitialize` → compiler emits `NOP`
- `SetLizard` → compiler emits `NOP`
- `UpdateVar` → no runtime bytecode (GUI-only)
- `DisplayVariable` → no runtime bytecode (GUI-only)

C2 deliberately did **not** add dead VM cases for these because their semantics are not active in the current compiler execution path.

## Files changed

```text
robot-platform/main/src/Services/VM/VM.cpp
robot-platform/main/src/Services/Robot/RobotAPI.h
robot-platform/main/src/Services/Robot/RobotAPI.cpp
docs/ROBOSIM_COVERAGE_MATRIX.md
docs/C2_VM_DISPATCH_CONTRACT.md
docs/C2_RESULT.md
tests/c2/test_vm_dispatch_completion.py
```

## Implementation behavior

`RobotAPI::LineMillisecond()`:

- checks robot readiness;
- stops immediately for non-positive duration;
- resets the existing `LineFollower`;
- samples the existing line sensor path;
- updates the existing `LineFollower`;
- applies the resulting motor output;
- runs for the requested elapsed milliseconds;
- stops the follower and motors at completion.

No changes were made to Ultrasonic, IMU, PWM diagnostics, compiler opcode numbering, or existing VM semantics.

## Verification

### C2 source/contract tests

```text
test_compiler_emits_line_millisecond: PASS
test_esp32_vm_dispatch_exists: PASS
test_robot_api_contract_exists: PASS
test_no_c2_dead_dispatch_cases_required: PASS
```

Result: **4/4 PASS**

### Existing regression suite

`run_all_tests.py` completed successfully:

```text
Compiler tests: PASS
Frontend tests: PASS
End-to-end tests: 8/8 PASS
Overall: PASS
```

### ESP32 firmware build

Not performed in this environment because PlatformIO (`pio`) is not installed.

Therefore C2 is **source/test PASS**, with **physical firmware compile still required on the development machine**.

## Next completion target

C3 should focus on **API/Hardware E2E coverage**, not more VM dispatch stubs.

Priority should be given to capabilities that are already backed by real RobotAPI/platform implementations and are currently only compile/rewrite tested.
