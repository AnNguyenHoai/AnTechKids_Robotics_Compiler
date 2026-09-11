# RSD-15 — Release Compatibility Contract

## Purpose

RSD-15 defines the compatibility identity of a portable RoboStudio release. A release must carry enough information to prove that its application, runtime integrity, distribution, and release schemas belong to the same supported contract.

## Contract

Each release manifest contains a `compatibility` object with:

- `schema`: `antechkids.robostudio.release-compatibility`
- `schema_version`: `1`
- `application_version`: the shipped `VERSION` value
- `runtime_integrity_schema_version`: the runtime-integrity contract version
- `distribution_schema_version`: the distribution contract version
- `release_schema_version`: the release-manifest contract version
- `portable_python_required`: must be `true`
- `bundled_platformio_required`: must be `true`

The top-level release manifest also records the same `application_version`; validation rejects disagreement between the two fields.

## Compatibility policy

Application versions use `MAJOR.MINOR.PATCH` syntax.

- The release and runtime must have the same major version.
- A release newer than the runtime is rejected.
- Older or equal releases within the same major are accepted by the application-version check.
- Runtime-integrity, distribution, and release schema versions must match exactly.
- Portable Python and application-owned PlatformIO are mandatory for portable releases.

Schema compatibility is intentionally stricter than application-version compatibility because schema changes can alter the meaning of persisted metadata.

## Failure classes

The compatibility API distinguishes malformed metadata from incompatible metadata and produces deterministic errors for:

- missing compatibility contract;
- unsupported compatibility schema;
- malformed application version;
- incompatible application major version;
- release newer than runtime;
- runtime-integrity schema drift;
- distribution schema drift;
- release schema drift;
- disabled portable Python requirement;
- disabled bundled PlatformIO requirement.

## API

`tools.release_compatibility` provides:

- `parse_version()`
- `build_compatibility()`
- `read_compatibility()`
- `validate_compatibility()`

`tools.release_package.validate_release_compatibility()` exposes the contract through the existing release-package error boundary for callers that already consume `release_package`.

## Verification

Run:

```powershell
python tests\rsd_15\run_rsd_15.py
python run_all_tests.py
```
