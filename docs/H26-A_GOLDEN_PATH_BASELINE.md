# H26-A — Golden Path Baseline

## Purpose

This document freezes the currently working robot development path as the **Golden Path** for non-breaking architecture work.

H26-A does **not** replace or refactor the production compiler, VM, RobotAPI, firmware, or Arduino workflow. It documents and protects the existing path before later migration tasks begin.

## Protected Golden Path

```text
RoboSim source (.py)
        |
        v
Frontend rewrite (`tools/rewrite.py`)
        |
        v
Standard Robot API `.rewrite.py`
        |
        v
Compiler (`tools/compile.py` / `robot-compiler`)
        |
        v
Generated C++ program header (`program.h`)
        |
        v
Copy to firmware `generated_program.h`
        |
        v
Arduino / PlatformIO firmware build
        |
        v
ESP32 upload
        |
        v
Robot VM + RobotAPI
        |
        v
Physical robot behavior
```

The repository's current build tooling confirms that `build.py` composes the rewrite and compile stages, while `flash.py` copies the generated header into the firmware application and invokes PlatformIO upload. See `tools/build.py`, `tools/compile.py`, and `tools/flash.py`.

## Artifact Boundaries

| Stage | Input | Output | Owner |
|---|---|---|---|
| Frontend | RoboSim `.py` | `.rewrite.py` | `tools/rewrite.py` |
| Compiler | `.rewrite.py` | `program.h`, `compile_report.json` | `tools/compile.py` |
| Build orchestration | `.py` | complete compiler artifacts | `tools/build.py` |
| Firmware deployment | `program.h` | firmware upload | `tools/flash.py` + `robot-platform` |
| Runtime | firmware + generated program | robot behavior | ESP32 VM / RobotAPI |

`BUILD_PIPELINE.md` and `TOOLCHAIN.md` describe the same stage boundary. This document treats those files as operational documentation of the current path, not as a reason to change the implementation during H26-A.

## Golden Inputs

The current `robot-platform/golden/` programs are the characterization corpus for compiler-side regression. `tools/golden_build.py` already runs the compiler pipeline over that corpus and writes `build/golden_summary.json`.

At minimum, future migration work must retain coverage for:

- basic motion (`forward`, `backward`, `stop`)
- timing (`wait`)
- sensor/control examples present in the existing golden corpus
- representative multi-instruction programs

## Invariants

The following are non-negotiable during the H26 architecture migration:

1. Existing source programs that currently reach the robot successfully must retain their observable behavior.
2. Existing generated `program.h` format consumed by firmware must remain valid until an explicit migration task proves an equivalent replacement.
3. H26-A itself must not change VM dispatch, RobotAPI semantics, opcode values, firmware initialization, or physical behavior.
4. Any future compiler/ISA/ABI migration must be introduced behind characterization tests and must prove equivalence before the old path is retired.
5. Hardware-only validation remains distinct from software-only validation. A compiler PASS is not a claim that physical robot behavior was verified.

## Validation Levels

### Level 1 — Compiler / Artifact

Confirm the rewrite + compile pipeline completes and produces the expected program artifact and report for the golden corpus.

### Level 2 — Firmware Build

Confirm the generated program can be consumed by the existing ESP32 firmware build. This requires the project's Arduino/PlatformIO toolchain.

### Level 3 — Upload

Confirm the firmware image can be uploaded to an ESP32 using the existing deployment workflow.

### Level 4 — Physical E2E

Confirm boot, VM execution, RobotAPI interaction, and expected physical robot behavior on connected hardware.

Levels 1–3 may be automated where the toolchain is available. Level 4 remains a hardware acceptance gate.

## Architecture Map

```text
                 +-----------------------+
                 |    RoboSim Program    |
                 +-----------+-----------+
                             |
                             v
                 +-----------------------+
                 | Frontend / Rewrite     |
                 | tools/rewrite.py       |
                 +-----------+-----------+
                             |
                       .rewrite.py
                             |
                             v
                 +-----------------------+
                 | Compiler               |
                 | tools/compile.py       |
                 | robot-compiler/        |
                 +-----------+-----------+
                             |
                    program.h + report
                             |
              +--------------+--------------+
              |                             |
              v                             v
 +--------------------------+    +-----------------------+
 | build/ artifact          |    | Firmware application  |
 | program.h                |--->| generated_program.h  |
 +--------------------------+    +-----------+-----------+
                                            |
                                            v
                                  +-----------------------+
                                  | Arduino / PlatformIO  |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  | ESP32 VM / RobotAPI   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  | Physical Robot        |
                                  +-----------------------+
```

## Known Future Migration Areas

These are intentionally **observations only** for later H26 tasks:

- multiple compiler/ISA representations exist in the repository;
- binary `.rbot` work exists but is not the protected deployment path for H26-A;
- some test runners cover different subsets of the repository;
- capability and API contracts need later reconciliation;
- firmware build and physical validation need stronger automated gates.

No migration is performed here. The purpose of H26-A is to establish the baseline from which those changes can be made safely.
