# VM Runtime Blocking-Point Audit

Tracking: #303, parent #302
Baseline: `main@71662c84d90c6dbbe682925d9c509309505588d7`

## Purpose

Inventory VM-reachable work before `RunSlice` implementation. This document records current scheduling behavior; it does not change runtime semantics.

Classification:

- `IMMEDIATE`: synchronous work expected to complete in one short VM step with no intentional wait loop.
- `COOPERATIVE`: logical operation spans multiple `Step()` calls and keeps PC on the current instruction until completion.
- `BOUNDED_IO`: synchronous hardware I/O that may block, but has a known finite bound/timeout.
- `UNRESOLVED`: duration is data-dependent/unbounded, contains an intentional delay that is not cooperative, or requires measurement/contract work before it can be treated as bounded.

## VM execution observations

- `VM::Step()` executes one current instruction/tick.
- `Wait` already stores `mPendingDeadlineMs`, returns without advancing PC, and advances PC only after the deadline.
- Line operations `LineIntersectionStop`, `LineMillisecond`, `LineTurnEncounterLine`, and `LineForBmp` already route through `CooperativeLineOperation` and use `VMPendingOperation::Line`.
- `CooperativeLineOperation` runs a line-control tick no more often than every 20 ms and completion is observed on later `Step()` calls.
- `Reset`, `Start`, `SetRunning(false)`, VM error handling, and `Stop`/line-stop paths cancel cooperative line state.
- Direct blocking RobotAPI versions of the line operations still exist, but current VM dispatch for the four operations above does not call those blocking functions.

## VM-reachable classification matrix

| Opcode / group | Runtime path | Current class | PC / side effect behavior | Evidence / follow-up |
|---|---|---|---|---|
| `LoadConst`, comparisons, `Add/Sub/Mul/Div/Mod/Neg/Store`, jumps/call/return | VM local state | `IMMEDIATE` | PC advances/branches synchronously; arithmetic faults stop VM | Preserve in #305 |
| `Pow` | VM local loop | `UNRESOLVED` | PC advances after exponent-sized loop | Work grows with runtime exponent; bound or slice policy required |
| `Forward`, `Backward`, `TurnLeft`, `TurnRight`, `Stop`, `SetMotorSpeed` | VM → RobotAPI → motor/heading path | `IMMEDIATE`* | Command applied then PC++ | `*` Contains diagnostics/controller work; instrument longest call in #310 |
| `Wait` | VM pending deadline | `COOPERATIVE` | PC held while pending; PC++ once deadline reached | Existing pattern should become generic pending-state baseline |
| `ReadUltrasonic` | VM → RobotAPI → `Ultrasonic::update()` → `pulseIn(timeout)` | `BOUNDED_IO` | value stored then PC++ | Configured sensor timeout is 50,000 us in current initialization; this is a major indivisible latency candidate |
| `ReadTouch`, `ReadLight`, `ReadColor` | VM → RobotAPI/device read | `UNRESOLVED` | value stored then PC++ | Need driver-level timing verification; logging is synchronous |
| `ReadLine` | VM → RobotAPI → one TCRT5000 update | `UNRESOLVED` | value stored then PC++ | Also violates future shared-snapshot ownership until #308 |
| `GetTraceValue`, `GetTraceState` | VM → RobotAPI → one TCRT5000 update | `UNRESOLVED` | value stored then PC++ | Same snapshot/timing concern as `ReadLine` |
| `GetTraceRaw` | VM → RobotAPI → three TCRT5000 updates | `UNRESOLVED` | mask stored then PC++ | Three sequential reads; #308 must establish one coherent snapshot |
| `LineBasis`, `LineFollow` | VM → RobotAPI line sensor/control/output tick | `UNRESOLVED` | one synchronous tick then PC++ | Intended bounded tick, but sensor/output duration must be measured before classifying `BOUNDED_IO` |
| `LineMillisecond` | VM → `CooperativeLineOperation` → repeated `LineBasis` ticks | `COOPERATIVE` | PC held; completion stops follower/motors; PC++ once | 20 ms tick scheduling already exists |
| `LineIntersectionStop` | VM → `CooperativeLineOperation` → repeated `LineBasis` ticks | `COOPERATIVE` | PC held until follower stopped; PC++ once | Completion is follower-state driven |
| `LineTurnEncounterLine` | VM → `CooperativeLineOperation` → repeated `LineBasis` ticks | `COOPERATIVE` | PC held until turn request clears; PC++ once | Completion uses follower state from same tick rather than second sensor read |
| `LineForBmp` | VM → `CooperativeLineOperation` → repeated `LineBasis` ticks | `COOPERATIVE` | PC held until BMP inactive; final stop then PC++ | Existing cooperative path |
| `LineStop` | VM → cancel cooperative line → RobotAPI stop | `IMMEDIATE`* | cancels active line work, stops, PC++ | Verify stop latency in #310/#312 |
| `SetServo` | RobotAPI | `IMMEDIATE` currently | PC++ | Current implementation is dummy/feature-gated |
| `Set3CLed` | RobotAPI → GPIO | `IMMEDIATE` | GPIO write + log then PC++ | Synchronous logging may affect measured duration |
| `SetLightSensorLed` | RobotAPI | `IMMEDIATE` currently | PC++ | Current implementation is dummy |
| `SetMotorStraightAngle` | RobotAPI | `IMMEDIATE` currently | PC++ | Current implementation is dummy; future real implementation must be reclassified |
| `SetMp3Play` | RobotAPI → buzzer + `delay(200)` | `UNRESOLVED` / blocking | VM cannot return during 200 ms beep; PC++ afterward | P0 conversion candidate for #307 when buzzer feature is enabled |

## Blocking points outside the active VM path

The following RobotAPI functions are still blocking and must not be accidentally reintroduced into VM dispatch:

- `RobotAPI::Wait(ms)` uses `delay(ms)`.
- `RobotAPI::LineMillisecond` uses a duration loop plus `delay(20)`.
- `RobotAPI::LineIntersectionStop` loops until follower stop plus `delay(20)`.
- `RobotAPI::LineTurnEncounterLine` loops until line reacquisition plus `delay(20)`.
- `RobotAPI::LineForBmp` loops while BMP is active plus `delay(20)`.

These APIs may still be reachable by non-VM callers. VM responsiveness work must keep the distinction between VM dispatch semantics and public RobotAPI compatibility explicit.

## P0 / high-risk findings

1. **`SetMp3Play` blocks the VM for 200 ms** when buzzer support is enabled.
2. **Ultrasonic read can occupy one VM step for up to the pulse timeout (~50 ms configured)**; this is finite but too large to ignore in a responsiveness budget.
3. **`Pow` has runtime-data-dependent work** and currently has no explicit exponent/work bound.
4. **Line getters sample hardware independently**. `GetTraceRaw` performs three sequential sensor updates, while individual getters update their sensor again. This is the snapshot-consistency problem assigned to #308.
5. **`LineBasis` is the indivisible control tick** for cooperative line operations. Its real worst-case duration must be measured before a hard slice-time claim is made.
6. **Synchronous Serial diagnostics are present in sensor/motion paths** and can materially affect timing; #310 must measure with a defined diagnostics configuration.

## PC / cancellation baseline

- Immediate instructions: side effect/value computation then PC advances once.
- `Wait`: INIT stores deadline without PC advance; pending calls leave PC unchanged; completion clears pending and advances once.
- Cooperative line operations: start sets pending without PC advance; each update leaves PC unchanged while active; completion clears pending and advances once.
- `Reset`, `Start`, `SetRunning(false)` and VM fault cleanup cancel cooperative line state and clear pending state.

This is the compatibility baseline that #304 must freeze in fixtures/tests before #305–#307 alter scheduling infrastructure.

## Remaining `UNRESOLVED` items and owner

| Item | Why unresolved | Planned owner |
|---|---|---|
| `Pow` | Runtime-dependent loop length | #305/#310 |
| touch/light/color reads | Driver timing not yet measured | #310 |
| line getter/raw timing | Needs snapshot ownership + timing | #308/#310 |
| `LineBasis` worst-case duration | Needs instrumentation | #310 |
| buzzer `SetMp3Play` | Intentional 200 ms delay | #307 |
| public blocking RobotAPI line/wait functions | Non-VM compatibility/reachability needs explicit decision | #304/#313 |

## #303 Definition of Done assessment

- [x] VM dispatch cases inventoried for current `VM.cpp`.
- [x] VM → RobotAPI/service paths classified at audit level.
- [x] Known delay/busy/duration/polling loops identified.
- [x] Current PC and cooperative side-effect behavior recorded.
- [x] Unresolved entries have explicit reason and follow-up issue.
- [x] No runtime behavior changed.

After review/merge of this audit, #303 can close and #304 compatibility fixtures can be finalized.