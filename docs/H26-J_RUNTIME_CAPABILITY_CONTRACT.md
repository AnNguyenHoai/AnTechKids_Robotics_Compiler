# H26-J — Runtime Capability Contract Enforcement

## Purpose

H26-J turns the existing H26-E capability model into an execution-boundary contract. A compiled `RuntimeProgram` records the canonical capability IDs required by its instruction stream. A `VirtualMachine` can then reject a program at `load()` time when the runtime does not expose all required capabilities.

## Flow

```text
binary
  ↓
ProgramLoader
  ↓
RuntimeProgram.required_capabilities
  ↓
VirtualMachine.load()
  ↓
validate against runtime_capabilities
  ↓
execute only when the contract is satisfied
```

The capability IDs and opcode ownership remain sourced from `packages/robot-isa/capability_model.json`; no opcode values are renumbered and no runtime dispatch behaviour is changed.

## Enforcement boundary

`VirtualMachine(..., runtime_capabilities=...)` enables enforcement. Missing capabilities raise `CapabilityContractError` before `ExecutionEngine.load()` and before the first instruction can execute.

Existing callers that do not provide a runtime capability set remain compatible. This is intentional for the current Golden Path while platform integrations migrate to explicit capability declarations.

## Required capabilities

`ProgramLoader` derives required capability IDs from the decoded instruction stream. For example, `Forward` requires `motion.basic`, while `SetServo` requires `actuator.servo`.

## Validation

Run:

```text
python tests/h26_j/run_h26_j.py
```

The H26-J tests cover canonical opcode-to-capability derivation, loader metadata, rejection before execution, acceptance when all capabilities are present, and backward compatibility for existing VM callers.

## Non-goals

- no opcode renumbering;
- no compiler instruction changes;
- no firmware upload;
- no physical robot claim;
- no forced capability enforcement for existing callers until they provide an explicit runtime capability set.
