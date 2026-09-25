# VM Responsiveness Instrumentation

Tracking: #310, parent #302
Baseline: `main@1726a41b5c8b70ef7bb4c5c66044c4272adce7f4` (merged #309 / PR #321)

## Purpose

VM-RT H turns responsiveness into measurable evidence without changing VM scheduling decisions, bytecode, opcode semantics, or cooperative pending behavior.

## Per-slice evidence

`VMRunSliceResult` now carries diagnostic observations in addition to the existing stop reason/work-unit/PC contract:

- total slice duration in microseconds;
- work units executed;
- termination reason;
- slowest indivisible work-unit duration and the PC that owned it;
- pending operation, lifecycle, owner PC, generation, and pending opcode;
- line snapshot validity, sequence, age, physical read count, consumer count, and invalid count.

A work unit is one legacy `Step()` call. Therefore `maxWorkUnitDurationUs` identifies the scheduler-visible indivisible unit that consumed the most wall-clock time in the slice. It does not claim to isolate time inside a nested RobotAPI implementation; it identifies the PC/work unit to investigate.

## Snapshot timing

Snapshot evidence is captured by `RunSlice()` before the RAII line-snapshot cycle closes. A valid line snapshot therefore has an age measured from the shared sample timestamp to slice termination. No getter performs an extra refresh for instrumentation.

## Stop/abort latency

The firmware measures an upper-bound stop/abort observation window around its control-plane service phase:

```text
firmware cycle enters serial/network service
  -> command/service may stop VM
  -> firmware observes VM non-running
  -> RecordStopLatency(elapsed_us)
```

This measures the bounded scheduling/control-plane observation window rather than pretending to know transport latency before the firmware received the command.

## Aggregation

`VMRuntimeTelemetry` records:

- slice count;
- latest slice evidence;
- maximum slice duration;
- maximum work-unit duration and PC;
- latest and maximum stop/abort observation latency.

The VM never reads this state, so telemetry cannot influence scheduling decisions.

## Physical / host evidence format

When built with:

```text
-DVM_RESPONSIVENESS_DIAGNOSTICS=1
```

one JSONL record can be emitted for each VM slice. The stable record begins with:

```json
{"type":"vm_rt","slice":1,"duration_us":123,"work_units":4,"reason":0}
```

and also contains PC, pending-operation, line-snapshot, slowest-work-unit, and stop-latency fields. This is intentionally machine-readable so a host capture script or physical qualification harness can parse the same evidence.

The macro defaults to `0`, so normal production firmware does not print per-cycle telemetry to Serial. Measurement fields remain observational and do not change VM behavior.

## Acceptance mapping

- Slice timing/reason: `sliceDurationUs`, `workUnits`, `reason`.
- Longest indivisible call candidate: `maxWorkUnitDurationUs` + `maxWorkUnitProgramCounter`.
- Pending diagnostics: operation/lifecycle/owner/generation/opcode fields.
- Snapshot freshness/read count: sequence/age/read/consumer/invalid/valid fields.
- Stop/abort latency: firmware control-plane observation window plus last/max aggregation.
- Runtime semantics: `Step()` remains unchanged; instrumentation is read-only from the scheduler's perspective.

## Follow-up

Physical qualification should capture JSONL with diagnostics enabled, execute representative long-running/line-follow/stop scenarios, and attach timing distributions and worst-case evidence to the VM-RT qualification issue.
