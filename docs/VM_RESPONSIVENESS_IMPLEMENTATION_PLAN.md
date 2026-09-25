# VM Responsiveness Implementation Plan

## 1. Purpose

This plan turns the VM Real-Time Control Responsiveness architecture into an implementation sequence that keeps contracts, compatibility, tests, and hardware qualification synchronized.

The ordering is intentional. A later phase must not bypass an unresolved dependency from an earlier phase.

## 2. Source-of-truth documents

Implementation and review must use these documents together:

- `docs/ROBOT_EXECUTION_MODEL.md`
- `docs/VM_COOPERATIVE_EXECUTION_SPEC.md`
- `docs/LINE_SENSOR_SNAPSHOT_CONTRACT.md`
- `docs/VM_RESPONSIVENESS_COMPATIBILITY_MATRIX.md`
- `docs/VM_RESPONSIVENESS_ACCEPTANCE_TEST_PLAN.md`
- existing `docs/C2_VM_DISPATCH_CONTRACT.md`
- existing `docs/H35_COMPATIBILITY_UPGRADE_POLICY.md`

When implementation discovers that a contract is incomplete or wrong, update the relevant document in the same PR or in a preceding docs PR. Code must not silently become the new source of truth.

## 3. Global implementation rules

1. Preserve `Step()` semantics.
2. Do not change opcode numbers or bytecode encoding unless a dedicated ISA/H35 change is approved.
3. Do not special-case line-follow in the compiler to hide runtime scheduling problems.
4. Convert blocking behavior by preserving logical instruction semantics while improving firmware scheduling behavior.
5. Every time-spanning operation requires explicit pending/resume state.
6. Program counter advances exactly once on logical completion.
7. Stop/abort must interrupt pending work deterministically.
8. Line getters in one control cycle use one shared snapshot.
9. New tests are additive to existing regression gates.
10. No implementation PR is merged without compatibility classification and evidence.

## 4. Work breakdown A–K

### A — Runtime Blocking-Point Audit

**Goal:** create a verified inventory of VM-dispatched operations and their timing/blocking behavior.

**Work:**

- enumerate VM dispatch cases;
- trace each case into RobotAPI/service/driver calls;
- identify `delay`, busy loops, duration loops, polling loops, repeated sensor reads, and unbounded work;
- classify each operation as `IMMEDIATE`, `COOPERATIVE`, `BOUNDED_IO`, or `UNRESOLVED`;
- record current PC and side-effect behavior.

**Deliverable:** blocking/yield classification matrix.

**DoD:** no VM-reachable runtime operation remains unclassified for the target scope.

### B — Compatibility Baseline and Regression Matrix

**Goal:** freeze the behavior that responsiveness work must preserve.

**Work:**

- capture representative pre-change bytecode/programs;
- identify direct `Step()` regression tests;
- map C2 blocking semantics that will later receive cooperative scheduling;
- document H35 impact per proposed change;
- add/prepare regression fixtures before behavior changes.

**DoD:** reviewers can distinguish intended scheduling change from accidental semantic drift.

### C — Bounded `RunSlice` Core

**Goal:** add the cooperative scheduler primitive without converting blocking RobotAPI behavior yet.

**Work:**

- define slice budget/result types;
- implement bounded dispatch loop;
- distinguish budget/yield/wait/halt/stop/fault outcomes;
- add instrumentation hooks;
- preserve direct `Step()` path.

**DoD:** purely runnable bytecode executes across deterministic slices; budget and PC tests pass; `Step()` tests remain green.

### D — Cooperative Runtime State and Yield Policies

**Goal:** establish reusable infrastructure for resumable instructions.

**Work:**

- add explicit pending-operation state;
- define init/resume/complete/reset lifecycle;
- implement monotonic deadline helper for timed work;
- define stop/fault cleanup;
- prohibit replay of one-time side effects.

**DoD:** generic pending-state tests pass, including reset/abort and exactly-once completion semantics.

### E — Convert Wait/Time-Spanning VM Operations

**Goal:** remove firmware-thread blocking from in-scope waits/timed runtime work.

**Work:**

- convert wait/delay semantics to deadline + yield;
- convert selected timed movement/line operations according to audit priority;
- preserve completion/finalization and PC semantics;
- measure longest indivisible call remaining.

**DoD:** in-scope operations no longer monopolize firmware thread for their logical duration; acceptance tests T2–T5 pass.

### F — Shared Line Sensor Snapshot

**Goal:** guarantee one coherent line sample per control cycle.

**Work:**

- choose single snapshot owner;
- add sequence/timestamp/validity;
- refresh once per cycle;
- serve line getters and follower logic from the shared sample;
- eliminate duplicate same-cycle reads;
- preserve existing thresholds/channel semantics.

**DoD:** S1–S5 snapshot tests pass and existing line-follow stability gate remains green.

### G — Firmware Main-Loop Integration

**Goal:** make bounded VM execution a first-class participant in the platform loop.

**Work:**

- define cycle order for platform service, sensor refresh, `RunSlice`, outputs, diagnostics;
- choose initial conservative slice budget;
- ensure communication/watchdog/OTA/discovery responsibilities remain serviceable;
- integrate stop/abort observation at bounded points.

**DoD:** long-running programs repeatedly return control to firmware and integration tests show platform responsibilities continue to run.

### H — Timing and Responsiveness Instrumentation

**Goal:** replace subjective responsiveness claims with measurable evidence.

**Work:**

- record slice duration and work units;
- record termination/yield reasons;
- measure longest indivisible RobotAPI/service call;
- expose pending PC/opcode for diagnostics;
- expose line snapshot age/sequence/read count;
- measure stop/abort latency.

**DoD:** test/development builds can produce the evidence required by the acceptance plan without materially altering runtime behavior.

### I — Host CI and Regression Gates

**Goal:** make responsiveness and compatibility machine-verifiable.

**Work:**

- add dedicated VM responsiveness test runner;
- add snapshot contract tests;
- add compatibility fixtures/replay tests;
- integrate with current CI topology;
- ensure existing VM/compiler/line-follow/H35 gates remain required.

**DoD:** CI fails on budget violations, PC double-advance, blocking regression, snapshot inconsistency, Step incompatibility, or forbidden contract drift.

### J — Physical Robot Qualification

**Goal:** verify the architecture under real sensor/motor/timing conditions.

**Work:**

- execute line-follow, recovery, intersection where supported, ultrasonic decision loop, timed operation, and stop/abort scenarios;
- capture latency distributions and worst observed values;
- record hardware/profile/firmware/test-program identity;
- tune slice budget only from measured evidence;
- identify remaining blocking outliers.

**DoD:** approved physical evidence exists and production responsiveness thresholds are documented.

### K — Closure, Compatibility Review, and Documentation Sync

**Goal:** close the initiative with no architectural drift between code, tests, and docs.

**Work:**

- run H35 compatibility review;
- update compatibility policy/generation only if required;
- update contracts to match final implementation;
- record final timing thresholds/results;
- run full regression and production packaging gates;
- close remaining `UNRESOLVED` audit items or explicitly defer them with tracked issues.

**DoD:** all initiative acceptance criteria pass, docs describe actual behavior, compatibility status is explicit, and no unresolved P0 responsiveness blocker remains.

## 5. Dependency graph

```text
A Runtime Audit
      |
      v
B Compatibility Baseline
      |
      v
C RunSlice Core
      |
      v
D Cooperative State/Yield
      |
      +----------+
      v          v
E Timed Ops     F Line Snapshot
      \          /
       \        /
        v      v
      G Main-Loop Integration
              |
              v
      H Instrumentation
              |
              v
      I Host CI Gates
              |
              v
      J Physical Qualification
              |
              v
      K Closure / H35 Review
```

Parallel work is allowed only where dependencies are satisfied. In particular, physical tuning must not substitute for missing deterministic host contracts.

## 6. PR strategy

Prefer small reviewable PRs aligned with the work packages rather than one large runtime rewrite.

Recommended sequence:

1. docs/contract PR (this phase);
2. A+B audit/baseline PR;
3. C RunSlice core PR;
4. D cooperative state PR;
5. E timed-operation conversions in one or more scoped PRs;
6. F line snapshot PR;
7. G main-loop integration PR;
8. H+I instrumentation/CI PRs;
9. J qualification evidence PR;
10. K closure/policy/docs PR.

No PR should mix unrelated algorithm tuning with execution-model changes.

## 7. Required PR template content for this initiative

Each implementation PR must include:

- work package (A–K);
- contract documents affected;
- current behavior;
- intended behavior;
- blocking/yield classification affected;
- PC/pending-state impact;
- `Step()` compatibility statement;
- bytecode/compiler/H35 impact statement;
- tests added/updated;
- physical evidence required or not required;
- rollback risk.

## 8. Risks to explicitly prevent

### Risk: `RunSlice` wraps blocking `Step()`

Result: apparent new API but no real responsiveness.

**Guard:** longest indivisible runtime call instrumentation + wait/timed-operation tests.

### Risk: PC advances on yield

Result: operation finishes logically too early.

**Guard:** pending-state/PC tests for every cooperative opcode.

### Risk: side effects replay on resume

Result: motor/follower initialization or output commands execute repeatedly.

**Guard:** exactly-once initialization/finalization assertions.

### Risk: sensor getters sample at different times

Result: impossible line patterns and unstable decisions.

**Guard:** shared sequence/read-count snapshot tests.

### Risk: compiler patch hides runtime issue

Result: one lesson works but execution model stays broken.

**Guard:** no line-follow-specific compiler/bytecode special case without separate architecture review.

### Risk: silent compatibility drift

Result: generation-1 compiler/firmware pair no longer means the same thing.

**Guard:** compatibility matrix + H35 review and frozen SSoT gates.

## 9. Completion criteria

The Epic is complete only when A–K are closed with evidence, the acceptance test plan passes, physical timing thresholds are recorded, full regression remains green, and the final docs match the shipped runtime behavior.
