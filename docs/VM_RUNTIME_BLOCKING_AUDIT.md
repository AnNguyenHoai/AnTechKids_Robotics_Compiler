# VM Runtime Blocking-Point Audit

Tracking: #303, reconciliation #330, parent #302  
Original audit baseline: `main@71662c84d90c6dbbe682925d9c509309505588d7`  
Reconciliation baseline: `main@6264c8f253f2f05b209c83e7916dfcdaa9215882`

## Purpose

Inventory VM-reachable work and keep every unresolved responsiveness risk attached to explicit evidence or an open owner. This document does not promote a timing classification from host assumptions: physical timing remains unresolved until measured on the target profile/hardware.

Classification:

- `IMMEDIATE`: synchronous work expected to complete in one short VM step with no intentional wait loop.
- `COOPERATIVE`: logical operation spans multiple `Step()` calls and keeps PC on the current instruction until completion.
- `BOUNDED_IO`: synchronous hardware I/O with a finite code/configuration bound; final acceptability may still require physical evidence.
- `UNRESOLVED`: duration or production acceptability still requires code-path, compatibility, or physical measurement evidence.

## Current VM execution observations

- `VM::Step()` remains the single-dispatch compatibility primitive.
- Production scheduling uses bounded `RunSlice` work.
- `Wait` is deadline/pending based and no longer duration-blocking on the VM path.
- `SetMp3Play` deadline completion was fixed and protected by #331.
- `Pow` is cooperative as of #328, preserving repeated-multiply order with at most 8 multiplications per `Step()`.
- Line time-spanning operations route through `CooperativeLineOperation` rather than public blocking RobotAPI line helpers.
- Line consumers use the shared snapshot contract introduced by #308.
- The exact physical qualification profile is compiled by CI/release preflight as of #329.
- Direct public blocking RobotAPI wait/line helpers remain available for non-VM compatibility; their VM-boundary hardening is tracked by #338.

## VM-reachable classification matrix

| Opcode / group | Runtime path | Current class | Evidence / remaining owner |
|---|---|---|---|
| `LoadConst`, comparisons, `Add/Sub/Mul/Div/Mod/Neg/Store`, jumps/call/return | VM local state | `IMMEDIATE` | Host regression |
| `Pow` | VM pending state → bounded repeated-multiply chunks | `COOPERATIVE` | #328 completed; `run_pow_bounded_contract.py` |
| `Wait` | VM pending deadline | `COOPERATIVE` | Pending-state/deadline gates |
| `SetMp3Play` | VM pending deadline → cooperative buzzer begin/end | `COOPERATIVE` | #331 completed; deadline ownership/completion gates |
| `Forward`, `Backward`, `TurnLeft`, `TurnRight`, `Stop`, `SetMotorSpeed` | VM → RobotAPI → output/control path | `IMMEDIATE`* | `*` final physical outlier review: #342 / #325 |
| `ReadUltrasonic` | VM → RobotAPI → ultrasonic pulse acquisition | `BOUNDED_IO` | Finite timeout by code/config; physical timeout acceptability: #340 / #325 |
| `ReadTouch`, `ReadLight`, `ReadColor` | VM → RobotAPI/device read | `UNRESOLVED` | Driver/target timing evidence: #336 |
| `ReadLine`, `GetTraceValue`, `GetTraceState`, `GetTraceRaw` | VM → shared line snapshot | `SNAPSHOT-CONSISTENT; TIMING PENDING` | Snapshot ownership resolved by #308; residual call/sampling timing reconciliation: #339 / #337 |
| `LineBasis`, `LineFollow` | VM → line snapshot/control/output tick | `UNRESOLVED` | Physical indivisible work-unit evidence: #337 / #325 |
| `LineMillisecond`, `LineIntersectionStop`, `LineTurnEncounterLine`, `LineForBmp` | VM → cooperative line operation → repeated bounded scheduling points | `COOPERATIVE` | Host semantics protected; underlying LineBasis timing: #337 |
| `LineStop` | cancel line operation → output stop | `IMMEDIATE`* | stop/abort physical latency: #312 / #325 |
| `SetServo`, `SetLightSensorLed`, `SetMotorStraightAngle` | RobotAPI feature-gated/stub-dependent paths | `IMPLEMENTATION-SPECIFIC` | Prevent stub evidence being treated as real hardware timing: #344 |
| `Set3CLed` and other synchronous output/log paths | RobotAPI/GPIO/diagnostics | `IMMEDIATE`* | diagnostics configuration/outlier review: #341 / #342 |

## Blocking public RobotAPI compatibility boundary

The following public RobotAPI functions remain intentionally outside the cooperative VM scheduling contract and may remain for non-VM compatibility:

- `RobotAPI::Wait(ms)`;
- `RobotAPI::LineMillisecond`;
- `RobotAPI::LineIntersectionStop`;
- `RobotAPI::LineTurnEncounterLine`;
- `RobotAPI::LineForBmp`.

Current VM dispatch uses pending/cooperative paths instead. #338 owns the explicit fail-closed source guard preventing future VM dispatch from directly reintroducing these public blocking helpers. Public API semantics must not be removed or changed as part of that guard without a separate compatibility review.

## Resolved audit findings

| Finding | Resolution |
|---|---|
| exponent-sized `Pow` work in one Step | #328: cooperative chunks, fixed 8-multiply Step budget |
| `SetMp3Play` could remain pending forever | #331: shared deadline helper supports MP3 with live/current-PC ownership |
| qualification firmware could escape CI compile | #329: `esp32dev_vm_qualification` is compiled for VM/full/release paths |
| duplicate line reads / inconsistent same-cycle samples | #308: one shared line snapshot per VM control slice |

## Remaining evidence / compatibility owners

No remaining risk is intentionally ownerless.

| Item | Why still open | Owner |
|---|---|---:|
| touch/light/color read timing | target-driver bound not yet established | #336 |
| `LineBasis`/`LineFollow` indivisible duration | requires real robot timing/outlier evidence | #337 |
| public blocking RobotAPI wait/line reachability | needs explicit fail-closed VM boundary guard | #338 |
| line getter/raw residual timing after shared snapshot | call topology/timing reconciliation | #339 |
| ultrasonic finite timeout acceptability | finite does not imply acceptable responsiveness | #340 |
| synchronous diagnostics/logging cost | production vs qualification configuration must be explicit | #341 |
| motor/actuator/output work-unit outliers | must be reviewed in physical campaign | #342 |
| combined physical-evidence mapping | avoid fragmented/duplicated real-robot evidence | #343 |
| feature-gated/stub hardware paths | dummy implementation is not hardware timing evidence | #344 |
| production thresholds and end-to-end physical response | six-scenario real-robot campaign | #312 / #325 |

## Physical evidence rule

Host fixtures, source inspection, synthetic telemetry and CI duration cannot close rows that explicitly require physical timing. #325 remains the campaign authority. The exact qualification firmware SHA must have passed the `esp32dev_vm_qualification` CI compile and the same SHA must be recorded in evidence metadata.

## #330 reconciliation result

- [x] Every stale `UNRESOLVED` item has been re-audited at ownership level.
- [x] Resolved items reference code/test evidence (#308, #328, #329, #331).
- [x] Hardware-dependent items have dedicated open owners (#336–#344).
- [x] No physical threshold or timing result has been fabricated from host evidence.
- [x] Public blocking RobotAPI compatibility is explicitly outside the cooperative VM path; hardening remains tracked by #338.
- [x] Final closure remains blocked until the open evidence/guard owners are resolved or explicitly deferred by #313.

#303 remains correctly closed. #330 may close after this reconciliation is merged and its regression/doc gates pass; closing #330 does **not** close the child evidence issues or parent #302.
