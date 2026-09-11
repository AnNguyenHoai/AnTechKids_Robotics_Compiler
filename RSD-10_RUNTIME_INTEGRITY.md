# RSD-10 — Portable Runtime Integrity & Version Lock

## Objective

Freeze the identity of the runtime shipped with RoboStudio and fail closed when
runtime bytes or the application version drift after packaging.

## Contract

The distribution contains `runtime/runtime-integrity.json`. The manifest records:

- RoboStudio application version from `VERSION`.
- Portable Python runtime files.
- PlatformIO Core files.
- PlatformIO platform files.
- PlatformIO package files.
- Runtime resource files.
- Deterministic SHA-256 fingerprints and per-file size/digest records.

The manifest is generated **after** resource metadata has been generated, so the
fingerprints represent the final bytes shipped in the distribution.

## Validation

`tools/runtime_integrity.py` validates:

1. Manifest schema and portability flag.
2. Application version.
3. Required runtime components.
4. Exact component file lists.
5. Per-file sizes and SHA-256 digests.
6. Deterministic component fingerprints.
7. Safe relative paths.

`runtime_preflight.validate_distribution()` automatically validates the RSD-10
manifest when it is present. Pre-RSD-10 hand-built fixtures remain compatible,
while assembled distributions are protected by the new integrity boundary.

## Host isolation

RSD-10 does not discover or import runtime components from the host. It only
fingerprints files under the application-owned `runtime/` tree. Runtime
resolution remains governed by the existing RSD-02 application-owned path
contract.

## Release gate

Before release, run:

```powershell
python tests\rsd_10\run_rsd_10.py
python run_all_tests.py
```

A runtime mutation must be rejected before deployment can proceed.
