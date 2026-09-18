# B2.3 — Portable Path & State Isolation

Stacked on B2.2 hardening PR #262 (`13ec6ca2cd484a546039fa0e018a6b915073c794`).

## Problem

B2.2 closed executable/dependency lookup, but mutable PlatformIO state could still be rebound into `runtime/platformio` at the final subprocess boundary. The historical `ROBOSTUDIO_PORTABLE_DATA` mode also allowed `<release>/data`, making an extracted release mutable.

## Solution

- introduce `ROBOSTUDIO_STATE_ROOT` as the explicit external writable state boundary;
- reject relative or release-local state roots in packaged mode;
- reject legacy in-install portable data in packaged mode;
- fail fast when the external state root cannot be created/written;
- move PlatformIO core service data/cache/workspace/build/libdeps/shared/global-lib state outside the artifact;
- keep only PlatformIO platforms/packages and executable dependencies inside the artifact;
- preserve trusted project-specific state paths through the final B2.2 process seal only when they remain below the validated state root;
- make build path derivation use one environment snapshot instead of reading unrelated global environment state;
- verify firmware templates are copied to writable external state before mutation;
- add Unicode/space/unrelated-CWD/immutable-release regression coverage;
- add dedicated B2.3 Windows CI gate and include it in `run_all_tests.py`.

## Acceptance

The production release is treated as immutable. Mutable settings/build/cache state is external, path resolution does not depend on CWD, release/state paths with spaces and Unicode are preserved by RoboStudio's path layer, and invalid state roots fail closed.

Real PlatformIO/USB behavior on all non-ASCII Windows path combinations remains a B2.4+ hardware qualification concern because PlatformIO documents upstream non-ASCII path limitations.
