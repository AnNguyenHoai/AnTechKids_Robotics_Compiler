# V1-S5 — RoboSim and physical acceptance (V1 TT open-loop)

**Base:** main after V1-S4B (#427). **Scope:** V1 TT motors only; no changes to main_V2.  
**Status:** User-reported supervised real-robot functional T1–T8: **8/8 PASS** using T7-R1 as replacement for original T7. Evidence granularity is user-reported outcomes; per-trial timestamps, serial logs and videos were not provided. Full hardware/system safety acceptance remains OPEN.

## Aim

Confirm that the same RoboSim-facing API can be compiled, uploaded and executed by the V1 ESP32 robot; students must decide line steering themselves using sensor reads, conditions and independent motor speeds. The autonomous `rcu.line_basis()` remains a separate reference baseline.

## Preconditions

1. Start with the robot raised off the ground. Secure a clear test area, maintain easy power-disconnect access and an observer who can stop the robot.
2. Confirm battery/driver wiring, wheel rotation direction, line-sensor polarity, five-channel ordering and programmed hardware profile.
3. Use **one program at a time** with the V1 RoboStudio compiler/flash workflow. Preserve serial logs and record the exact commit SHA, board, battery condition, map, observations and test video where available.
4. Never treat GitHub CI or successful flashing alone as evidence of physical PASS. Do not run an unattended `while True` program.

## Programs

| ID | Source | Intent |
| --- | --- | --- |
| M1 | `examples/physical/v1_s5_01_motor_commands.py` | `SetMoveSpeed` → `Wait(2s)` → `Stop`, asymmetric steering and pivot |
| L3 | `examples/physical/v1_s5_02_student_line3.py` | Read three channels, use If/Else to choose wheel speeds |
| L5 | `examples/physical/v1_s5_03_student_line5.py` | Read five channels, handle far sensors and pivot independently of `line_basis` |
| T7-R1 | `examples/physical/v1_s5_04_student_to_line5.py` | Student 1s → repeated Line5 20ms refresh for ~3s → Stop; replaces the insufficient 100ms T7 probe |

These are **starting algorithms**, not calibrated claims of physical line-following success. For L3/L5, `while True` is deliberately continuous; operator must be ready to disable motors and interrupt/reset the program.

## Recording evidence

| ID | Required check | Pass condition | Status |
| --- | --- | --- | --- |
| S5-01 | M1 straight segment | Both wheels rotate in expected direction; 2s hold does not stop at 300ms | PENDING |
| S5-02 | M1 steering segment | Wheel-speed asymmetry creates intended turn; no legacy minSpeed compression | PENDING |
| S5-03 | M1 pivot segment | `(0,70)` leaves one wheel stopped and moves the other | PENDING |
| S5-04 | M1 `SetMoveStop` | Output PWM returns to zero | PENDING |
| S5-05 | L3 on straight / gentle curve | Robot tracks line with observable sensor-driven corrections, without autonomous API | PENDING |
| S5-06 | L5 on round curve / 90-degree turn | Student algorithm reacts to far sensor and can negotiate target course; count departures | PENDING |
| S5-07 | Stop after program completion, with no final Stop | Motors stop under VM lifecycle safety logic | PENDING |
| S5-08 | VM fault/invalid program | Motors stop; serial/network/OTA remain recoverable | PENDING |
| S5-09 | Student → Line5 ownership | T7-R1: after Student 1s, Line5 actively corrects for ~3s, followed by Stop | PASS (user reported) — reverse direction and Heading still PENDING |
| S5-10 | `line_basis(80)` regression | Existing baseline still performs comparably under matched hardware/course conditions | PENDING |

**Quality measurements:** use one fixed line course, fixed start pose, similar battery state and at least three repetitions per course. Record successful finishes, line departures, unexpected stops and approximate lap time. Do not invent thresholds: agree on numerical pass targets after baseline runs.

## Software gate

```bash
python tests/v1_s5/run_v1_s5.py
python run_all_tests.py
```

This gate verifies syntax/API patterns, sample channel ordering, Line5 preservation, absence of the Student 300ms deadline, and VM-lifecycle stop source contracts. It **does not** prove serial timing, motor torque, compilation of every sample, physical behavior or firmware fail-safe behavior under a hardware freeze.

## Acceptance rule

- CI PASS + physical evidence for every applicable case + review of safety observations are required for **S5 FINAL PASS**.
- A failing physical case stays FAIL/PENDING until reproduced, investigated and retested. Do not modify motor calibration just to force a test PASS without recording the change.
- Hardware driver enable/stby fail-safe and MCU crash reset safety remain an additional hardware-specific verification; software Stop alone is insufficient.


## V1-S5 functional closeout — operator report (2026-10-12)

**Release candidate code reference (pre-closeout):** `main@9b3a2114bfdc988b704625d9ee6488eec0d46bb8` (merged PR #428). This is the reference code identified when closeout began, not a separately verified flash SHA. Do not claim that exact SHA was running on the physical robot without build/flash evidence.

| Test | Operator result | Description |
| --- | --- | --- |
| T1 | PASS | Straight, steering and pivot |
| T2 | PASS | 3-second Wait does not stop at 300ms |
| T3 | PASS | Reverse and motor restart |
| T4 | PASS | Student 3-channel line following |
| T5 | PASS | Student 5-channel line following |
| T6 | PASS | VM completion stops motors |
| T7 original | FAIL | 100ms Line5 followed by Stop was insufficient to establish a meaningful transfer |
| T7-R1 | PASS | Student 1s → 150 repetitions of line_basis(70), Wait(0.02) → Stop |
| T8 | PASS | Autonomous Line5 baseline |

**Status:** 8/8 functional acceptance scenarios reported PASS with corrected T7-R1. Original T7 is **superseded**, not retroactively claimed PASS. No cause in motor firmware was established for the original failed trial.

**Evidence limitations:** Operator reported status values but no detailed per-trial timing, video, logs, line-loss measurements, board identifier, battery state, or firmware flash SHA. The 10-row physical acceptance matrix is **not** identical to the 8 operator trials: for example VM fault/recovery, Line5→Student and Heading transitions have not been shown to pass. Keep these open.

**Release use:** Suitable as a **functional V1 TT open-loop release-candidate baseline for supervised validation**, not a claim of comprehensive hardware fail-safe or unattended classroom readiness. Freeze controller parameters; introduce no further motor tuning without reproducible measurements.

### Open follow-ups

1. VM runtime fault, cancellation, corrupted/invalid program and OTA recovery on a safe test rig.
2. Line5→Student and Heading ownership transitions, including switching while motors are active.
3. MCU hang/reset and TB6612FNG standby/output fail-safe verification (hardware-level).
4. Quantitative fixed-course benchmark (3+ runs, stable battery, line departures, elapsed time).
5. Student usability trial: have learners author and debug their own 3/5-channel control without simply copying a complete implementation.


## Result template

```text
Commit:
Firmware/board:
Robot / TT motor / battery:
Course and surface:
Operator / date:
Test ID:
Trial 1:
Trial 2:
Trial 3:
Observed behavior and serial evidence:
PASS / FAIL / BLOCKED / NOT RUN:
Issue / follow-up:
```
