# VM-RT Closure Audit (#313)

Parent epic: #302  
Closure task: #313  
Baseline reviewed: `5587f27c7e3893092e887b36ebaf030c4a91108f`

## Status

The implementation sequence A–I is merged and protected by deterministic host gates. The physical qualification harness for J is also merged. The initiative is **not yet eligible for final closure**, because repository source-of-truth still records physical timing evidence as pending.

Tracked physical-evidence completion: #325.

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
| J | #312 | physical qualification harness/runbook merged; measured robot evidence and approved thresholds still pending | **deferred to #325** |

## Final shipped runtime contract

- Firmware services control plane work before student-code VM work.
- Student code runs through bounded `RunSlice` scheduling; legacy `Step()` behavior remains a compatibility boundary.
- Pending instructions retain PC ownership until logical completion and advance PC exactly once.
- Wait/time-spanning work is cooperative rather than duration-blocking on the VM path.
- Stop/fault/reset cleanup cancels pending cooperative state deterministically.
- Line consumers share one line-sensor snapshot per VM control slice.
- VM responsiveness telemetry is available behind the diagnostic build profile.

## H35 compatibility review

Result: **NO GENERATION CHANGE REQUIRED** for the VM responsiveness initiative.

Reasoning:

1. canonical opcode numbers and bytecode encoding are unchanged;
2. compiler generation remains 1 and firmware generation remains 1;
3. Robot Language API version remains 1.0.0;
4. platform-contract generation remains 1;
5. VM responsiveness changes are runtime scheduling/internal execution changes that preserve logical bytecode behavior;
6. legacy generation-0 firmware remains upgrade-only through the existing explicit migration path;
7. unknown/future generations remain fail-closed.

Therefore `packages/robot-isa/compatibility_policy.json` must remain generation 1 unless a separately reviewed contract change requires a bump.

## Threshold / physical qualification state

Authoritative threshold file: `docs/VM_RESPONSIVENESS_THRESHOLDS.json`.

Until #325 is completed it must remain:

- status: `UNAPPROVED_PENDING_PHYSICAL_EVIDENCE`;
- `approval.approved = false`;
- measured thresholds unset (`null`);
- production slice budget unchanged at 4 work units;
- no host/synthetic fixture accepted as physical evidence.

This is a deliberate closure blocker, not a test failure.

## Regression and packaging closure gates

Before #313 / #302 final closure, all of the following must pass from the final evidence commit:

1. `python tests/vm_responsiveness/run_vm_rt_ci.py`
2. `python tests/h35_compatibility/run_h35_compatibility.py`
3. `python run_all_tests.py`
4. production Windows ZIP build through `BUILD_PRODUCTION_ZIP.cmd --clean`
5. packaged offline first-flash evidence gate.

## Open closure blocker

#325 is the only explicitly tracked remaining VM-RT closure blocker identified by this audit. It requires real-robot execution, evidence retention, threshold approval, and a final full regression/packaging run.

Parent #302 and #313 must remain open until #325 is complete and the threshold document is approved from measured physical evidence.
