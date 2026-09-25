# VM Time-Spanning Operations Implementation Note

Tracking: #307, parent #302
Baseline: `main@b90e1e680ea982ceb9dcc9b5b5aca6994575907b`

## Scope

VM-RT E converts in-scope logical delays/timed VM operations so the firmware thread is not occupied for the operation's full logical duration. It preserves opcode/bytecode/compiler contracts and builds on the generic pending state from #306.

## Converted operations

### `Wait`

`Wait` was already cooperative before #307. This task migrates its completion check to the shared wrap-safe `VMContext::IsPendingDeadlineReached(...)` primitive so all deadline-driven VM operations use the same timing contract.

Behavior remains:

1. first encounter validates duration;
2. duration <= 0 completes immediately;
3. positive duration enters `VMPendingOperation::Wait`, stores deadline, and returns without PC advance;
4. resume before deadline returns with PC unchanged;
5. resume at/after deadline clears pending state and advances PC exactly once.

No `delay(...)` or `RobotAPI::Wait(...)` occurs on the VM Wait path.

### `SetMp3Play`

The legacy public `RobotAPI::SetMp3Play(index)` remains blocking for non-VM compatibility. VM dispatch no longer calls it.

Two additive RobotAPI primitives are introduced:

- `BeginMp3PlayCooperative(index)` — enables the buzzer and returns the logical duration (200 ms), or 0 when the buzzer capability is disabled;
- `EndMp3PlayCooperative()` — disables the buzzer immediately.

VM behavior is now:

```text
first SetMp3Play Step
  -> BeginMp3PlayCooperative(index)
  -> pending kind = Mp3Play
  -> deadline = now + returned duration
  -> PC unchanged
  -> return

resume before deadline
  -> PC unchanged
  -> return

resume at/after deadline
  -> EndMp3PlayCooperative()
  -> clear pending
  -> PC++ exactly once
```

`RunSlice` reports both `Wait` and `Mp3Play` as `Waiting`; line operations remain `Yielded`.

## Cancellation semantics

`VM::CancelPendingOperation(stopLineMotors)` centralizes cooperative cleanup.

On reset, start/restart, diagnostic stop, normal end cleanup, or VM fault:

- cooperative line work is cancelled;
- a pending `Mp3Play` forces the buzzer LOW;
- pending ownership is cleared;
- cancellation does **not** advance the PC as successful completion.

This prevents stale pending state and prevents a buzzer from remaining active after abort/reset/fault.

## Compatibility

Unchanged:

- opcode numbering and encoding;
- compiler output;
- Robot Language API;
- firmware compatibility generation;
- direct public `RobotAPI::SetMp3Play` blocking semantics for existing non-VM callers;
- `Step()` one-dispatch semantics;
- line-operation cooperative semantics.

The VM observable semantics of `SetMp3Play` remain a fixed 200 ms logical operation, but the 200 ms interval no longer blocks the VM execution thread.

## Acceptance mapping

- T2 cooperative wait starts once: Wait enters one pending generation and holds PC.
- T3 wait completes once: clear then PC advance only after deadline.
- T4 timed operation resumes: `SetMp3Play` uses pending/deadline/resume.
- T5 stop during pending operation: centralized cancellation forces buzzer off and clears pending without success PC advance.

The deterministic host gate `tests/vm_responsiveness/run_run_slice_core.py` verifies these source-level contracts. Impact CI also compiles ESP32 firmware to catch integration/link errors.

## Remaining indivisible/blocking work

#307 does not claim all VM work is now wall-clock bounded. Remaining findings from #303 are:

| Runtime path | Current status | Follow-up |
|---|---|---|
| Ultrasonic `pulseIn` | bounded synchronous I/O, configured up to ~50 ms | #310 measurement/instrumentation; future conversion only if required by measured target |
| `Pow` exponent loop | runtime-data-dependent CPU loop | #310 measurement; explicit bound/slicing if necessary |
| touch/light/color reads | synchronous device I/O, timing not yet qualified | #310 |
| line sensor/read tick | synchronous sensor/control tick | #308 snapshot + #310 timing |
| public `RobotAPI::Wait` | intentionally blocking public API; VM does not call it | #313 compatibility closure |
| public blocking line helpers | intentionally retained for non-VM compatibility; VM already uses `CooperativeLineOperation` | #313 compatibility closure |
| public `RobotAPI::SetMp3Play` | intentionally blocking compatibility API; VM uses additive cooperative primitive | #313 compatibility closure |

The longest known configured indivisible VM-reachable I/O remains the ultrasonic read timeout (~50 ms). A production wall-clock responsiveness threshold is intentionally deferred until #310 instrumentation and #312 physical qualification.
