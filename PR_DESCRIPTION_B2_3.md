# B2.3 — Portable Path & State Isolation

## Lineage

B2.2 hardening PR #262 is already merged into `main` at `4423ad23dfe6a8840f009f029ec817f7c8e70247`. B2.3 is based directly on that merge and targets `main`.

## Problem

B2.2 closed executable/dependency lookup, but mutable state could still escape the portability contract: PlatformIO Core/cache/build paths could point at the release, user settings and generated firmware headers could be written beside packaged files, bootstrap generation could mutate the packaged Arduino sketch, and GUI compilation could use the application directory as its working directory.

## Solution

- introduce `ROBOSTUDIO_STATE_ROOT` as the explicit external writable state boundary;
- reject relative, release-local, legacy in-install, or unwritable state roots in packaged mode;
- keep the extracted production release immutable;
- move PlatformIO Core/cache/workspace/build/libdeps/shared/global-lib state outside the artifact while keeping bundled platforms/packages inside;
- preserve only trusted project-specific mutable paths that remain below the validated state root;
- persist hardware configuration and firmware selection under external user state, with packaged configuration used only as read-only defaults;
- generate `generated_device_config.h` under external state and overlay it only into the staged firmware copy;
- copy the packaged Arduino bootstrap sketch to external state before generating bootstrap JSON/header or opening it for editing;
- run GUI compilation with a B2.2-sealed environment and a disposable external compile workspace/CWD;
- keep production E2E compiler output and working directories outside the extracted release;
- cover Unicode/space relocation, unrelated CWD, hostile host overrides, invalid state roots, user settings, generated files, bootstrap, GUI compile, and byte-for-byte release immutability;
- expose dedicated B2.2 and B2.3 Windows CI gates before the full repository regression suite.

## Acceptance

The copied production release behaves as an immutable application payload. Mutable settings, generated headers, bootstrap data, compiler scratch data, PlatformIO Core/cache/build state, and firmware working copies live outside the release. Path resolution does not depend on the caller CWD, and production rejects any supported state override that would write back into the release.

Real target-machine PlatformIO + USB/COM + physical robot qualification, including upstream non-ASCII toolchain limitations, remains B2.4+ hardware portability scope.
