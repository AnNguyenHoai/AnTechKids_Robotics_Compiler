# H26-E — Capability Model Completion

## Purpose

H26-E establishes one versioned capability vocabulary for compiler/tooling consumers and the robot platform. A capability is a semantic feature; opcode membership is its compatibility boundary.

## Source of truth

`packages/robot-isa/capability_model.json` is authoritative. The C++ header is a checked-in runtime adapter generated from the same semantic table, and the Python module is the tooling adapter.

## Rules

1. Capability IDs are stable semantic identifiers and must not encode hardware model names.
2. A capability may cover multiple opcodes; an opcode may belong to multiple capabilities when semantics overlap.
3. `required=true` means the platform baseline cannot operate without the capability. Optional capabilities may be absent on a target.
4. Capability discovery must not change opcode numbering or successful VM behavior.
5. Consumers should gate feature availability using capability IDs, not free-form strings or guessed opcode ranges.
6. Adding a capability is additive. Removing or changing an existing capability requires a contract migration and compatibility review.

## Current capabilities

The baseline defines 16 capabilities covering basic motion, runtime control, sensors, actuators, line following, peripherals and GUI helpers. `motion.basic` and `runtime.control` are required; the remaining capabilities are optional.

## Platform integration boundary

H26-E deliberately does not alter VM dispatch or compiler emission. `CapabilityModel.h` provides a small, allocation-free descriptor table suitable for ESP32 firmware and exposes `supports()` for opcode-level compatibility checks. Higher-level hardware detection may map platform features to these stable IDs in a later task.

## Validation

`tests/h26_e/test_capability_model.py` validates manifest uniqueness, opcode coverage against the canonical ISA, required-capability invariants, Python adapter parity, and C++ adapter parity.
