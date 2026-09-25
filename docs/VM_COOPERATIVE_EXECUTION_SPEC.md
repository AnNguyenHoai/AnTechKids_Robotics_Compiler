# VM Cooperative Execution Specification

## 1. Purpose

This document defines the normative cooperative execution contract for the ESP32 VM. It complements `ROBOT_EXECUTION_MODEL.md` and is the implementation reference for `RunSlice(...)`, yield behavior, resumable operations, stop/abort handling, and scheduling tests.

## 2. Design goals

The cooperative execution model must:

- return control to the firmware loop regularly;
- preserve deterministic bytecode order;
- preserve legacy `Step()` behavior;
- support time-spanning operations without long blocking loops;
- make pending state explicit and testable;
- avoid compiler/bytecode special cases for responsiveness;
- remain compatible with H35 policy unless an explicit generation change is approved.

## 3. Non-goals

This phase does not require:

- preemptive multitasking;
- RTOS task migration of the VM;
- opcode renumbering;
- source-language syntax changes;
- converting every hardware read into cached I/O;
- redefining all historical blocking APIs at once.

## 4. `Step()` contract

`Step()` remains the legacy compatibility primitive.

A `Step()` call dispatches according to the current opcode contract and preserves current program-counter, halt, and error semantics. New responsiveness work must not turn `Step()` into a scheduler abstraction or silently execute multiple instructions.

Tests must retain direct coverage of `Step()` so cooperative work cannot hide compatibility regressions.

## 5. `RunSlice` contract

Conceptual API:

```cpp
RunSliceResult RunSlice(const RunSliceBudget& budget);
```

Exact C++ names/types may differ, but the semantics are normative.

### 5.1 Input budget

A slice must have at least one deterministic work bound. The recommended model is:

- primary bound: maximum completed/attempted instruction-work units;
- optional safety bound: elapsed wall-clock microseconds/milliseconds for instrumentation and protection.

Wall-clock time alone should not be the only semantic budget because host tests and different hardware speeds must remain deterministic.

### 5.2 Slice termination reasons

A slice returns when the first applicable condition occurs:

1. `BUDGET_EXHAUSTED`
2. `YIELDED`
3. `WAITING`
4. `HALTED`
5. `STOPPED` / `ABORTED`
6. `FAULT`

The concrete enum may use different names, but these states must remain distinguishable for tests and diagnostics.

### 5.3 Progress guarantee

If the VM is runnable, no stop/fault exists, and the current instruction is not waiting on time/hardware, successive slices must make forward progress.

A cooperative pending instruction must not repeatedly re-run its initialization side effects.

## 6. Runtime state model

Time-spanning instructions require explicit pending state. At minimum the state must identify:

- whether an instruction is pending;
- the opcode/instruction identity or program counter owning the state;
- operation-specific state;
- optional start/deadline timestamp;
- whether initialization side effects have already been applied.

Invariant:

> Pending state belongs to exactly one logical in-flight instruction and is cleared only on completion, abort/reset, or fault handling defined by that instruction.

## 7. Program counter rules

For every instruction converted from blocking to cooperative execution:

1. entering pending state does **not** imply completion;
2. yielding while pending does **not** advance the PC;
3. PC advances exactly once when the logical instruction completes;
4. abort/fault must not advance PC as though the operation completed successfully;
5. re-entry into the instruction must resume from pending state rather than replay one-time side effects.

These rules are mandatory regression targets.

## 8. Cooperative wait

For a duration-based wait:

```text
IDLE
  -> encounter wait(t)
  -> validate t
  -> save deadline
  -> WAITING + yield

WAITING
  -> now < deadline: yield, no PC advance
  -> now >= deadline: clear state, PC += 1, continue/return according to budget
```

The implementation must use a monotonic platform time source suitable for elapsed-time comparisons and must handle timer wrap according to platform conventions.

A cooperative wait must not use a busy loop or long `delay(...)` that prevents the firmware loop from running.

## 9. Cooperative timed motion / line operations

An existing operation that currently performs:

```text
start motor/follower
while duration/condition not complete:
    sample/update
stop
return
```

must be decomposed conceptually into:

```text
INIT
  -> initialize operation once
  -> store runtime state
  -> yield

ACTIVE
  -> perform one bounded update/sample step
  -> condition incomplete: yield
  -> condition complete: finalize once, clear state, advance PC
```

The conversion must preserve:

- initial command semantics;
- termination condition;
- final stop/finalization semantics;
- PC advancement;
- error behavior;
- externally visible result, subject only to the scheduling improvement defined by this initiative.

## 10. Yield policy classification

Before implementation, every runtime operation reachable from VM dispatch must be classified:

| Class | Meaning | Slice rule |
|---|---|---|
| `IMMEDIATE` | Small deterministic call | May execute inside slice |
| `COOPERATIVE` | Logical operation spans time/iterations | Must keep resumable state and yield |
| `BOUNDED_IO` | Physical I/O with verified finite bound | May execute; duration instrumented |
| `UNRESOLVED` | Timing/side effects not understood | Must be audited before responsive path relies on it |

No operation may be labelled safe only because it currently appears fast on one board.

## 11. External stop and abort

Stop/abort must be observable between bounded work units and while a cooperative operation is pending.

Required behavior:

- clear pending VM operation state;
- invoke required actuator stop/safe transition;
- prevent stale operation completion on next start;
- reset timing/snapshot state as required;
- return a distinguishable stop/abort result.

A stop request must not wait for an entire multi-second duration operation to finish.

## 12. Fault behavior

A runtime fault during cooperative execution must:

- stop forward VM progress;
- preserve enough diagnostic context to identify PC/opcode/reason;
- clear or quarantine pending state deterministically;
- avoid PC advancement as success;
- apply existing safety behavior for active actuators.

The responsiveness feature must not swallow legacy errors and convert them into yields.

## 13. Main-loop integration contract

The main loop should follow this conceptual order:

```text
service platform responsibilities
refresh cycle-scoped sensor snapshot
RunSlice(budget)
service output/telemetry/diagnostics
repeat
```

The VM is a participant in the platform loop, not the owner of it.

The chosen slice budget must leave enough time for watchdog, communication, OTA, discovery, diagnostics, and control responsibilities already owned by the firmware.

## 14. Instrumentation

At minimum development/test builds must be able to observe:

- slice start/end duration;
- work units/instructions attempted/completed;
- termination reason;
- current/pending opcode and PC;
- time spent in indivisible RobotAPI calls;
- wait age/deadline state;
- stop/abort latency.

Instrumentation must not materially change production control behavior.

## 15. Compatibility requirements

- No opcode-number change is required by this spec.
- No bytecode-format change is required by this spec.
- Compiler output must remain valid for current firmware generation unless H35 review decides otherwise.
- `Step()` remains available and compatible.
- Existing full regression must pass together with new cooperative-execution tests.

## 16. Required test categories

Implementation PRs must cover:

1. budget exhaustion with deterministic PC progress;
2. wait yields without blocking;
3. deadline completion advances PC once;
4. timed operation initialization occurs once;
5. repeated slices resume correctly;
6. stop/abort interrupts pending operation;
7. fault does not masquerade as yield;
8. `Step()` compatibility;
9. long-running loop repeatedly returns to caller;
10. full repository regression.

## 17. Definition of Done

This spec is implemented only when `RunSlice` and all in-scope cooperative operations satisfy the state/PC/yield rules above, instrumentation exists, CI tests are deterministic, and physical qualification confirms that the firmware loop remains responsive under representative robot programs.
