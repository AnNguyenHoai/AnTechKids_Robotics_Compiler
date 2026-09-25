# VM-RT I — Host CI and Regression Gates

Tracking: #311  
Parent: #302  
Depends on: #310 / PR #322

## Purpose

VM responsiveness contracts are fail-closed in host CI. A green result means the
scheduler/pending/snapshot compatibility contracts pass **and** representative
regressions are proven to be rejected by negative mutation tests.

## Dedicated runner

```text
python tests/vm_responsiveness/run_vm_rt_ci.py
```

The runner owns the VM responsiveness family:

1. `run_vm_responsiveness_baseline.py` — legacy `Step()` and production-loop compatibility.
2. `run_run_slice_core.py` — bounded slices, cooperative pending operations, line snapshot and timing instrumentation.
3. `vm_rt_contract_guard.py` — reusable fail-closed source contract validator.
4. `run_vm_rt_negative.py` — deliberate regression mutations that must be rejected.
5. `run_compatibility_replay.py` — frozen opcode and compiler-output replay.

## Cross-domain required gates

When VM-impacting paths change, CI also independently runs:

- `robot-compiler/tests/run_tests.py`;
- `tests/line_follow_stability/run_line_follow_stability.py`;
- `tests/h35_compatibility/run_h35_compatibility.py`;
- ESP32 PlatformIO compile.

These remain separate from `run_vm_rt_ci.py` so ownership is explicit and local
VM testing does not silently replace broader compiler/line/H35 contracts.

## Negative regressions

`run_vm_rt_negative.py` mutates an in-memory copy of production source and
requires the contract guard to reject each case:

| Regression | Required rejection |
|---|---|
| slice loop `<` becomes `<=` | budget violation |
| extra PC advance in pending `Wait` | double-advance / pending PC contract |
| cooperative `Wait` calls blocking `RobotAPI::Wait` | blocking regression |
| same-cycle snapshot reuse guard is disabled | duplicate physical-read risk |
| legacy `Step()` dispatches instruction twice | `Step()` compatibility regression |
| firmware opcode number changes | bytecode compatibility drift |

The negative tests never write the mutated source back to the repository.

## Compatibility replay

`fixtures/compatibility_replay_v1.json` freezes compatibility generation 1:

- all 60 canonical opcode name/number pairs;
- representative compiled instruction streams (`demo_forward.py`, `demo_variable.py`).

The replay gate requires exact agreement among:

1. the frozen fixture;
2. `packages/robot-isa/canonical_isa.json`;
3. compiler generated `Opcode` values;
4. firmware generated `opcode.h`;
5. actual compiler output for the frozen programs.

This catches coordinated drift where canonical ISA and generated files are all
changed together but compatibility generation/evidence was not intentionally
advanced through the H35 policy.

## CI topology

`tests/vm_responsiveness/` is a VM-impact path in `tools/ci_impact.py`. Therefore
this work selects the narrow VM gate family rather than silently falling through
to an unrelated scope. `run_all_tests.py` also invokes the dedicated runner, so
full/release regression includes the same fail-closed VM evidence.

## Issue #311 acceptance mapping

- Slice/budget violation: positive RunSlice tests + negative off-by-one mutation.
- Pending PC/double advance: pending-state assertions + injected extra increment.
- Blocking regression: cooperative Wait/MP3 checks + injected blocking Wait call.
- Snapshot inconsistency/duplicate reads: S1–S5 checks + disabled reuse guard mutation.
- Legacy `Step()` incompatibility: baseline/core checks + double-dispatch mutation.
- Compiler/bytecode compatibility drift: compiler gate + frozen fixture replay + H35 gate.

No production VM execution semantics are changed by this work package.
