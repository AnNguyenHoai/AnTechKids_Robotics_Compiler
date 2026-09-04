# H26-F — Compiler Safety & Resource Validation

## Purpose

H26-F adds an explicit, versioned safety boundary between compiler output and firmware/runtime delivery.

## Contract

`packages/robot-isa/resource_contract.json` defines the current runtime resource limits:

- maximum program size: 128 instructions;
- maximum variables: 32;
- maximum call stack depth: 8;
- maximum loop depth: 8;
- signed 32-bit operand range;
- jump-to-end is valid.

The contract is additive and does not change existing opcode numbers or generated program format.

## Validation boundary

`robot-compiler/compiler/safety_validator.py` validates a compiled instruction sequence for:

- unknown opcodes;
- program-size overflow;
- invalid variable indices;
- invalid jump targets;
- static linear call-stack overflow / invalid return;
- operand range violations;
- optional target capability support using the H26-E capability model.

`robot-compiler/compiler/safe_compile.py` provides an opt-in `compile_safe()` wrapper. The legacy compiler entry point remains unchanged so existing Golden Path workflows are not forced to migrate in H26-F.

## Compatibility rules

A safety violation must fail closed before runtime delivery. Consumers should surface the rule ID and source instruction where available rather than parsing free-form log strings.

Capability checking is opt-in because a target capability set may not be known during ordinary compilation. Resource and ISA validation are target-independent.

## Validation

`tests/h26_f/test_safety_validator.py` covers valid programs, opcode/resource violations, jump boundaries, call depth, capability mismatch, and contract-driven limits.

Run:

```text
python tests/h26_f/run_h26_f.py
```

PlatformIO, ESP32 hardware, and physical robot execution are not claimed unless the repository CI/hardware environment performs those checks.

## Non-goals

- no opcode renumbering;
- no binary ABI migration;
- no VM dispatch redesign;
- no mandatory change to the existing `RobotCompiler.compile()` path;
- no inference of hardware capabilities from opcode ranges.
