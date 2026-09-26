# VM Control-Latency Corrective Audit

Date: 2026-09-25
Tracking: #325 / #312, parent #302
Branch baseline: `main@8df426b14770356121cf4a3f8a7405a5a8559c49`

## Trigger

Physical robot retest reported two observable failures:

1. `line_basis(60)` with a 20 ms student wait was too slow to remain on the line.
2. A direct `SetMoveSpeed(70, 70)` loop followed by `GetTraceV2I2CState(...) -> SetMoveStop()` stopped materially beyond the detected line.

These observations are treated as failure reports, not quantitative qualification evidence. No latency threshold is approved from distance estimates or host simulation.

## Confirmed software findings

- Production scheduling used a four-work-unit slice with no wall-clock bound. A short source-level sensor/branch/actuator reaction can compile to more than four cheap VM instructions, allowing the decision and actuator command to fall in different firmware cycles.
- Qualification firmware streamed a large JSON record over 115200-baud Serial after every active slice. The instrumentation could therefore perturb the control loop being measured.
- `DiagnosticsManager` performed additional line-sensor updates after `SensorManager`, creating redundant physical sampling outside the shared VM snapshot.
- The September 24 line-stability change combined weaker P-only steering, lower mixer authority, three scheduler-dependent loss-confirmation samples, and a 300 ms soft-recovery interval. The combined behavior traded excessive responsiveness for smoothness.
- Physical stopping distance cannot be interpreted as VM latency alone; motor-driver brake/coast behavior and mechanical inertia remain part of the end-to-end result.

## Corrective implementation

- `RunSlice` keeps the legacy work ceiling and gains an optional wall-clock ceiling checked between `Step()` calls.
- Production uses provisional `max_work_units=16`, `max_duration_us=2000` so common reactive chains can finish in one slice while platform service still has a wall-clock return boundary.
- Qualification telemetry is captured in a fixed RAM ring and emitted only after VM motion stops; one stop-latency observation is attached only to the final buffered record.
- Diagnostics consume cached line state instead of re-sampling the hardware.
- Line-loss confirmation is elapsed-time based (`10 ms`) instead of fixed sample count.
- Default line controller remains P-only to avoid derivative jitter, but restores steering authority (`Kp=1.2`, mixer scale `15`).
- Soft recovery is shortened from 300 ms to 120 ms while retaining bounded motor commands.
- Physical qualification metadata and campaign aggregation now require the exact dual scheduler configuration, preventing mixed-budget evidence.

## Compatibility classification

No opcode number, bytecode encoding, compiler generation, firmware generation, or legacy `Step()` semantics are changed. `TimeBudgetExhausted` is appended to the scheduler diagnostic stop-reason enum, and `maxDurationUs` is an optional trailing field whose zero value preserves work-unit-only callers.

## Evidence status

The runtime configuration is provisional and explicitly `UNAPPROVED_PENDING_PHYSICAL_EVIDENCE`. All production thresholds remain `null`. #325/#312 remain blocked until the corrective firmware is CI-verified and the six physical scenarios plus external sensor-to-decision-to-motor evidence are captured and reviewed.
