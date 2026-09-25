# VM Line Sensor Snapshot Implementation Note

Tracking: #308, parent #302
Baseline: `main@88b672b9bc5375cbbe554446a3dda115a83959a1`

## Scope

VM-RT F implements one shared line-sensor snapshot per `RunSlice` control cycle. It does not alter opcode numbers, compiler output, thresholds, channel ordering, or line-follow steering algorithms.

## Owner and cycle boundary

`LineSensorSnapshot` is the single sampling owner. `RunSlice()` opens one snapshot cycle through `LineSnapshotCycleGuard` and closes it on every return path through RAII.

Sampling is lazy:

```text
RunSlice begin
  -> BeginCycle()
  -> no hardware read yet
  -> first line consumer
       -> EnsureSample()
       -> sample left + center + right exactly once
       -> sequence++
       -> timestamp captured
       -> snapshot valid
  -> additional line consumers in same slice
       -> reuse same sample
       -> no additional physical reads
RunSlice end
  -> EndCycle()
  -> snapshot valid=false
```

Therefore a slice that does not access line sensors performs no line-sensor I/O.

## Integration with existing RobotAPI getters

Existing RobotAPI code continues to call `TCRT5000::update()`. The TCRT driver now detects an active snapshot cycle:

- in-cycle: `update()` delegates to the snapshot owner and reuses the cached channel values;
- outside a snapshot cycle: `update()` performs its legacy direct hardware read.

This preserves direct/non-VM RobotAPI compatibility while ensuring VM/control work inside one `RunSlice` sees one coherent L/C/R sample set.

`GetTraceRaw()` may still invoke `update()` on left, center, and right, but after the first call in a cycle the remaining calls are cache consumers rather than physical reads.

## Snapshot model

The snapshot exposes:

- `left`, `center`, `right`;
- derived bit mask with existing ordering `left=4`, `center=2`, `right=1`;
- `timestampUs`;
- monotonically increasing `sequence`;
- `valid`;
- `physicalReadCount` for the current cycle;
- `consumerCount` for the current cycle;
- cumulative `invalidCount`.

A successful sample set performs exactly three physical reads, one per channel.

## Invalid sample policy

The owner resolves all three sensor instances before sampling. If one channel is unavailable, the cycle is marked invalid atomically and the existing RobotAPI fallback value `0` is applied consistently to available channel objects rather than combining new and stale values.

At `EndCycle()`, `valid` becomes false. Sequence, timestamp and sampled values remain available as diagnostic evidence, but they cannot be interpreted as a current-cycle sample.

## Compatibility

Unchanged:

- TCRT threshold comparison (`_lastReading == _threshold`);
- logical channel ordering;
- line-follow state machine and steering decisions;
- VM bytecode and compiler output;
- H35 compatibility generation;
- direct TCRT/RobotAPI behavior outside an explicit snapshot cycle.

The only intended semantic change is same-cycle sampling consistency.

## Acceptance mapping

- S1: first in-cycle line consumer produces one L/C/R snapshot and one sequence.
- S2: repeated same-cycle getter/update calls reuse `g_sampledThisCycle`; physical-read count remains three.
- S3: next `RunSlice` starts a new cycle and the next line access increments sequence.
- S4: missing channel produces one atomic invalid snapshot with mask/value fallback rather than mixed timestamps.
- S5: line follower and VM getters use the same TCRT cached values when they execute in one `RunSlice` cycle.
- Stale-state guard: `EndCycle()` marks the previous sample invalid.

The deterministic host contract gate lives in `tests/vm_responsiveness/run_run_slice_core.py`. Existing line-follow stability regression and ESP32 firmware compile remain mandatory impacted-CI gates.

## Follow-up

#309 will integrate `RunSlice` into the firmware main loop and make the platform control-loop boundary operational in production. #310 will add timing/age/read-count instrumentation suitable for runtime diagnostics and measurement. Physical behavior remains qualified by #312.
