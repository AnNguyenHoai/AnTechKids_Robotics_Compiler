# H26-M — Deployment Contract

## Goal

Introduce a deterministic deployment boundary between compiler artifacts and the physical ESP32 flashing step.

## Contract

A deployment manifest is the hand-off for flashing. It records the contract schema, selected deployment target, canonical required capabilities, PlatformIO environment, and exact artifact metadata. Each artifact is recorded with its path, byte size, and SHA-256 checksum.

## Enforcement

`tools/flash.py` requires `--manifest` and validates the complete manifest before copying `program.h` into the firmware project or invoking PlatformIO. Validation rejects malformed manifests, unknown targets, target/capability incompatibility, missing artifacts, changed sizes, checksum mismatches, and requested/manifest target mismatches.

## API

`tools/deployment_contract.py` provides `create_manifest`, `write_manifest`, `load_manifest`, `validate_manifest`, and `sha256_file`.

The canonical target capability profile remains `packages/robot-isa/target_profiles.json`.

## Boundary

H26-M does not change compiler semantics, bytecode, VM dispatch, or firmware execution. It establishes and enforces the deployment hand-off contract.

## Validation

```bash
python tests/h26_m/run_h26_m.py
python run_all_tests.py
```
