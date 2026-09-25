# VM-RT Closure Audit (#313)

Parent epic: #302  
Closure task: #313  
Reconciliation task: #330  
Baseline reviewed: `6264c8f253f2f05b209c83e7916dfcdaa9215882`

## Status

The deterministic VM-RT implementation through A–I is merged and protected by host/firmware CI. The physical qualification harness and campaign tooling are merged, but the initiative is **not yet eligible for final closure** because measured real-robot evidence, approved thresholds, and several explicitly tracked timing/compatibility follow-ups remain open.

This audit is fail-closed: an item is considered resolved only when code/test evidence or required physical evidence exists. Merely having a finite-looking implementation or a synthetic fixture is not enough.

## A–J evidence map

| Package | Issue | Repository evidence | Closure state |
|---|---:|---|---|
| A | #303 | VM blocking/yield audit and execution-model docs | merged/closed |
| B | #304 | compatibility baseline, Step fixtures, responsiveness compatibility matrix | merged/closed |
| C | #305 | bounded `RunSlice` core + host tests | merged/closed |
| D | #306 | generic pending operation state + deterministic cleanup | merged/closed |
| E | #307 | cooperative Wait/time-spanning operations | merged/closed |
| F | #308 | shared line-sensor snapshot contract | merged/closed |
| G | #309 | firmware main-loop `RunSlice` integration | merged/closed |
| H | #310 | timing/responsiveness telemetry | merged/closed |
| I | #311 | host CI, negative regressions and compatibility replay | merged/closed |
| J | #312 | harness/runbook exist; real robot evidence and threshold approval pending | **open** |

## Post-audit corrections completed

The later full audit found gaps not represented by the original #313 document. These are now explicit rather than hidden behind the statement that #325 was the only blocker.

| Issue | Finding | State |
|---:|---|---|
| #328 | `Pow` had exponent-sized indivisible work | completed via cooperative fixed-size chunks |
| #329 | qualification firmware profile was not compile-verified by full/release CI | completed; `esp32dev_vm_qualification` now has CI/release preflight compile |
| #331 | MP3 pending deadline helper excluded `Mp3Play` | completed; deadline ownership/completion gates added |
| #330 | stale `UNRESOLVED` rows and closure ownership drift | this reconciliation |

## Final shipped runtime contract currently proven

- Firmware services control-plane work before student-code VM work.
- Student code runs through bounded `RunSlice` scheduling; legacy `Step()` remains the compatibility primitive.
- Pending instructions retain PC ownership until logical completion and advance PC exactly once.
- Wait and MP3 duration-spanning work use cooperative deadline state.
- `Pow` yields across bounded repeated-multiply chunks instead of monopolizing one Step.
- Stop/fault/reset cleanup clears pending cooperative state deterministically.
- Line consumers share one line-sensor snapshot per VM control slice.
- VM responsiveness telemetry is available behind the diagnostic qualification profile.
- The exact qualification profile is compile-verified in VM/full/release CI before it is used for real-test evidence.

## H35 compatibility review

Result remains: **NO GENERATION CHANGE REQUIRED** for the implemented VM responsiveness scheduling changes.

Reasoning:

1. canonical opcode numbers and bytecode encoding are unchanged;
2. compiler generation remains 1 and firmware generation remains 1;
3. Robot Language API version remains 1.0.0;
4. platform-contract generation remains 1;
5. cooperative scheduling changes preserve the logical bytecode/result contract;
6. legacy generation-0 firmware remains upgrade-only through the existing explicit migration path;
7. unknown/future generations remain fail-closed.

Any future follow-up that changes source-visible sensor semantics, opcode behavior, bytecode encoding, public RobotAPI compatibility, or required protocol fields must repeat H35 review rather than inheriting this result automatically.

## Threshold / physical qualification state

Authoritative threshold file: `docs/VM_RESPONSIVENESS_THRESHOLDS.json`.

Until the physical campaign is completed it must remain:

- status: `UNAPPROVED_PENDING_PHYSICAL_EVIDENCE`;
- `approval.approved = false`;
- measured thresholds unset (`null`);
- production slice budget unchanged at 4 work units unless measured evidence justifies a reviewed change;
- no host/synthetic fixture accepted as physical evidence.

## Open closure owners after #330 reconciliation

### Core physical campaign

- **#312** — VM-RT J physical robot qualification remains open.
- **#325** — execute the six-scenario physical campaign, retain raw evidence, propose/review thresholds.

### Explicit formerly-ownerless risks

- **#336** — touch/light/color target-driver timing bounds.
- **#337** — `LineBasis`/line-control indivisible work-unit physical latency.
- **#338** — fail-closed VM boundary against public blocking RobotAPI wait/line helpers.
- **#339** — line getter/raw timing classification after shared snapshot.
- **#340** — ultrasonic finite timeout versus final responsiveness threshold.
- **#341** — synchronous diagnostics/logging overhead and production-vs-qualification configuration.
- **#342** — actuator/output work-unit outlier review from physical evidence.
- **#343** — map these hardware-dependent checks into one #325 evidence campaign rather than duplicating runs.
- **#344** — distinguish feature-gated/dummy paths from real production hardware timing evidence.

These issues do not all imply separate physical runs. #343 exists specifically so one well-identified campaign capture can support multiple child conclusions where the evidence is genuinely applicable.

## Regression and packaging closure gates

Before #313 / #302 final closure, all of the following must pass from the final evidence commit:

1. `python tests/vm_responsiveness/run_vm_rt_ci.py`
2. `python tests/h35_compatibility/run_h35_compatibility.py`
3. `python run_all_tests.py`
4. `python -m platformio run -d robot-platform -e esp32dev_vm_qualification`
5. production Windows ZIP build through `BUILD_PRODUCTION_ZIP.cmd --clean`
6. packaged offline first-flash evidence gate.

The real-robot metadata must identify the same qualification firmware commit that passed the qualification-profile compile gate.

## Closure rule

#325 is **not** the only remaining blocker. The current closure set is #312/#325 plus #336–#344, with #330 closing only the stale ownership/documentation gap itself.

#313 may close only after:

- every open P0/P1 VM-RT risk is resolved;
- physical-required issues have real evidence rather than host estimates;
- any non-P0 deferral is explicit and justified in a dedicated issue;
- thresholds/results are approved and recorded;
- final full regression, qualification firmware compile, production packaging and first-flash gates pass;
- this document is updated again to describe the actually shipped final state.

Parent #302 must remain open until #313 satisfies that rule.
