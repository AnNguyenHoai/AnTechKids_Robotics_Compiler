# V1-S8-C — Regression and Physical Acceptance

**Base:** main after S8-A PR #433 and S8-B PR #434, commit `9aa1f32d8d5a6e70bd59a7e1b007bbe9bbc6dc82`.

## Acceptance scope and evidence levels

**Automated CI** validates compiler, 512/128 resource gates, target-aware 7-to-5 channel projection, ISA branch behavior under a bounded Python reference runner, and the existing full repository regression suite.

**Physical acceptance remains PENDING** until a human operates the TT-motor robot with calibrated Line5 and records real logs. A passing CI never qualifies real GPIO timing, resets, motor torque or power integrity.

**Important source behavior:** The original student's `DiChuyen()` ends with `pass` if no supported sensor is active, preserving previous motor command. The source is *not* a fail-safe stop or emergency-stop program. For first physical tests keep wheels lifted and use a separate power cutoff.

## Reproducible build and safety gate

1. Check out the tested PR head. Verify RoboStudio, compiler and firmware are built from the **same revision**; do not use a 512/128 compiler with older 128/32 firmware.
2. Run `python run_all_tests.py`, including `tests/v1_s8c/run_v1_s8c.py`.
3. Rewrite/compile the provided source in `tests/v1_s8a/fixtures/user_line7_overflow.py` using target `esp32`, not `robosim`. The ESP32 target maps seven logical positions to five physical sensors and must pass `validate_program`.
4. Flash the resulting **full firmware** containing 512/128 VM arrays using the normal supported deployment path. Check flash/OTA with a signed-off firmware build, not just a source-code assertion.
5. Capture build size and runtime free heap before and after, serial boot/reset events and observed program count. If any resource validation or build step fails, physical test is blocked.

## Existing physical Line5 layout

| Logical RoboSim position | ESP32 physical channel | Eye |
|---|---|---|
| 1 and 2 | 3 | Far left |
| 3 | 0 | Left |
| 4 | 1 | Center |
| 5 | 2 | Right |
| 6 and 7 | 4 | Far right |

This is a **lossy projection**, not seven independent physical sensors. Polarity and sensor power must be checked against the actual calibrated V1 Line5 board.

## Physical test sequence

**Safety setup:** isolate drive wheels first; secure chassis, keep an independent motor power cutoff accessible; check GND, power rail under motor load and battery charge. No child performs the first-run tests.

For each case, run at least **3 trials**, record test evidence with timestamp, battery voltage, firmware commit, board ID, measured response, serial logs and any reset/brownout.

| Test ID | Acceptance observation |
|---|---|
| boot_idle | Power cycle with motors disabled; no boot loop or unexpected reset |
| compile_line7 | Source compiles for ESP32, valid generated header and resource counts, flash boots |
| initial_motion | First command is `(50,50)`, then delay 500ms before reading sensors |
| line_center | Only center active → `(70,70)` |
| line_left | Only left active → `(40,70)` |
| line_right | Only right active → `(70,40)` |
| line_corner_left | Center + left active → `(-70,70)` |
| line_corner_right | Center + right active → `(70,-70)` |
| line_loss | All inactive: document *continued last motor command*; do not falsely mark STOP |
| line5_baseline | Verify original Line5 straight, curved and right-angle tracking not regressed |
| touch_gpio36 | GPIO36 single-touch input remains stable, pressed during reset does not boot-loop |
| servo_gpio19 | Servo selected/Buzzer disabled; confirm no PWM conflict or unexpected resets |
| ultrasonic | Existing HC-SR04 echo/trigger reads behave as before |
| ota_full_firmware | Full firmware update with expanded VM boots, recovery path still available |

Before any on-floor motion verify direction and polarity. Run corner tests lifted first, then slowly on a protected track, and document observed deviation rather than claiming the student algorithm is a tuned line follower.

## Measurement and gate criteria

- **PASS:** three recorded and evidenced trials per required test, no resets/brownouts, no compiler/VM safety errors, correct expected motion decisions; leave no open P0/P1 regression. For line loss, the known `pass` behavior is documented and supervisor retains power cutoff.
- **FAIL:** any wrong command, unexpected reset, unhandled VM error, OTA recovery failure, or sensor mapping disagreement.
- **BLOCKED:** missing board, evidence, valid battery/voltage readings or tested firmware identity.
- Collect initial/free heap and sketch/OTA usage. Compare to the approved V1 baseline; no invented heap/latency limit is specified here.
- Physical latency measurement: record time from line transition to effective motor response. Compare with previously signed-off Line5 baseline for the same speed, track, motor and battery. If a baseline does not exist, record measurements and do not assert performance non-regression.

## Evidence and result entry

Copy `tests/v1_s8c/physical_evidence_TEMPLATE.csv` into a separate evidence file (never overwrite this template). Fill one row per trial with:
`test_id,trial,decision,boot_count_before,boot_count_after,free_heap_before,free_heap_after,latency_ms,evidence_link,notes`.

Use `python tests/v1_s8c/validate_physical_evidence.py <evidence.csv>` to verify the **completeness and consistency** of recorded evidence. This validator cannot authenticate measurements or replace physical inspection. Keep PR Draft unless CI green and physical status is explicitly reported.

## Do not silently change scope

S8-C does not change motor/Line5 PWM tuning, the 7-to-5 projection, ESP32 GPIO pinouts, motion algorithms, error IDs, or VM 512/128 limits. If real trials show a defect, open a distinct scoped issue/PR with logs and reproduce before remediation.
