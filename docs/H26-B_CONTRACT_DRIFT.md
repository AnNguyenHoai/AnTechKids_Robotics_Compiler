# H26-B — Contract Drift Detection

## Purpose

H26-B adds a read-only guard around the currently working production Golden
Path. It does **not** reconcile or replace the existing architecture.

The protected flow is:

```text
RoboSim source
    ↓
tools/rewrite.py
    ↓
.rewrite.py
    ↓
tools/compile.py
    ↓
program.h
    ↓
tools/flash.py
    ↓
robot-platform/.../generated_program.h
    ↓
Arduino / PlatformIO
    ↓
ESP32 VM / RobotAPI
    ↓
physical robot
```

This matches the H26-A baseline. Future architecture work must preserve this
flow until a later migration task proves an equivalent replacement.

## What the guard checks

### 1. Tool boundary

`tools/build.py` must still invoke rewrite before compile.

`tools/compile.py` must still use the production `RobotCompiler` and
`HeaderEmitter` and emit the existing program artifact/report.

`tools/flash.py` must still consume `program.h`, copy it to the firmware
`generated_program.h`, and invoke the existing PlatformIO upload target.

### 2. Generated compiler contract

The generated `function_registry.py` is checked against generated
`opcode.py`:

- every registry opcode name must exist in the generated opcode enum;
- numeric opcode values must be unique.

This detects a common class of silent generator drift without changing either
side of the contract.

### 3. Firmware program boundary

The checked-in generated firmware artifact must still contain the existing
`generatedProgram[]` and `generatedProgramSize` declarations.

The artifact content is protected by the H26-B baseline file because it is an
input to the currently working firmware deployment flow.

### 4. Golden corpus

`robot-platform/golden/` must remain present and non-empty.

### 5. Protected baseline

`docs/H26-B_CONTRACT_BASELINE.json` stores Git blob SHAs for the production
boundary files captured at commit `9d14e8941b2ea8bacc429c7118feb2a37001dc97`.

A future edit to one of these files is therefore an explicit drift event. A
migration task should update the baseline only after the new behavior has been
characterized and the existing E2E gate has passed.

## Known architectural migrations

The baseline deliberately does **not** fix the following already-known
architecture issues:

- legacy `packages/robot-common` opcode definitions versus the generated
  production opcode contract;
- alternative/new compiler and binary pipeline work that is not yet the
  physical deployment path;
- binary ABI reconciliation;
- completion of the hardware capability model;
- firmware-build integration into the IDE flow.

These belong to later H26 tasks. H26-B turns the current production path into a
measurable guardrail so those migrations can be made incrementally.

## Running

From repository root:

```bash
python tools/check_contract_drift.py
```

or, without requiring pytest:

```bash
python tests/h26_b/run_h26_b.py
```

A successful run exits `0`. Any unexpected contract drift exits non-zero.

The checker is read-only apart from an optional JSON report requested with
`--json <path>`.

## Non-breaking rule

H26-B must never be used as a reason to change compiler output, firmware
execution, VM dispatch, RobotAPI semantics, Arduino/PlatformIO settings, or
physical robot behavior. It is a detection and characterization task only.
