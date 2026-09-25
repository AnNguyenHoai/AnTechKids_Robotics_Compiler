# VM Firmware Main-Loop Integration

Tracking: #309, parent #302
Baseline: `main@b487ead90dcd6dae9172436627604a5a285e3558` (merged PR #320 / VM-RT F)

## Goal

VM-RT G makes `VM::RunSlice()` the production firmware scheduling boundary. Student programs may run for arbitrarily many VM work units, but firmware control returns after every bounded slice so communication, OTA, sensing, motion service and diagnostics continue to progress.

## Production cycle order

The normal `loop()` order is intentionally:

1. service serial/control-plane input;
2. service network/discovery/OTA;
3. if OTA is active, stop motors and return without student-code execution;
4. refresh platform sensors and diagnostic sensor state;
5. update IMU heading and motion/output service;
6. update the development console;
7. run behavior scheduler **or** one bounded VM slice;
8. record firmware-loop diagnostics and return to Arduino runtime.

`RunSlice()` owns the line-sensor snapshot lifecycle introduced by #308. It begins one lazy snapshot cycle, reuses one coherent L/C/R sample set for all line consumers in that slice, and closes the snapshot on every return path through RAII.

## Initial VM budget

Production starts with:

```text
VM_WORK_UNITS_PER_FIRMWARE_CYCLE = 4
```

One work unit is at most one legacy `Step()` call. Four is deliberately conservative: it amortizes simple VM dispatch while preserving a short deterministic return boundary to platform services. This is a semantic work budget, not a wall-clock guarantee. #310 owns runtime timing/snapshot-age/read-count instrumentation and any evidence-based tuning.

The budget must not be increased to hide a blocking RobotAPI call. Remaining blocking work must be fixed at its owner.

## Stop, abort and OTA responsiveness

Serial and network services execute before a new VM slice. Therefore a stop/abort that changes VM running state is observed before more student work is scheduled on the next firmware cycle. A slice itself is cooperative rather than preemptive and remains bounded by `maxWorkUnits` plus the duration of any single synchronous operation that still exists.

OTA has stronger priority: when an update is active, motors are stopped and the VM/behavior scheduler is skipped for that cycle.

## Terminal behavior

VM completion and VM faults no longer enter a nested `while (1)` inside `loop()`.

- faults stop robot outputs and are reported once;
- normal completion is reported once;
- stability restart behavior remains available when `STABILITY_ITERATIONS` requests another run;
- after the final run, firmware continues its ordinary cycle so serial/network/OTA/diagnostics remain serviceable.

Boot-time fatal conditions are intentionally outside this work package.

## Compatibility

Unchanged:

- bytecode and opcode numbering;
- legacy `Step()` semantics and public API;
- compiler output;
- cooperative pending-operation semantics;
- line-follow control algorithms;
- #308 line-snapshot ownership and threshold behavior.

The production integration changes only who schedules VM work: `loop()` now calls bounded `RunSlice()` instead of directly calling `Step()`.

## Acceptance mapping

- Long-running programs repeatedly return control: enforced by bounded `RunSlice` scheduling and deterministic long-program scheduler model in `run_vm_responsiveness_baseline.py`.
- Platform responsibilities progress: serial/network/sensors/motion execute before VM scheduling every cycle; the host model asserts one service tick per long-program cycle.
- Stop/abort bounded observation: control-plane service precedes each slice; the host model verifies stop prevents work in the observed cycle.
- Sensor lifecycle contract: one `RunSlice` remains one lazy line-snapshot cycle from #308.
- Integration regression: source-order checks plus scheduler model are part of the VM responsiveness gate; ESP32 compilation remains required for impacted VM firmware changes.

## Follow-up

#310 should add runtime measurements for slice duration, loop duration, line snapshot age/read count and service progress. #312 remains the physical qualification boundary.
