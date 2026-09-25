# VM Cooperative Pending-State Implementation Note

Tracking: #306, parent #302
Baseline: `main@68e13ec43c85040d3319d311b94c2770049522d5`

## Scope

This note records the VM-RT D implementation of reusable cooperative runtime state. It builds on the bounded `RunSlice` core from #305 and does not yet convert additional blocking operations; that remains #307.

## Generic state model

`VMPendingState` is the shared state holder for cooperative logical instructions. It records:

- pending operation kind (`None`, `Wait`, `Line` today);
- lifecycle (`Idle` or `Pending`);
- owning program counter;
- generation counter for successive logical operations.

The owner PC is captured only when the state enters a new pending generation. Re-entering the same operation at the same PC is treated as resume and does not create a new generation. This prevents the state layer from replaying initialization merely because the scheduler calls `Step()` again.

## Compatibility shim

Existing VM dispatch currently writes:

```cpp
mContext.mPendingOperation = VMPendingOperation::Wait;
```

or:

```cpp
mContext.mPendingOperation = VMPendingOperation::Line;
```

`VMPendingState::operator=(VMPendingOperation)` intentionally preserves this source shape while routing the transition through the generic `Begin(...)` logic and capturing the current PC. This keeps `VM.cpp` dispatch behavior stable while removing the need to create per-opcode pending-state structures.

## Lifecycle

Conceptually:

```text
IDLE
  -> Begin(kind, ownerPc)
  -> PENDING generation N

PENDING generation N
  -> same kind + same ownerPc
  -> RESUME (generation unchanged)

PENDING generation N
  -> logical completion / stop / fault cleanup
  -> Clear()
  -> IDLE

VM Reset
  -> HardReset()
  -> IDLE, generation = 0
```

Completion remains defined by the opcode contract: the pending state is cleared, then the PC advances exactly once on successful logical completion. Stop/fault/reset clear pending state without advancing the PC as successful completion.

## Deadline helper

`VMContext::IsPendingDeadlineReached(nowMs)` defines the reusable wrap-safe deadline comparison for wait-like operations using signed subtraction over the monotonic `uint32_t` millisecond clock:

```cpp
static_cast<int32_t>(nowMs - mPendingDeadlineMs) >= 0
```

#307 may migrate concrete timed operations onto this helper while preserving existing observable semantics.

## Yield policy

The `RunSlice` result contract remains:

- pending `Wait` -> `Waiting`;
- other pending cooperative work -> `Yielded`;
- work budget consumed -> `BudgetExhausted`;
- normal program completion -> `Halted`;
- externally stopped VM -> `Stopped`;
- VM error -> `Fault`.

A pending operation remains owned by its current PC until completion/cancel/reset/fault. `VMContext::PendingOperationOwnedByCurrentPc()` exposes this invariant for diagnostics/tests and future instrumentation.

## Compatibility

Unchanged by #306:

- opcode numbers and bytecode encoding;
- compiler output;
- Robot Language API;
- legacy `Step()` one-dispatch semantics;
- existing Wait and cooperative line completion behavior;
- compatibility generation.

No hard wall-clock responsiveness claim is added here. Synchronous indivisible RobotAPI calls identified by #303 remain for #307/#310.

## Acceptance mapping

- Generic pending state lifecycle: `VMPendingState`.
- Owner identity: captured program counter.
- Initialization replay guard: same operation + same owner does not start a new generation.
- Exactly-once completion: preserved legacy clear-then-PC-advance paths.
- Cleanup: existing Reset/Start/stop/fault paths continue to clear pending state; hard VM reset also resets generation.
- Monotonic deadline primitive: `IsPendingDeadlineReached`.
- Regression evidence: VM responsiveness source gate plus ESP32 compile-only impacted CI.

## Out of scope

- Converting `SetMp3Play` or other remaining blocking operations.
- Shared line-sensor snapshot implementation.
- Main-loop `RunSlice` integration.
- Timing instrumentation/physical latency qualification.
