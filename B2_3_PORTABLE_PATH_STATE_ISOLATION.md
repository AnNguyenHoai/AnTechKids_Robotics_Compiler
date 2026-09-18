# B2.3 — Portable Path & State Isolation

## Objective

B2.3 makes the extracted RoboStudio production release an **immutable application payload**. The ZIP may be copied/extracted to a different directory, a path containing spaces, or a Unicode path without making mutable runtime state relative to the install directory or caller CWD.

B2.3 is stacked on B2.2 dependency closure. B2.2 answers **where executable/runtime dependencies may come from**; B2.3 answers **where mutable state may be written**.

## Canonical boundary

```text
<release-root>/                         READ-ONLY / IMMUTABLE
├── RoboStudio.exe
├── compiler/
├── firmware/
└── runtime/
    ├── bin/                            bundled Python
    └── platformio/
        ├── platforms/                  bundled immutable platform definitions
        └── packages/                   bundled immutable toolchains/frameworks

<ROBOSTUDIO_STATE_ROOT>/                WRITABLE / EXTERNAL
├── platformio/
│   ├── core/                           PlatformIO service/core state
│   ├── cache/
│   ├── build-cache/
│   ├── workspace/
│   ├── lib/
│   └── shared/
└── build/<project>/platformio/
    ├── build/
    ├── libdeps/
    ├── cache/
    ├── build-cache/
    ├── shared/
    └── firmware/                       copied writable firmware project
```

## State-root contract

`ROBOSTUDIO_STATE_ROOT` is the explicit production override for writable RoboStudio state. It must be:

- absolute;
- outside the extracted application/release root;
- writable by the current user.

When no explicit override is supplied, RoboStudio uses the normal per-user data location (`LOCALAPPDATA/RoboStudio` on Windows, with a home-directory fallback).

The historical `ROBOSTUDIO_PORTABLE_DATA=1` mode wrote to `<release>/data`. It is rejected for packaged/artifact-closed execution because it mutates the copied release. It remains only as a source/development compatibility mode.

## PlatformIO split

PlatformIO's `core_dir` contains mutable service data, so production no longer points `PLATFORMIO_CORE_DIR` into `runtime/platformio`.

Production sets:

- `PLATFORMIO_CORE_DIR` → external state;
- `PLATFORMIO_CACHE_DIR` → external state;
- `PLATFORMIO_BUILD_CACHE_DIR` → external state;
- `PLATFORMIO_WORKSPACE_DIR` → external state;
- `PLATFORMIO_BUILD_DIR` → external state;
- `PLATFORMIO_LIBDEPS_DIR` → external state;
- `PLATFORMIO_SHARED_DIR` → external state;
- `PLATFORMIO_GLOBALLIB_DIR` → external state;
- `PLATFORMIO_PLATFORMS_DIR` → bundled `runtime/platformio/platforms`;
- `PLATFORMIO_PACKAGES_DIR` → bundled `runtime/platformio/packages`.

Host-supplied mutable PlatformIO paths are discarded unless they are already below the validated RoboStudio state root. This lets a project-specific workspace survive the final B2.2 subprocess sealing step without allowing arbitrary host state back into production.

## Fail-closed behavior

Packaged startup/build fails with an actionable error when:

- `ROBOSTUDIO_STATE_ROOT` is relative;
- the state root is equal to or below the release root;
- legacy in-install portable state is requested;
- the state root cannot be created;
- the state root is not a directory;
- a write probe cannot be created/deleted;
- a build workspace cannot be created.

Inspection-only bootstrap (`apply=False`) resolves and validates path boundaries but does not create state.

## Relocation requirements

The B2.3 gate verifies:

1. release roots containing spaces and Vietnamese/Unicode characters are resolved without CWD dependence;
2. an unrelated CWD does not alter application/state resolution;
3. mutable PlatformIO paths remain outside the release;
4. bundled platforms/packages remain inside the release;
5. hostile host PlatformIO state overrides cannot redirect production;
6. project-specific external state survives the final subprocess closure;
7. the firmware template is copied to external state before mutation;
8. the release tree is unchanged after workspace preparation;
9. invalid/unwritable state roots fail fast.

## PlatformIO Unicode note

RoboStudio's path/state layer is Unicode-safe and the B2.3 tests exercise Unicode + spaces. PlatformIO itself documents known limitations for some non-ASCII project/toolchain paths. B2.3 therefore guarantees that RoboStudio does not derive mutable state from the release path and preserves Unicode paths correctly; final real PlatformIO/USB qualification on target Windows machines remains part of B2.4+ hardware portability.

## Verification

```powershell
python tests\b2_2\run_b2_2.py
python tests\b2_2\run_portable_child_closure.py
python tests\b2_3\run_b2_3.py
python run_all_tests.py
```

The GitHub Actions workflow exposes B2.3 as a dedicated gate before the full repository regression suite.
