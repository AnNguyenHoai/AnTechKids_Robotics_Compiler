# H26-I — Architecture Migration & Legacy Retirement Gate

## Purpose

H26-I makes the new architecture boundary enforceable without deleting or rewriting
legacy code prematurely. The canonical ISA remains the semantic source of truth;
the current compiler/firmware Golden Path remains the production path.

The task therefore performs **migration of ownership and enforcement**, not a risky
big-bang deletion.

## Production boundary

```text
RoboSim
  -> tools/rewrite.py
  -> tools/compile.py
  -> robot-compiler/compiler
  -> packages/robot-isa/canonical_isa.json
  -> build/<program>/program.h
  -> tools/firmware_build.py
  -> robot-platform/main/src/generated_program.h
  -> PlatformIO / ESP32
```

H26-I records these boundaries in:

```text
packages/robot-isa/architecture_manifest.json
```

That manifest is the migration inventory for later work. It identifies the
canonical paths, production scan roots, and legacy components that must not leak
back into the production path.

## Legacy policy

The repository still contains older architecture material, including the
`packages/robot-common/include/Opcode.h` vocabulary and the older C++ compiler
implementation files.

They are now explicitly classified as:

```text
legacy-isolated
blocked-until-equivalence
```

The H26-I gate rejects production source that references the registered legacy
components. It evaluates dependency-shaped references rather than raw filename
substrings, and it excludes the legacy component's own source file from its scan.
This prevents a new production dependency from silently recreating the
architecture split without producing false positives from the legacy island itself.

## Retirement is evidence-gated

H26-I intentionally keeps deletion disabled:

```json
"allow_delete": false
```

The following evidence is required before any registered legacy component can be
removed in a later task:

1. canonical semantic equivalence;
2. unified H26-G E2E oracle pass;
3. H26-H firmware build pass;
4. physical validation gate.

A software-only PASS is therefore never treated as physical robot equivalence.

## Tooling

Run the gate directly:

```text
python tools/architecture_migration_gate.py
```

Optional machine-readable report:

```text
python tools/architecture_migration_gate.py --report build/h26_i_report.json
```

Standalone contract suite:

```text
python tests/h26_i/run_h26_i.py
```

The root `run_all_tests.py` includes the H26-I runner so the migration gate is part
of the repository regression chain.

## What H26-I changes

- establishes an explicit architecture migration manifest;
- verifies canonical ISA rows still match the generated production opcode contract;
- verifies required production and canonical paths exist;
- scans production roots for registered legacy references using dependency-aware matching;
- locks legacy deletion behind an explicit equivalence/physical-evidence policy;
- adds regression coverage for both passing and failing migration conditions.

## What H26-I does not change

- no opcode renumbering;
- no VM dispatch changes;
- no RobotAPI semantic changes;
- no generated `program.h` format changes;
- no firmware upload behavior changes;
- no deletion of `robot-common` or the older C++ compiler files;
- no claim of physical robot validation.

## Acceptance criterion

H26-I is complete when the migration boundary itself is testable and enforced:
canonical semantics remain aligned with the production opcode contract, registered
legacy components are isolated from production roots, and retirement remains
blocked until the evidence chain is complete.
