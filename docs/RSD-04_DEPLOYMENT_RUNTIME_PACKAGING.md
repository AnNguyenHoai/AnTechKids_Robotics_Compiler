# RSD-04 — Deployment Runtime Packaging

## Goal

Make USB/bootstrap/OTA deployment consume a RoboStudio-owned deployment runtime rather than the target machine's PlatformIO installation, PlatformIO home, or shell PATH.

## Runtime contract

```text
RoboStudio/
├── RoboStudio.exe
├── app/
├── compiler/
├── firmware/
├── assets/
└── runtime/
    ├── bin/
    │   └── python.exe
    └── platformio/
        ├── platforms/
        ├── packages/
        ├── lib/
        ├── workspace/
        ├── build-cache/
        └── .cache/
```

The bundled Python runtime is the future owner of the PlatformIO module. A copied Windows `venv` is deliberately not treated as portable because its interpreter metadata can retain the machine-specific Python installation path. The packager therefore rejects `penv` unless `--allow-penv` is explicitly used for development-only experiments.

## Implemented

### 1. Application-owned PlatformIO environment

`tools/deployment_runtime.py` now exposes `deployment_runtime_environment()`.

In frozen mode it sets:

- `PLATFORMIO_CORE_DIR`
- `PLATFORMIO_PLATFORMS_DIR`
- `PLATFORMIO_PACKAGES_DIR`
- `PLATFORMIO_CACHE_DIR`
- `PLATFORMIO_BUILD_CACHE_DIR`
- `PLATFORMIO_WORKSPACE_DIR`
- `PLATFORMIO_DISABLE_UPGRADE_CHECK=true`
- `PLATFORMIO_DISABLE_PROGRESSBAR=true`
- `PLATFORMIO_NO_ANSI=true`

This prevents PlatformIO from silently creating/using `%USERPROFILE%\\.platformio` for a packaged deployment.

### 2. Application-owned PlatformIO command

`runtime_paths.platformio_command()` prefers:

```text
runtime/bin/python.exe -m platformio ...
```

when the packaged Python exists. This is preferred over copying a PlatformIO Windows virtual-environment executable. A directly bundled `pio.exe`/`platformio.exe` remains supported as a compatibility path. Frozen mode never falls back to system Python or PATH.

### 3. Existing deployment flows use the isolated environment

Both `tools/deploy_robot.py` and `tools/flash.py` now pass the application-owned deployment environment to PlatformIO subprocesses.

This covers:

- normal firmware build;
- USB upload;
- bootstrap/first flash;
- OTA firmware build;
- manifest-based flash.

The HTTP OTA transport remains application-owned and does not invoke PlatformIO for the network transfer itself.

### 4. Release staging tool

`tools/package_deployment_runtime.py` stages a provisioned PlatformIO Core data directory into `runtime/platformio` and writes `deployment-runtime.json`.

The tool is a **release-build utility**, not an end-user installer. It does not modify the developer's PlatformIO installation.

Required source directories:

```text
platforms/
packages/
```

Optional:

```text
lib/
```

Excluded by default:

```text
penv/
```

## Why the PlatformIO core data is packaged

PlatformIO's core directory contains development platforms, toolchains, frameworks, SDKs, upload/debug tools and related service data. Pointing `PLATFORMIO_CORE_DIR` at the RoboStudio runtime makes those dependencies application-owned instead of user-owned. The final bundle must therefore be produced from a known-good, fully provisioned release environment.

## Clean-machine acceptance

RSD-04 is complete only when the eventual Windows distribution can demonstrate:

1. no global Python required;
2. no global PlatformIO required;
3. no Git required;
4. no PATH lookup for deployment tools;
5. USB flash works with a user-selected COM port;
6. bootstrap first flash works with packaged PlatformIO runtime and artifacts;
7. OTA build/upload works without a host PlatformIO home;
8. PlatformIO does not write deployment state to `%USERPROFILE%\\.platformio`;
9. missing packaged runtime produces an actionable error rather than fallback;
10. deployment logs remain readable and bounded by the existing process timeout.

## Next step

**RSD-05 — RoboStudio Windows Portable Build** should package the application, compiler runtime, portable Python runtime, PlatformIO module, required PlatformIO ESP32 packages, firmware/artifacts and assets into a reproducible Windows onedir distribution.
