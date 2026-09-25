# VM Responsiveness Acceptance Test Plan

## 1. Purpose

This document defines the minimum evidence required to accept VM real-time responsiveness work. It is intentionally broader than unit tests: the initiative is complete only when host-side behavior, compatibility, firmware integration, instrumentation, and physical robot response are all demonstrated.

## 2. Acceptance philosophy

A test that proves only "the program eventually finishes" is insufficient.

Responsiveness tests must prove:

- the firmware thread is returned regularly;
- long logical operations do not monopolize execution;
- program-counter and side-effect semantics remain deterministic;
- control decisions use coherent sensor data;
- stop/abort can interrupt pending work;
- existing programs remain compatible;
- physical response is acceptable under representative workloads.

## 3. Test layers

### Layer A — VM unit tests

Focus:

- `Step()` compatibility;
- `RunSlice` budget semantics;
- pending operation state;
- PC advancement;
- yield/wait/halt/fault outcome separation;
- reset/abort cleanup.

### Layer B — RobotAPI/service host tests

Focus:

- blocking-point classification;
- resumable timed operations;
- line-snapshot physical-read counts;
- sensor sequence/timestamp consistency;
- actuator initialization/finalization occurs exactly once.

### Layer C — firmware integration tests

Focus:

- main loop regains control between slices;
- watchdog/communication/diagnostic responsibilities remain serviceable;
- VM state remains correct over many cycles;
- stop/abort is honored while an operation is pending.

### Layer D — compiler/ISA regression

Focus:

- no opcode-number drift;
- no bytecode-encoding drift;
- existing compiler output remains executable;
- H32/H33/H34/H35 gates remain green where relevant;
- current line-follow stability regression remains green.

### Layer E — physical robot qualification

Focus:

- real sensor-to-command responsiveness;
- repeated line following under dynamic path changes;
- obstacle detection/control scenarios;
- stop/abort response;
- timing distribution under production-like firmware load.

## 4. Mandatory VM scenarios

### T1 — Slice budget exhaustion

Given a bytecode sequence containing more runnable instructions than the configured slice budget:

- `RunSlice` returns because the budget is exhausted;
- PC reflects only work actually completed;
- the next slice resumes correctly;
- no instruction executes twice due to the boundary.

### T2 — Cooperative wait begins once

Given a wait instruction:

- first encounter stores pending state/deadline;
- PC does not advance;
- slice returns as `WAITING`/equivalent;
- repeated slices before the deadline do not recreate the deadline or repeat initialization.

### T3 — Cooperative wait completes once

When the deadline is reached:

- pending state clears;
- PC advances once;
- execution may continue subject to remaining budget;
- no extra delay is introduced by stale state.

### T4 — Timed actuator operation resumes

For each in-scope converted timed movement/line operation:

- initialization occurs exactly once;
- bounded update work occurs across slices;
- finalization occurs exactly once;
- PC advances only on logical completion.

### T5 — Stop during pending operation

While a wait/timed operation is pending:

- external stop/abort is observed without waiting for the full operation duration;
- motors/actuators enter the defined safe/stop state;
- pending state clears;
- PC does not pretend the operation completed;
- restart does not reuse stale deadline/state.

### T6 — Fault during cooperative execution

A forced runtime fault must:

- return `FAULT`/equivalent, not `YIELDED`;
- stop forward progress;
- preserve diagnostic PC/opcode/reason;
- clear/quarantine pending state safely.

### T7 — Infinite/long-running loop responsiveness

A representative `while True` / forever program must execute over many slices while the caller regains control every cycle. The test must prove forward progress without one slice owning the thread indefinitely.

## 5. Mandatory line-snapshot scenarios

### S1 — Same-cycle consistency

For one control cycle:

- refresh physical line sample once;
- call left/center/right getters in arbitrary order;
- all returned values report the same snapshot sequence;
- physical-read count remains one.

### S2 — Repeated getters

Repeated reads of the same line getter in one cycle do not trigger additional physical samples.

### S3 — Next-cycle refresh

At the next control-cycle refresh:

- a new physical sample can be captured;
- sequence increments;
- getters observe the new sample consistently.

### S4 — Atomic invalid sample

A simulated sensor failure must not produce a valid snapshot assembled from mixed old/new channels.

### S5 — follower/getter consistency

When line follower logic and VM getter logic participate in the same control cycle, they must observe the same sampled state or an explicitly derived representation of that sample.

## 6. Compatibility scenarios

### C1 — `Step()` regression

All existing direct VM dispatch/Step tests pass unchanged unless a separately approved test correction is needed.

### C2 — Existing bytecode replay

Representative bytecode compiled before the responsiveness work must execute with equivalent logical results on the updated VM.

### C3 — ISA/encoding stability

Canonical opcode numbers and bytecode serialization remain unchanged for this initiative unless a dedicated compatibility change is approved.

### C4 — line-follow regression

Existing steering-direction and recovery-stability tests remain green after snapshot/runtime changes.

### C5 — H35 compatibility review

If no compatibility generation change is intended, CI evidence must show the current generation pair remains valid and no frozen SSoT drift occurred unintentionally.

## 7. Instrumentation evidence

Test/development builds must be capable of producing at least:

- per-slice duration;
- work units/instructions per slice;
- slice termination reason;
- longest indivisible runtime call;
- pending opcode/PC;
- line-snapshot sequence and age;
- physical line-read count;
- stop/abort latency.

Host tests may use deterministic fake time. Physical qualification uses monotonic board timing.

## 8. Timing thresholds

This document deliberately does not invent production millisecond thresholds before hardware measurement.

Acceptance follows two steps:

1. **Host deterministic bounds** — prove no unbounded loop/busy wait exists in the cooperative path and every slice respects configured work bounds.
2. **Physical qualification** — collect latency distributions on real hardware under representative workloads, then record approved production thresholds in a follow-up evidence/result document.

No developer may claim "real-time" based solely on average latency or one manual run.

## 9. Physical qualification scenarios

At minimum execute:

1. line following on straight path and curves with repeated correction;
2. lost-line/recovery transitions;
3. line intersection behavior where supported;
4. ultrasonic decision loop with changing obstacle distance;
5. long wait/timed action while platform communication/diagnostics remain alive;
6. stop/abort during active timed operation;
7. sustained run long enough to expose stale pending state or timer-wrap assumptions where practical.

Record firmware commit, board/profile, test program, relevant timing configuration, and observed latency statistics.

## 10. CI gate requirements

Before merge of implementation work:

- dedicated responsiveness tests pass;
- existing VM/compiler tests pass;
- line-follow stability gate passes;
- relevant H32/H33/H34/H35 gates pass;
- full regression runner passes;
- no expected-failure test is silently converted to pass by weakening assertions.

## 11. Definition of Done

The initiative is accepted only when:

- every mandatory host scenario passes;
- instrumentation demonstrates bounded cooperative execution;
- snapshot tests prove same-cycle consistency;
- compatibility gates remain green or an explicit compatibility upgrade is approved;
- physical robot evidence demonstrates acceptable responsiveness;
- measured production thresholds and final implementation status are documented.
