# VM-RT #385 — Fixed-rate line-sensor sampling evaluation

## Status

Evaluation implementation. The independent sampler is enabled only by the `esp32dev_vm_qualification` profile. Production `esp32dev` keeps the firmware-cycle-owned snapshot until physical evidence justifies adoption.

## Candidate design

Qualification profile:

- producer cadence: 1 kHz (`1000 us` target period)
- stale threshold: `3000 us` (3 target periods)
- implementation: bounded FreeRTOS task
- producer work: read left/center/right digital line inputs, form canonical `L=0b100 / C=0b010 / R=0b001` mask, timestamp, publish one coherent record
- consumer work: copy the latest coherent record at `LineSensorSnapshot::EnsureSample()`
- no controller, PWM, Serial logging, network work, allocation, or blocking I/O in the sampling task

The VM and RobotAPI continue consuming the existing `LineSensorSnapshot` boundary. No opcode, bytecode, compiler, or scheduler specialization is introduced.

## Stale policy

A published sample is fresh when:

`now_us - sample_timestamp_us <= 3000 us`

If the latest sample is stale or no sample has been published yet, the consumer returns an invalid snapshot with mask `0`. The line sensor objects receive the same zero fallback used by the existing unavailable-input path. Stale observations are counted for qualification evidence.

This is intentionally fail-safe and explicit; the controller never silently treats an arbitrarily old sample as current.

## Compatibility comparison

### Existing production model

One coherent L/C/R physical sample is lazily owned by each firmware control cycle. Advantages: simple ownership, no concurrent producer, established compatibility. Limitation: a long indivisible firmware/background call can stretch the next sample interval.

### Fixed-rate qualification model

A periodic task produces the sample independently of normal firmware-loop cadence. Advantages: sampling can preempt ordinary loop jitter and exposes producer interval/jitter/staleness. Costs: one periodic RTOS task, synchronized publication, and additional CPU scheduling load.

The task does **not** solve an interrupt-disabled region or a higher-priority CPU stall. Physical measurements are therefore required before claiming a deterministic 1 kHz hardware cadence.

## Evidence

Existing qualification telemetry already emits `last_line_sample_period_us` and `max_line_sample_period_us`; with a 1000-us target these values expose period and allow jitter to be calculated. `LineSensorSnapshot` additionally tracks latest interval, maximum producer jitter and stale count for runtime diagnostics/tests.

Required physical comparison before production adoption:

1. current firmware-cycle snapshot: p50/p95/p99/max sample period under representative VM + serial/network workload;
2. fixed-rate qualification sampler: same distribution plus stale count;
3. CPU/control impact: firmware-cycle max, VM slice max, sensor-to-decision-to-PWM timing;
4. line-follow/recovery/intersection behavior on the same robot, battery state and course;
5. verify no starvation or watchdog instability during network/OTA-adjacent background activity.

## Adoption rule

Do not enable `VM_RT_FIXED_RATE_LINE_SAMPLING` in the production environment solely because host CI passes. Adopt it only if physical evidence shows materially better cadence/jitter without control regression or unacceptable CPU cost. If measurements show no meaningful benefit, retain the current firmware-owned snapshot and close #385 with the evidence.
