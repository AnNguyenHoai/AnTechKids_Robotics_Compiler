# EPIC H29 — Runtime Cooperative Execution Contract

## Goal

Student bytecode must never monopolize the firmware application loop. A program
may run forever or start a long-duration robot action, while the robot must
remain discoverable and responsive to the control plane.

## Runtime contract

`VM::Step()` MUST return control to the top-level Arduino loop after one bounded
unit of work. A long-running instruction MUST keep its program counter on the
same instruction, retain explicit pending state, and resume on later `Step()`
calls instead of waiting inside the call.

The top-level scheduling order remains:

1. serial/control commands;
2. `RobotNetworkService::update()` for Wi-Fi, HTTP, OTA and UDP discovery;
3. sensors and motion maintenance;
4. one bounded VM step.

No VM instruction may implement an unbounded internal loop or sleep for its full
student-visible duration.

## H29-A — Execution state

`VMContext` owns a small pending-operation contract:

- `None`: normal instruction execution;
- `Wait`: deadline-backed wait whose PC does not advance until the deadline;
- `Line`: a long-running line operation advanced one bounded control tick at a
  time.

Reset, manual stop, program termination and VM error all clear pending state and
cancel any cooperative line operation.

## H29-B — Non-blocking WAIT

The `Opcode::Wait` path no longer calls the legacy blocking
`RobotAPI::Wait(uint32_t)`. The VM records a `millis()` deadline and returns.
Every later `Step()` polls the deadline; once reached, the pending state is
cleared and the program counter advances.

This preserves sequential program semantics while allowing the main loop to
service Wi-Fi and OTA throughout long waits.

## H29-C — Cooperative line operations

The VM no longer calls the legacy blocking implementations of:

- `LineMillisecond`;
- `LineIntersectionStop`;
- `LineTurnEncounterLine`;
- `LineForBmp`.

`CooperativeLineOperation` converts those opcodes to state machines. Each update
performs at most one 20 ms line-control tick by calling the already bounded
`RobotAPI::LineBasis`, then returns to the scheduler. Completion conditions
match the existing line follower state/deadline behavior.

The old RobotAPI wrappers remain temporarily for firmware/source compatibility,
but they are outside the student VM execution path and are treated as legacy
migration surface.

## H29-D — Liveness and regression boundary

Regression tests lock the following properties:

- VM WAIT cannot call `RobotAPI::Wait`;
- long-running line opcodes cannot enter blocking RobotAPI wrappers;
- cooperative line code contains no `delay()` and no internal `while` loop;
- network update stays ahead of VM execution in the top-level scheduler;
- per-instruction VM trace defaults off so a tight forever loop cannot flood the
  serial path;
- the existing H29 compiler-hardening test namespace is preserved; runtime
  tests live under `tests/h29_runtime/` to avoid historical task collision.

## Non-goals

H29 does not change robot discovery persistence, multi-robot RoboStudio state,
or boolean `and/or` compiler semantics. Those remain separate workstreams.
