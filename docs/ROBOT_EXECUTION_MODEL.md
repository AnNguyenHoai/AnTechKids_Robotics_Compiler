# Robot Execution Model

## 1. Purpose

This document is the normative execution-model contract for VM responsiveness work. It defines how bytecode execution, control-loop scheduling, RobotAPI calls, yielding, timing, sensor sampling, stop/abort, and compatibility must interact.

The goal is not to make the VM merely "faster". The goal is to make robot control responsiveness explicit, bounded, testable, and compatible with the existing compiler/ISA/runtime pipeline.

## 2. Scope

In scope:

- VM instruction execution and scheduler ownership;
- legacy single-step execution compatibility;
- cooperative execution slices;
- yield and wait semantics;
- sensor/control-cycle interaction;
- stop, abort, halt, and runtime-fault behavior;
- timing instrumentation and acceptance boundaries.

Out of scope for this documentation phase:

- changing opcode numbers or bytecode encoding;
- adding line-follow-specific compiler rewrites;
- changing Robot Language source semantics;
- changing compatibility generation without an explicit H35 review;
- implementing runtime code before the contracts are approved.

## 3. Existing compatibility baseline

The current repository already contains blocking runtime behavior for some line operations. For example, C2 documents `LineMillisecond` as a blocking RobotAPI operation whose program counter advances once after the operation completes.

This VM-responsiveness initiative MUST NOT silently reinterpret all legacy behavior. Instead it introduces a cooperative execution path while preserving the observable contract of existing programs unless a separately reviewed compatibility change is required.

## 4. Execution modes

### 4.1 `Step()` — legacy compatibility mode

`Step()` remains the compatibility primitive.

Normative requirements:

1. One call preserves the current instruction-dispatch semantics.
2. Program-counter movement remains exactly as defined by the current opcode implementation.
3. Existing halt/error behavior remains unchanged.
4. Existing tests that directly exercise `Step()` must continue to pass.
5. The responsiveness initiative MUST NOT redefine `Step()` into a multi-instruction scheduler call.

### 4.2 `RunSlice(...)` — cooperative execution mode

`RunSlice(...)` is the target scheduling primitive for responsive execution.

A slice executes bounded VM work and returns control to its caller when the first of these conditions occurs:

- the configured instruction/work budget is exhausted;
- a cooperative yield is requested;
- a non-blocking wait is pending;
- the program halts normally;
- a runtime fault occurs;
- an external stop/abort request must be honored.

`RunSlice(...)` MUST NOT rely on an unbounded loop around `Step()`.

### 4.3 Scheduler ownership

The outer robot loop owns scheduling. The VM does not own the firmware main loop.

Conceptual flow:

```text
firmware/control loop
    -> refresh cycle-scoped inputs
    -> VM RunSlice(budget)
    -> apply/maintain outputs
    -> diagnostics/instrumentation
    -> return to platform loop
```

The platform must regain control regularly enough to service safety, communication, telemetry, OTA/watchdog, and control-loop responsibilities.

## 5. Cooperative execution invariants

The implementation MUST preserve these invariants:

1. Instruction order remains deterministic.
2. A yielded operation resumes from explicit runtime state; it is not restarted accidentally.
3. Program-counter advancement occurs exactly once per completed instruction according to that opcode's contract.
4. A pending timed operation must not monopolize the firmware thread with a busy wait or long delay.
5. A slice has a finite execution bound defined by budget and by the maximum indivisible runtime operation.
6. Stop/abort can be observed at slice boundaries and at cooperative yield points.
7. No line-follow-only scheduling special case may be added to the compiler or bytecode format.

## 6. Time and wait semantics

A wait has two semantic layers:

- language/bytecode meaning: execution must not continue past the wait until the requested duration has elapsed;
- runtime scheduling behavior: the firmware thread must be released while that time is pending.

Target cooperative model:

```text
first encounter WAIT(t)
    -> validate t
    -> record deadline
    -> mark instruction pending
    -> yield

subsequent slice
    -> deadline not reached: yield again
    -> deadline reached: complete WAIT, advance PC once
```

A negative or otherwise invalid duration follows the existing opcode/API validation contract; this initiative does not invent new source-language semantics.

## 7. Timed, blocking, and CPU-bound runtime operations

Every operation used by the VM must be classified before implementation as one of:

- `IMMEDIATE`: expected to complete within a small, bounded call;
- `COOPERATIVE`: may span time/work and therefore requires resumable runtime state;
- `BOUNDED_IO`: performs physical I/O but has a measured upper bound;
- `UNRESOLVED`: behavior/timing not yet safe to classify.

An `UNRESOLVED` operation MUST NOT be treated as cooperative-safe by assumption.

Long movement/line operations currently implemented as blocking loops are candidates for conversion to resumable cooperative state. Conversion must preserve externally visible command semantics and must be covered by compatibility tests.

CPU-bound opcodes are subject to the same rule. A `RunSlice` work-unit count is not a real responsiveness bound if one opcode can perform unbounded data-dependent work inside a single `Step()`. Such opcodes must either have a deterministic indivisible upper bound or yield through explicit pending state. `Pow` is the reference implementation: legacy repeated-multiply ordering is preserved, but only a fixed number of multiplications are allowed per `Step()` and the PC remains owned by the pending instruction until completion.

## 8. Sensor execution model

Sensor handling has two categories.

### 8.1 Control-cycle snapshot sensors

Sensors that participate in one logical control decision, especially multi-channel line sensors, should expose one shared snapshot per control cycle. Multiple getters within that cycle must observe values from the same sample.

The detailed contract is defined in `LINE_SENSOR_SNAPSHOT_CONTRACT.md`.

### 8.2 On-demand sensors

Expensive or naturally request/response I/O may remain on-demand unless a separate contract requires caching. The responsiveness work MUST NOT introduce broad, implicit caching of all hardware reads.

Diagnostics should avoid duplicate physical reads when one sampled value can be safely reused for the same reporting cycle.

## 9. Stop, abort, halt, and fault

The VM must distinguish:

- `HALTED`: program completed normally;
- `YIELDED`: execution is valid and intentionally returned control;
- `WAITING`: execution is valid but a pending deadline/operation prevents forward progress;
- `STOP_REQUESTED` / `ABORTED`: external control requested termination;
- `FAULT`: invalid instruction/state/runtime failure.

Exact public enum names are implementation details until code review, but tests and logs must be able to distinguish these outcomes.

On stop/abort:

1. pending cooperative state must be cleared deterministically;
2. motors/actuators must transition according to the existing safety/stop contract;
3. the program counter must not advance as if an unfinished operation completed;
4. the next start must not inherit stale deadlines or sensor snapshots.

## 10. Responsiveness budget

The implementation must expose measurable evidence for:

- maximum VM slice duration;
- instruction/work count per slice;
- number/reason of yields;
- maximum duration of indivisible runtime calls;
- sensor-sample age used by a control decision;
- stop/abort response latency.

Exact production thresholds are established by physical qualification, not guessed in this document. CI must still enforce deterministic host-side bounds and regression behavior.

## 11. Compatibility guards

The following are mandatory guards for this initiative:

1. `Step()` compatibility is preserved.
2. Existing opcode numbers and bytecode encoding are unchanged unless a dedicated ISA change is approved.
3. Compiler output is not rewritten specifically for line-follow responsiveness.
4. Existing source programs preserve observable behavior unless an explicit migration is documented.
5. H35 compatibility generation/policy is reviewed before any semantic change that alters compiler/firmware compatibility.
6. Full regression gates remain green in addition to new responsiveness tests.

## 12. Definition of Done

This execution-model initiative is complete only when:

- cooperative `RunSlice` behavior is implemented and bounded;
- blocking/time-spanning/runtime-data-dependent work covered by the project has explicit bounded/yield policy;
- line sensor reads used in one control cycle are snapshot-consistent;
- main-loop integration regularly returns control to firmware;
- stop/abort behavior is deterministic;
- timing instrumentation exists;
- host CI covers compatibility and responsiveness;
- physical robot qualification demonstrates acceptable control response;
- H35 compatibility review is complete;
- documentation reflects the final implementation rather than an aspirational design.

## 13. Related documents

- `docs/C2_VM_DISPATCH_CONTRACT.md`
- `docs/H35_COMPATIBILITY_UPGRADE_POLICY.md`
- `docs/VM_COOPERATIVE_EXECUTION_SPEC.md`
- `docs/LINE_SENSOR_SNAPSHOT_CONTRACT.md`
- `docs/VM_RESPONSIVENESS_COMPATIBILITY_MATRIX.md`
- `docs/VM_RESPONSIVENESS_ACCEPTANCE_TEST_PLAN.md`
- `docs/VM_RESPONSIVENESS_IMPLEMENTATION_PLAN.md`
