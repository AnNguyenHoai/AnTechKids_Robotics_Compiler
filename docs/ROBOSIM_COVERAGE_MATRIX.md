# RoboSim API & E2E Coverage Matrix

**Audit:** C1 — RoboSim API & E2E Coverage Audit  
**Baseline:** `04_Robotics_SW_DeepSeek(20260821-155447)`  
**Purpose:** establish the current completion boundary before implementing missing RoboSim capabilities.

## 1. Executive Summary

The current codebase contains **two compiler paths**:

1. `compiler.compiler.RobotCompiler` — the path used by `robot-compiler/main.py`, the current unit tests, and the end-to-end test harness after RoboSim frontend rewriting.
2. `compiler.frontend.compiler.FrontendCompiler` — a newer AST → IR → passes path, but its `ASTVisitor` currently recognizes only a small subset of `rcu.*` calls directly.

The RoboSim frontend transformer is substantially broader than `ASTVisitor`: it maps movement, sensors, LEDs, servo, motor, line, peripheral and GUI calls into the canonical built-in API names used by `RobotCompiler`.

**Baseline tests executed:**

- `robot-frontend-robosim/test/run_tests.py` — PASS
- `robot-compiler/tests/run_tests.py` — PASS
- `robot-compiler/integration/end_to_end/run_integration_tests.py` — 8/8 PASS

This means the existing tested path is healthy, but **PASS in the current suite does not mean the entire opcode/API surface is E2E-complete**.

## 2. Status Definitions

| Status | Meaning |
|---|---|
| PASS | Evidence exists for the stage being tested and it currently passes. |
| PARTIAL | Some stage exists, but at least one downstream stage or syntax path is incomplete/unverified. |
| MISSING | Required implementation is absent in the relevant stage. |
| UNVERIFIED | Source exists, but there is no adequate test evidence yet. |
| BLOCKED | Cannot reach E2E because an earlier required stage is missing. |

> `PASS` is evidence-based. Existence of a symbol alone is not treated as E2E PASS.

## 3. RoboSim API Coverage

| RoboSim capability | Frontend mapping | Compiler registry | Compiler opcode | ESP32 VM dispatch | Robot API / platform | Current E2E evidence | Overall |
|---|---|---|---|---|---|---|---|
| `SetMoveRun` | PASS | PASS via `forward/backward/turn_*` | PASS | PASS | PASS | PASS | PASS |
| `SetMoveStop` | PASS | PASS via `stop` | PASS | PASS | PASS | PASS | PASS |
| `SetMoveRunSecond` | PASS | PASS via rewrite | PASS via generated sequence | PASS | PASS | PASS compile/rewrite | PASS* |
| `SetWaitForTime` | PASS | PASS via `wait` | PASS | PASS | PASS | PASS | PASS |
| `SetMoveSpeed` | PASS | PASS | PASS | PASS | UNVERIFIED | compile/rewrite only | PARTIAL |
| `SetMoveInitialize` | PASS | PASS | NOP stub (does not emit `MoveInitialize`) | N/A — opcode not emitted by current handler | UNVERIFIED | rewrite only | PARTIAL* |
| `SetMoveRunAngle` | PASS | PASS | NOP stub (does not emit `MoveRunAngle`) | N/A — opcode not emitted by current handler | UNVERIFIED | rewrite only | PARTIAL* |
| `GetUltrasound` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `GetTouch` | PASS | PASS | PASS | PASS | UNVERIFIED | compile/rewrite | PARTIAL |
| `GetLightSensor` | PASS | PASS | PASS | PASS | UNVERIFIED | compile/rewrite | PARTIAL |
| `GetTraceV2I2CChxState` | PASS | PASS | PASS (`ReadLine`) | PASS | UNVERIFIED | compile/rewrite | PARTIAL |
| `GetTraceV2I2C` | PASS | PASS | PASS (`GetTraceValue`) | PASS | PASS | UNVERIFIED | PARTIAL |
| `GetTraceV2I2CState` | PASS | PASS | PASS (`GetTraceState`) | PASS | PASS | UNVERIFIED | PARTIAL |
| `GetTraceV2I2CData` | PASS | PASS | PASS (`GetTraceRaw`) | PASS | PASS | UNVERIFIED | PARTIAL |
| `GetLightSensorData` | PASS | PASS | LoadConst stub (does not emit `GetLightSensorData`) | N/A — opcode not emitted by current handler | UNVERIFIED | rewrite only | PARTIAL* |
| `Set3CLed` | PASS | PASS | PASS | PASS | PASS | compile/rewrite only | PARTIAL |
| `SetLightSensorLed` | PASS | PASS | PASS | PASS | PASS | compile/rewrite only | PARTIAL |
| `SetServo` | PASS | PASS | PASS | PASS | PASS | compile/rewrite only | PARTIAL |
| `SetSeeringEngine` | PASS | PASS | NOP stub (does not emit `SetSeeringEngine`) | N/A — opcode not emitted by current handler | UNVERIFIED | rewrite only | PARTIAL* |
| `SetSeeringEngineTime` | PASS | PASS | NOP stub (does not emit `SetSeeringEngineTime`) | N/A — opcode not emitted by current handler | UNVERIFIED | rewrite only | PARTIAL* |
| `SetMotor` | PASS | PASS | NOP stub (does not emit `SetMotor`) | N/A — opcode not emitted by current handler | UNVERIFIED | rewrite only | PARTIAL* |
| `SetMotorServo` | PASS | PASS | NOP stub (does not emit `SetMotorServo`) | N/A — opcode not emitted by current handler | UNVERIFIED | rewrite only | PARTIAL* |
| `SetMotorStraightAngle` | PASS | PASS | PASS | PASS | PASS | compile/rewrite only | PARTIAL |
| `line_basis` | PASS | PASS | PASS | PASS | PASS | UNVERIFIED E2E | PARTIAL |
| `line_follow` | PASS | PASS | PASS | PASS | PASS | UNVERIFIED E2E | PARTIAL |
| `line_stop` | PASS | PASS | PASS | PASS | PASS | UNVERIFIED E2E | PARTIAL |
| `line_millisecond` | PASS | PASS | PASS (`LineMillisecond`) | PASS | PASS | compile/rewrite only | PARTIAL |
| `line_intersection_stop` | PASS | PASS | PASS | PASS | PASS | rewrite/compile only | PARTIAL |
| `line_turn_encounterline` | PASS | PASS | PASS | PASS | PASS | UNVERIFIED E2E | PARTIAL |
| `line_for_bmp` | PASS | PASS | PASS | PASS | PASS | UNVERIFIED E2E | PARTIAL |
| `line_set_initialize` | PASS | PASS | NOP stub (does not emit `LineSetInitialize`) | N/A — opcode not emitted by current handler | UNVERIFIED | rewrite only | PARTIAL* |
| `SetMp3Play` | PASS | PASS | PASS | PASS | PASS | compile/rewrite only | PARTIAL |
| `SetLizard` | PASS | PASS | NOP stub (does not emit `SetLizard`) | N/A — opcode not emitted by current handler | UNVERIFIED | rewrite only | PARTIAL* |
| `UpdateVar` | PASS | PASS | No runtime bytecode (GUI-only stub) | N/A | UNVERIFIED | rewrite only | PARTIAL* |
| `DisplayVariable` | PASS | PASS | No runtime bytecode (GUI-only stub) | N/A | UNVERIFIED | rewrite only | PARTIAL* |

\* `SetMoveRunSecond` is proven through rewrite/compile behavior, but it should receive a dedicated runtime/E2E test before being promoted to hardware PASS.

## 4. Important Architectural Finding

C2 traced the C1 "12 missing VM dispatch" list back through the **actual compiler handlers**.

Only `LineMillisecond` is currently a live compiler → opcode path that reaches the ESP32 VM without a dispatch case.

The other C1-listed opcodes are currently **not emitted by their compiler handlers**:

```text
MoveInitialize        → NOP
MoveRunAngle          → NOP
GetLightSensorData    → LoadConst(0) stub
SetSeeringEngine      → NOP
SetSeeringEngineTime  → NOP
SetMotor              → NOP
SetMotorServo         → NOP
LineSetInitialize     → NOP
SetLizard             → NOP
UpdateVar              → no runtime bytecode (GUI-only)
DisplayVariable       → no runtime bytecode (GUI-only)
```

Therefore adding dead VM `case` statements for these opcodes would create an execution contract that the current compiler does not use and, for several APIs, semantics are explicitly unresolved in the existing platform contract.

C2 therefore implements the one confirmed live gap:

```text
line_millisecond
    ↓
Opcode::LineMillisecond (59)
    ↓
ESP32 VM dispatch
    ↓
RobotAPI::LineMillisecond(speed, millisecond)
    ↓
LineFollower + motor output
```

This correction prevents the VM from accumulating handlers for compiler stubs that currently emit `NOP`.

* `PARTIAL*` means the API is intentionally not treated as a C2 VM-dispatch blocker because its current compiler handler is a stub/non-runtime path. It remains a future API-completion item.

## 5. Language Construct Coverage

| Construct | Current compiler evidence | E2E evidence | Status |
|---|---|---|---|
| assignment | PASS | PASS | PASS |
| variable reference | PASS | PASS | PASS |
| integer / float constants | PASS | PASS for tested cases | PASS |
| arithmetic `+ - * / % **` | PASS | Partial | PARTIAL |
| unary `-` | PASS | UNVERIFIED E2E | PARTIAL |
| `== != < <= > >=` | PASS | PASS compile/VM tests | PASS |
| `and` | PASS | PASS compile test | PASS |
| `or` | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| `if` | PASS | PASS | PASS |
| `if/else` | PASS | PASS | PASS |
| nested `if` | PASS | PASS compile | PARTIAL |
| `while` | PASS | PASS | PASS |
| nested `while` | PASS compile | UNVERIFIED E2E | PARTIAL |
| `break` | PASS compile | UNVERIFIED E2E | PARTIAL |
| `continue` | PASS compile | UNVERIFIED E2E | PARTIAL |
| user functions | PASS | PASS | PASS |
| function return | PASS opcode/runtime support; dedicated RoboSim E2E not found | UNVERIFIED | PARTIAL |
| `_thread.start_new_thread` | PASS rewrite/compile | UNVERIFIED hardware E2E | PARTIAL |
| `pass` | PASS | UNVERIFIED | PASS (compile-level) |

## 6. Existing E2E Coverage

The current end-to-end suite proves these programs through:

```text
RoboSim source
  → frontend rewrite
  → RobotCompiler
  → ISA conversion
  → binary encode
  → runtime loader
  → VirtualMachine
  → MockHardware
```

Currently proven programs:

```text
demo_forward.py
demo_backward.py
demo_turn.py
demo_variable.py
demo_if.py
demo_loop.py
demo_function.py
demo_wait
```

Result: **8/8 PASS**.

This is strong compiler/runtime evidence, but it is **MockHardware E2E**, not physical ESP32 E2E.

## 7. Highest-Priority Completion Backlog

### C2 — VM Dispatch Completion

Implement and test the missing VM opcode dispatch cases listed in Section 4.

Priority: **P0** because compiler output can currently reach an ESP32 VM default/invalid-opcode path for these capabilities.

### C3 — Sensor / Actuator E2E Coverage

Add compile + VM + MockHardware tests for:

- ultrasonic
- touch
- light
- line/trace
- 3-color LED
- light sensor LED
- servo
- motor APIs
- line APIs

Priority: **P0/P1** depending on actual RoboSim curriculum usage.

### C4 — Language Coverage Completion

Close the unverified constructs, especially:

- `or`
- return values
- nested control flow E2E
- break/continue E2E
- function + sensor/actuator combinations

Priority: **P1**.

### C5 — Physical ESP32 Program Matrix

After C2–C4, compile and flash representative programs on the actual platform and record hardware evidence.

Priority: **P1**.

## 8. C1 Conclusion

The project is **not blocked by the compiler core**. The strongest current completion gap is downstream:

```text
RoboSim API
    ↓ PASS / PARTIAL
Frontend rewrite
    ↓ PASS
Compiler registry + handlers
    ↓ PASS
Opcode generation
    ↓ PASS
ESP32 VM dispatch
    ↓ <-- CURRENT MAJOR GAP
Robot API / hardware
    ↓
E2E
```

Therefore the next implementation task should **not** be another diagnostic investigation. It should be **VM Dispatch Completion (C2)**, followed by systematic E2E coverage.
