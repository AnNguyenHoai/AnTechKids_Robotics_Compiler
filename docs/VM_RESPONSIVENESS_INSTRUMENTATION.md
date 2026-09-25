# VM Responsiveness Instrumentation

Tracking: #310 / corrective latency work under #325, parent #302
Historical baseline: `main@1726a41b5c8b70ef7bb4c5c66044c4272adce7f4` (merged #309 / PR #321)

## Purpose

VM-RT H turns responsiveness into measurable evidence without changing bytecode/opcode semantics or cooperative pending behavior. The September 25, 2026 physical retest also established an instrumentation requirement: collecting evidence must not materially slow the control loop being measured.

## Per-slice evidence

`VMRunSliceResult` carries diagnostic observations in addition to the stop reason/work-unit/PC contract:

- total slice duration in microseconds;
- work units executed;
- termination reason;
- slowest indivisible work-unit duration and the PC that owned it;
- pending operation, lifecycle, owner PC, generation, and pending opcode;
- line snapshot validity, sequence, age, physical read count, consumer count, and invalid count.

A work unit is one legacy `Step()` call. Therefore `maxWorkUnitDurationUs` identifies the scheduler-visible indivisible unit that consumed the most wall-clock time in the slice. It does not claim to isolate time inside a nested RobotAPI implementation; it identifies the PC/work unit to investigate.

The scheduler now also supports an optional `maxDurationUs` wall-clock ceiling in addition to `maxWorkUnits`. This is checked between `Step()` calls and therefore remains cooperative rather than preemptive.

## Snapshot timing

Snapshot evidence is captured by `RunSlice()` before the RAII line-snapshot cycle closes. A valid line snapshot therefore has an age measured from the shared sample timestamp to slice termination. No getter performs an extra refresh for instrumentation.

`DiagnosticsManager` is an observer only: it reads the cached TCRT5000 state and does not call `update()` again. This avoids a second diagnostic-owned physical sample at a different instant from the control decision.

## Stop/abort latency

The firmware measures an upper-bound stop/abort observation window around its control-plane service phase:

```text
firmware cycle enters serial/network service
  -> command/service may stop VM
  -> firmware observes VM non-running
  -> RecordStopLatency(elapsed_us)
```

This measures the bounded scheduling/control-plane observation window rather than pretending to know transport latency before the firmware received the command. Physical stopping distance must be measured separately because it also contains motor-driver braking/coast behavior and robot inertia.

## Aggregation

`VMRuntimeTelemetry` records:

- slice count;
- latest slice evidence;
- maximum slice duration;
- maximum work-unit duration and PC;
- latest and maximum stop/abort observation latency;
- a fixed RAM ring of the latest qualification slice records when diagnostics are enabled.

The VM never reads this state, so telemetry cannot influence scheduling decisions.

## Observer-safe JSONL capture

When built with:

```text
-DVM_RESPONSIVENESS_DIAGNOSTICS=1
```

`RecordSlice()` stores evidence in RAM. It does **not** call `Serial.printf()` from the active VM hot path.

The previous implementation printed one large JSON record after every slice. At 115200 baud, serial transmission can take far longer than a normal VM slice and therefore distort the exact line-follow/decision-loop latency being measured. The corrective implementation removes that observer effect.

After VM motion has stopped, `PrintBufferedJson()` emits the buffered slice records using the same stable JSONL schema:

```json
{"type":"vm_rt","slice":1,"duration_us":123,"work_units":9,"reason":0}
```

The records also contain PC, pending-operation, line-snapshot, slowest-work-unit, and stop-latency fields. The qualification parser therefore remains compatible with the JSONL evidence format; only the emission timing changes.

The current diagnostic ring stores the latest 256 slices. Operators must keep serial capture active through scenario stop/end so the post-run dump is retained. For long scenarios, the ring intentionally represents the latest bounded evidence window rather than claiming an unbounded full-run trace.

The macro defaults to `0`, so normal production firmware allocates no qualification ring and emits no VM-RT JSONL.

## Dual-budget evidence identity

Every physical run must record both scheduler fields:

```json
"slice_configuration": {
  "max_work_units": 16,
  "max_duration_us": 2000
}
```

These are the current provisional corrective runtime values, not approved thresholds. The qualification tool rejects physical metadata missing either field, and the campaign aggregator refuses to combine reports from different dual-budget configurations.

## Acceptance mapping

- Slice timing/reason: `sliceDurationUs`, `workUnits`, `reason`.
- Wall-clock scheduler exit: `TimeBudgetExhausted` when the optional duration ceiling is reached between work units.
- Longest indivisible call candidate: `maxWorkUnitDurationUs` + `maxWorkUnitProgramCounter`.
- Pending diagnostics: operation/lifecycle/owner/generation/opcode fields.
- Snapshot freshness/read count: sequence/age/read/consumer/invalid/valid fields.
- Stop/abort latency: firmware control-plane observation window plus last/max aggregation.
- Observer safety: no JSON transmission in the active `runVmSlice` path; RAM records are emitted only after motion stops.
- Runtime semantics: legacy `Step()` remains unchanged.

## Follow-up

Physical qualification must use the exact CI-verified firmware commit and dual-budget configuration, execute representative long-running/line-follow/stop scenarios, retain the post-stop JSONL dump, and correlate end-to-end sensor→decision→motor timing with external physical evidence where required. Threshold approval remains blocked until those measurements are reviewed.
