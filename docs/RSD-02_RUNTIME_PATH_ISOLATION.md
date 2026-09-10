# RSD-02 — Runtime Path Isolation & Application-Owned Tool Resolution

## Status

Implemented on top of RSD-01.

## Scope

RSD-02 establishes deterministic path and executable resolution so the future RoboStudio distribution does not rely on:

- the current working directory;
- a repository checkout;
- a developer-specific absolute path;
- Python installed globally;
- PlatformIO/pio installed on `PATH`.

## Runtime contract

The new `tools/runtime_paths.py` module provides:

- `application_root()` — immutable application/distribution root;
- `user_data_root()` — writable per-user data root;
- `resolve_path()` — deterministic application/data path resolution;
- `resolve_bundled_tool()` — lookup only inside the RoboStudio runtime tree;
- `python_command()` — packaged Python when available, development interpreter otherwise;
- `platformio_command()` — packaged `pio`/`platformio` in frozen builds, development fallback only in source builds;
- `require_bundled_tool()` — explicit failure for missing release tools.

## Resolution policy

### Packaged/frozen build

```text
<RoboStudio>/runtime/bin/pio.exe
<RoboStudio>/runtime/bin/python.exe
<RoboStudio>/runtime/tools/<tool>
```

A frozen build **never** falls back to `PATH` or system Python. A missing mandatory tool produces `RuntimePathError` with an actionable message.

### Source/development build

The repository remains runnable with the existing development environment. For PlatformIO this means:

```text
<current Python> -m platformio ...
```

This fallback exists only to preserve development workflows; it is not the release contract.

## Data isolation

Normal installation data is placed under `%LOCALAPPDATA%/RoboStudio` (or the platform fallback used by `user_data_root()`). Explicit portable mode uses:

```text
<RoboStudio>/data
```

through `ROBOSTUDIO_PORTABLE_DATA=1`.

This keeps mutable projects, configuration, logs, and cache separate from immutable application files.

## Deployment integration

`tools/deployment_runtime.py` now delegates PlatformIO command construction to the runtime resolver. Therefore the deployment layer no longer owns executable lookup policy.

This is important for the first-flash flow: the existing development invocation remains compatible, while a future packaged build can supply its own `runtime/bin/pio.exe` without changing the deployment service contract.

## Explicit non-goals

RSD-02 does not yet package PlatformIO/esptool, compile firmware, or create the final `.exe`. Those belong to subsequent distribution tasks after the path boundary is stable.

## Verification

Run:

```text
python tests/rsd_02/run_rsd_02.py
```

The test verifies:

- application root is independent of CWD;
- normal data is separated from the application root;
- portable data mode is explicit;
- bundled `pio.exe` is selected by absolute path;
- frozen builds reject missing bundled PlatformIO instead of using system tooling;
- source builds retain the development fallback;
- application and writable paths resolve from their respective roots.

## Next step

**RSD-03 — Compiler Runtime Packaging**

Move compiler invocation behind an application-owned service and define the exact runtime payload needed to compile RoboSim programs on a clean Windows machine.
