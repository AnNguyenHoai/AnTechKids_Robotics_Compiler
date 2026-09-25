# VM Runtime Blocking-Point Audit

Tracking: #303, parent #302
Baseline: `main@71662c84d90c6dbbe682925d9c509309505588d7`

## Purpose

Inventory VM-reachable work before `RunSlice` implementation. This document records current scheduling behavior and is updated as follow-up responsiveness work resolves or reclassifies audit findings.

Classification:

- `IMMEDIATE`: synchronous work expected to complete in one short VM step with no intentional wait loop.
- `COOPERATIVE`: logical operation spans multiple `Step()` calls and keeps PC on the current instruction until completion.
- `BOUNDED_IO`: synchronous hardware I/O that may block, but has a known finite bound/timeout.
- `UNRESOLVED`: duration is data-dependent/unbounded, contains an intentional delay that is not cooperative, or requires measurement/contract work before it can be treated as bounded.

## VM execution observations

- `VM::Step()` executes one current instruction/tick.
- `Wait` stores `mPendingDeadlineMs`, returns without advancing PC, and advances PC only after the deadline.
- Line operations `LineIntersectionStop`, `LineMillisecond`, `LineTurnEncounterLine`, and `LineForBmp` route through `CooperativeLineOperation` and use `VMPendingOperation::Line`.
- `CooperativeLineOperation` runs a line-control tick no more often than every 20 ms and completion is observed on later `Step()` calls.
- `Pow` is cooperative as of #328: repeated multiplication order is preserved, with at most 8 multiplications per `Step()` and pending progress held in `VMContext`.
- `Reset`, `Start`, `SetRunning(false)`, VM error handling, and stop paths cancel generic pending state.
- Direct blocking RobotAPI versions of wait/line operations still exist for non-VM compatibility and must not be reintroduced into VM dispatch.

## VM-reachable classification matrix

| Opcode / group | Runtime path | Current class | PC / side effect behavior | Evidence / follow-up |
|---|---|---|---|---|
| `LoadConst`, comparisons, `Add/Sub/Mul/Div/Mod/Neg/Store`, jumps/call/return | VM local state | `IMMEDIATE` | PC advances/branches synchronously; arithmetic faults stop VM | Protected by host regression |
| `Pow` | VM pending state → bounded repeated-multiply chunks | `COOPERATIVE` | PC held while exponent work remains; at most 8 multiplies per Step; PC++ once on completion | #328 + `run_pow_bounded_contract.py` |
| `Forward`, `Backward`, `TurnLeft`, `TurnRight`, `Stop`, `SetMotorSpeed` | VM → RobotAPI → motor/heading path | `IMMEDIATE`* | Command applied then PC++ | `*` physical duration remains part of qualification evidence |
| `Wait` | VM pending deadline | `COOPERATIVE` | PC held while pending; PC++ once deadline reached | VM-RT pending-state gates |
| `ReadUltrasonic` | VM → RobotAPI → `Ultrasonic::update()` → `pulseIn(timeout)` | `BOUNDED_IO` | value stored then PC++ | Configured timeout remains a physical latency candidate |
| `ReadTouch`, `ReadLight`, `ReadColor` | VM → RobotAPI/device read | `UNRESOLVED` | value stored then PC++ | Driver timing evidence owned by #330 / physical qualification |
| `ReadLine`, `GetTraceValue`, `GetTraceState`, `GetTraceRaw` | VM → shared line snapshot | `COOPERATIVE/BOUNDED SNAPSHOT` | same-slice consumers reuse one L/C/R snapshot; PC++ per getter | #308 snapshot contract; timing evidence still reviewed by #330/#312 |
| `LineBasis`, `LineFollow` | VM → RobotAPI line sensor/control/output tick | `UNRESOLVED` | one synchronous tick then PC++ | Worst-case physical duration owned by #330/#312 |
| `LineMillisecond` | VM → `CooperativeLineOperation` → repeated `LineBasis` ticks | `COOPERATIVE` | PC held; completion stops follower/motors; PC++ once | Host + physical qualification |
| `LineIntersectionStop` | VM → `CooperativeLineOperation` → repeated `LineBasis` ticks | `COOPERATIVE` | PC held until follower stopped; PC++ once | Host + physical qualification |
| `LineTurnEncounterLine` | VM → `CooperativeLineOperation` → repeated `LineBasis` ticks | `COOPERATIVE` | PC held until turn request clears; PC++ once | Host + physical qualification |
| `LineForBmp` | VM → `CooperativeLineOperation` → repeated `LineBasis` ticks | `COOPERATIVE` | PC held until BMP inactive; final stop then PC++ | Host + physical qualification |
| `LineStop` | VM → cancel cooperative line → RobotAPI stop | `IMMEDIATE`* | cancels active line work, stops, PC++ | stop latency measured by #312/#325 |
| `SetServo` | RobotAPI | `IMMEDIATE` currently | PC++ | Current implementation is feature-gated/dummy |
| `Set3CLed` | RobotAPI → GPIO | `IMMEDIATE` | GPIO write + log then PC++ | synchronous logging may affect measured duration |
| `SetLightSensorLed` | RobotAPI | `IMMEDIATE` currently | PC++ | Current implementation is dummy |
| `SetMotorStraightAngle` | RobotAPI | `IMMEDIATE` currently | PC++ | Current implementation is dummy; future real implementation must be reclassified |
| `SetMp3Play` | VM pending deadline → cooperative buzzer begin/end | `COOPERATIVE` with open liveness bug | PC should remain pending until deadline then finalize + PC++ | Deadline helper bug tracked by #331 |

## Blocking points outside the active VM path

The following RobotAPI functions are still blocking and must not be accidentally reintroduced into VM dispatch:

- `RobotAPI::Wait(ms)` uses `delay(ms)`.
- `RobotAPI::LineMillisecond` uses a duration loop plus `delay(20)`.
- `RobotAPI::LineIntersectionStop` loops until follower stop plus `delay(20)`.
- `RobotAPI::LineTurnEncounterLine` loops until line reacquisition plus `delay(20)`.
- `RobotAPI::LineForBmp` loops while BMP is active plus `delay(20)`.

These APIs may still be reachable by non-VM callers. VM responsiveness work keeps the distinction between VM dispatch semantics and public RobotAPI compatibility explicit; #330 owns the final reachability/compatibility decision.

## P0 / high-risk findings

1. **`Pow` exponent-sized indivisible work** — resolved by #328 using cooperative chunks with a fixed 8-multiply per-Step budget.
2. **`SetMp3Play` deadline completion** — cooperative conversion exists, but current deadline helper excludes `Mp3Play`; tracked by #331.
3. **Ultrasonic read can occupy one VM step up to its configured timeout**; this is finite but must remain in physical responsiveness evidence.
4. **`LineBasis` is an indivisible control tick** for cooperative line operations. Its real worst-case duration must be measured before a hard slice-time claim is approved.
5. **Touch/light/color read timing** still requires driver/physical evidence.
6. **Synchronous diagnostics/logging** can affect timing and must be represented by the qualification profile used for thresholds.

## PC / cancellation baseline

- Immediate instructions: side effect/value computation then PC advances once.
- `Wait`: INIT stores deadline without PC advance; pending calls leave PC unchanged; completion clears pending and advances once.
- `Pow`: INIT captures base/exponent/result; each Step performs at most 8 legacy-order multiplications; PC remains unchanged while work remains; completion clears pending and advances once.
- Cooperative line operations: start sets pending without PC advance; each update leaves PC unchanged while active; completion clears pending and advances once.
- `Reset`, `Start`, `SetRunning(false)` and VM fault cleanup clear generic pending state; actuator-specific cleanup remains centralized.

## Remaining `UNRESOLVED` items and owner

| Item | Why unresolved | Planned owner |
|---|---|---|
| touch/light/color reads | Driver timing not yet measured/bounded | #330 / #312 |
| `LineBasis` worst-case duration | Needs physical instrumentation evidence | #330 / #312 / #325 |
| `SetMp3Play` completion | Pending deadline helper currently accepts Wait only | #331 |
| public blocking RobotAPI line/wait functions | Non-VM compatibility/reachability needs explicit final decision | #330 |
| qualification firmware build verification | Real-test profile was not compiled by existing full host run | #329 |

## #303 Definition of Done assessment

- [x] VM dispatch cases inventoried for the original baseline.
- [x] VM → RobotAPI/service paths classified at audit level.
- [x] Known delay/busy/duration/polling loops identified.
- [x] Current PC and cooperative side-effect behavior recorded.
- [x] Unresolved entries have explicit reason and follow-up issue.
- [x] Original #303 changed no runtime behavior.

Follow-up issues now own post-audit runtime corrections and physical evidence. #303 remains correctly closed; #302 remains open until those follow-ups are complete.
