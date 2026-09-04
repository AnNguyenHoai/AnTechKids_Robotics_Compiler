# H26-C — Canonical ISA & Opcode Boundary

## Goal

Establish one authoritative semantic vocabulary for instructions without replacing the production compiler, changing VM dispatch, or migrating the firmware wire format.

## Source of truth

`packages/robot-isa/canonical_isa.json` is the single semantic source of truth.

Each row binds a stable semantic ID to the currently produced opcode name and numeric wire value:

```text
canonical semantic ID
        |
        +--> current producer name
        |
        +--> current wire numeric code
```

The numeric code is a compatibility binding. It is not the semantic identity.

## Current production boundary

The existing `robot-compiler/compiler/generated/opcode.py` remains unchanged and remains the producer of current program opcodes. H26-C only reads that contract.

The current production generated program and firmware upload path remain untouched. This preserves the H26-A/H26-B Golden Path.

## Adapters

### Python

`robot-compiler/compiler/canonical_opcode_adapter.py` provides lookup from producer name or current wire code to canonical semantic ID. It is intended for diagnostics, capability analysis, tests, and future migration work.

### C++ / ESP32

`packages/robot-isa/include/CanonicalOpcodeAdapter.h` provides a header-only translation from current wire code to a canonical enum. It is deliberately not included by the current VM dispatch, so runtime behavior cannot change as a side effect of H26-C.

Regenerate the header from the canonical manifest with:

```bash
python tools/generate_canonical_opcode_adapter.py
```

The generated file is an adapter artifact, not a second semantic source.

## Legacy isolation

The older `packages/robot-common/include/Opcode.h` model contains names such as `MOVE_RUN`, `THREAD_START`, and `JUMP_IF`. Those names are captured only as explicit `legacy_aliases` in the canonical manifest.

A legacy name is never silently assumed equivalent to a current producer opcode. When equivalence is not proven, the alias has a null canonical target.

This is intentional: H26-C establishes a boundary first; semantic reconciliation happens only when evidence exists.

## Equivalence contract

For every current producer opcode:

1. the producer name appears exactly once in the canonical manifest;
2. the numeric value appears exactly once;
3. the canonical semantic ID is unique and independent of the numeric value;
4. the Python adapter resolves the same semantic ID from the producer name and wire value;
5. the C++ adapter maps the same wire value to the corresponding canonical enum.

The tests treat the current generated opcode file as the compatibility oracle. This means H26-C cannot accidentally renumber or rename the production opcode contract.

## Scope / non-goals

H26-C does not:

- modify `robot-compiler/compiler/generated/opcode.py`;
- modify compiler instruction emission;
- modify `generated_program.h`;
- modify ESP32 VM dispatch;
- modify RobotAPI semantics;
- migrate `.rbot` or another binary file format;
- delete or rewrite `packages/robot-common` legacy definitions;
- claim physical robot equivalence without a hardware run.

## Acceptance result

The canonical vocabulary now covers all current production opcodes, while the legacy opcode vocabulary is explicitly isolated. The production wire contract remains the same numeric mapping and the new adapters are side-band migration infrastructure only.
