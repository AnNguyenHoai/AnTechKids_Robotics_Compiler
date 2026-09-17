# RSD-28 — Production PlatformIO Dependency Closure

## Purpose

The production RoboStudio ZIP must be able to build firmware without resolving PlatformIO platforms or packages from the developer machine. The firmware project declares its dependency roots; the application-owned `runtime/platformio` payload must contain the exact platform and every package required by that platform.

## Contract

1. `robot-platform/platformio.ini` must pin the ESP32 PlatformIO platform to an exact version.
2. The production environments are `esp32dev`, `esp32dev_bootstrap`, and `esp32dev_ota`.
3. Inherited environments must resolve to the same pinned platform as `esp32dev` unless they explicitly declare another exact platform.
4. The packaged PlatformIO runtime must contain matching `platform.json` metadata for the requested platform/version.
5. Every package declared by the selected platform metadata must have matching `package.json` metadata in the application-owned `runtime/platformio/packages` tree.
6. Conflicting package versions across supported environments fail closed.
7. Validation never consults PATH, user-local PlatformIO state, the current working directory, or a host virtual environment.
8. The validator records the resolved platform/package identities as release evidence.

## Implemented

- `tools/production_platformio_closure.py` performs deterministic closure validation without invoking PlatformIO.
- Production distribution validation invokes this closure check before assembling the artifact.
- `espressif32` is pinned to `6.12.0` in the firmware project.
- Regression tests cover unpinned platforms, missing packages, platform version mismatch, and all three deployment environments.

## Dependency graph

```text
platformio.ini
    |
    +--> espressif32@6.12.0
             |
             +--> platform.json
             |
             +--> required packages
                       |
                       +--> package.json for each exact version
```

## Important limitation

The repository does not contain the Windows application-owned PlatformIO runtime itself. Therefore the validator can enforce the contract and fail closed, but final closure evidence requires running it against the actual runtime payload that will be packaged. The runtime must contain metadata matching the pinned `espressif32@6.12.0` platform and all packages declared by that platform.

This is intentionally separate from clean-machine and physical ESP32 qualification.
