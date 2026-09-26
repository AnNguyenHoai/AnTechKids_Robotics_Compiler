# VM Firmware Main-Loop Integration

Tracking: #309, parent #302; corrective latency work validated under #325 physical qualification.
Historical baseline: `main@b487ead90dcd6dae9172436627604a5a285e3558` (merged PR #320 / VM-RT F)

## Goal

VM-RT G makes `VM::RunSlice()` the production firmware scheduling boundary. Student programs may run for arbitrarily many VM work units, but firmware control returns after every bounded slice so communication, OTA, sensing, motion service and diagnostics continue to progress.

The September 25, 2026 real-robot retest exposed a second requirement that the original work-count-only scheduler did not guarantee: a short reactive Python chain such as `GetTraceState -> if -> Stop` must not be split merely because its compiled representation needs more than four cheap VM instructions.

## Production cycle order

The normal `loop()` order is intentionally:

1. service serial/control-plane input;
2. service network/discovery/OTA;
3. if OTA is active, stop motors and return without student-code execution;
4. begin one firmware-owned line-sensor snapshot cycle and refresh platform sensor caches;
5. update IMU heading and motion/output service;
6. update the development console;
7. run behavior scheduler **or** one bounded VM slice against that same line snapshot;
8. update diagnostics from the same cached line state without re-sampling hardware;
9. end the shared line-sensor snapshot cycle;
10. record firmware-loop diagnostics and return to Arduino runtime.

In production, the firmware loop owns the line-sensor snapshot lifecycle introduced by #308. The first line-sensor refresh samples one coherent L/C/R set, then VM getters, line-follow logic and diagnostics reuse that same set until the firmware cycle closes. `RunSlice()` has an ownership-aware fallback guard: when called standalone outside an active firmware snapshot cycle, it still begins and ends its own lazy snapshot scope for compatibility and tests. When an outer firmware cycle is active, it must never restart or resample that snapshot.

## Scheduler budget evolution

The original VM-RT G integration used:

```text
VM_WORK_UNITS_PER_FIRMWARE_CYCLE = 4
```

That protected platform fairness, but physical testing showed that opcode count is not a sufficient proxy for control latency. A source-level reaction can compile to several cheap instructions: load arguments, read sensor, branch, issue actuator command, and jump back to the loop. With a four-work-unit boundary, the sensor decision and actuator action could land in different firmware cycles even when the entire chain would take far less than a millisecond.

The corrective runtime configuration is now:

```text
VM_WORK_UNITS_PER_FIRMWARE_CYCLE = 16
VM_MAX_SLICE_DURATION_US = 2000
```

The scheduler therefore has two independent guards:

- `maxWorkUnits` is a hard semantic ceiling;
- `maxDurationUs` is an optional wall-clock ceiling checked between legacy `Step()` calls.

Existing callers using `VMRunSliceBudget{4}` remain compatible: the missing time field defaults to zero, which disables the wall-clock guard and preserves work-count-only semantics.

The 16/2000 configuration is a **provisional corrective configuration**, not an approved qualification threshold. It exists because the real robot demonstrated that the four-opcode configuration was functionally inadequate for reactive control. Final tuning and approval still belong to physical evidence under #325/#312 and remain explicitly unapproved in `VM_RESPONSIVENESS_THRESHOLDS.json`.

A single synchronous `Step()` can still overrun the time ceiling because the scheduler is cooperative rather than preemptive. A blocking RobotAPI owner must still be converted or bounded at that owner; increasing either budget is not an acceptable substitute.

## Qualification telemetry must not perturb control

The qualification build previously called `Serial.printf()` with a large JSON record after every VM slice. At 115200 baud that transmission can be orders of magnitude slower than the VM work being measured, so the measurement path could dominate the line-control cadence.

`RecordSlice()` now stores qualification records in a fixed RAM ring buffer. The hot VM path never prints JSON. After VM motion has stopped, `PrintBufferedJson()` emits the stored JSONL evidence. This preserves the existing evidence schema while preventing UART transmission from becoming part of the active control loop.

## Line-sensor sampling ownership

Physical line sampling has one owner per production firmware cycle:

```text
BeginCycle
  -> SensorManager first line update samples L/C/R once
  -> VM / line follower reuse the same snapshot
  -> Diagnostics reads cached state only
EndCycle
```

`DiagnosticsManager` no longer calls `lineSensor->update()` itself. `RunSlice()` also does not begin a new cycle when the firmware already owns one. This removes the prior duplicate pattern where platform refresh sampled L/C/R and VM snapshot setup could sample a second L/C/R set before the same logical decision completed.

Standalone `RunSlice()` callers retain a self-owned snapshot lifecycle, so this correction does not require callers outside the production firmware loop to create a snapshot explicitly.

## Stop, abort and OTA responsiveness

Serial and network services execute before a new VM slice. Therefore a stop/abort that changes VM running state is observed before more student work is scheduled on the next firmware cycle.

Within a slice, the larger work ceiling lets a normal sensor/branch/actuator chain finish without an artificial four-opcode split, while the wall-clock ceiling still returns control to platform services promptly.

OTA has stronger priority: when an update is active, motors are stopped and the VM/behavior scheduler is skipped for that cycle.

## Terminal behavior

VM completion and VM faults do not enter a nested `while (1)` inside `loop()`.

- robot motion is stopped before post-run VM telemetry is printed;
- faults are reported once;
- normal completion is reported once;
- stability restart behavior remains available when `STABILITY_ITERATIONS` requests another run;
- after the final run, firmware continues its ordinary cycle so serial/network/OTA/diagnostics remain serviceable.

Boot-time fatal conditions are intentionally outside this work package.

## Compatibility

Unchanged:

- bytecode/opcode numbering;
- legacy `Step()` semantics and public API;
- compiler generation and firmware compatibility generation;
- cooperative pending-operation semantics;
- #308 same-cycle line-snapshot semantics.

Compatible extensions/corrections:

- `VMRunSliceBudget` gains optional `maxDurationUs` with zero meaning disabled;
- `VMRunSliceStopReason::TimeBudgetExhausted` is appended after existing reason values;
- production scheduler opts into dual work/time bounds;
- production snapshot ownership expands from slice-local to firmware-cycle scope so platform refresh, VM and diagnostics share one physical sample;
- standalone `RunSlice()` retains its own fallback snapshot scope;
- qualification telemetry moves from hot-path UART streaming to post-run RAM-buffer dump;
- line-follow loss confirmation is based on elapsed time rather than scheduler-dependent sample count, with responsive P-only steering retained to avoid derivative jitter.

## Acceptance mapping

- Long-running programs repeatedly return control: enforced by dual-bounded `RunSlice` scheduling and deterministic scheduler model in `run_vm_responsiveness_baseline.py`.
- Reactive control chain: host regression models a representative nine-work-unit sensor/branch/stop chain and requires it to fit one production slice when work is cheap.
- Platform responsibilities progress: serial/network/sensors/motion execute before VM scheduling every cycle.
- Stop/abort bounded observation: control-plane service precedes each slice; physical stop distance remains a qualification measurement rather than a host-test claim.
- Sensor lifecycle contract: one production firmware cycle has one shared L/C/R snapshot across platform refresh, VM/control consumers and diagnostics; standalone `RunSlice()` provides a compatible self-owned fallback scope.
- Observer-safe instrumentation: hot VM path records RAM telemetry only; JSONL is emitted after motion has stopped.
- Integration regression: source-order checks, dual-budget model, single-snapshot ownership, line temporal-response checks and ESP32 compilation remain required before physical retest.

## Physical qualification boundary

The corrective configuration does **not** close #325/#312. Real robot evidence must still measure sensor-to-decision-to-motor latency, stop/abort latency, slice/work-unit timing, snapshot age, outliers and mechanical stopping behavior. Only that evidence may populate and approve the production thresholds.
