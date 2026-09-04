# H26-A — Golden Path Evidence

## Baseline commit

`63cef2e145306b84332dc70728ebfcfd06dab466`

## Current protected artifact

`robot-platform/main/src/Application/generated_program.h`

The file is an auto-generated C++ header consumed by the firmware application. H26-A deliberately leaves its content unchanged.

## Current tool boundaries

- `tools/rewrite.py`: RoboSim source → `.rewrite.py`
- `tools/compile.py`: `.rewrite.py` → `program.h` + `compile_report.json`
- `tools/build.py`: orchestration of rewrite then compile
- `tools/flash.py`: copy `program.h` to firmware `generated_program.h`, then invoke PlatformIO upload
- `tools/golden_build.py`: compiler-side golden corpus validation

These boundaries are observable in the baseline source and are therefore treated as characterization facts for future refactors.

## H26-A scope decision

This task adds only:

1. an explicit architecture/baseline document;
2. repository-level characterization guards;
3. a standalone H26-A runner so the guards can execute without requiring a third-party test framework.

It does **not** modify the protected compiler, generated program format, VM dispatch, RobotAPI, firmware logic, or deployment behavior.

## Hardware validation

Physical robot execution is not claimed by this commit. A hardware-connected E2E run remains a separate acceptance activity and must be recorded when performed.
