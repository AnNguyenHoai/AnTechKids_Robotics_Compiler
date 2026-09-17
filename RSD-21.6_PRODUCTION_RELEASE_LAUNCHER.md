# RSD-21.6 — Production Release Launcher / Entry Point

> **RSD-22 authority notice:** This document defines the launcher mechanism only. The production release boundary is defined by `RSD-22_RELEASE_CONTRACT_CONSOLIDATION.md`.

## Purpose

Provide a user-facing Windows entry point for the production RoboStudio release.

The launcher is part of the production artifact and starts the application relative to the launcher's own directory. A copied release therefore does not depend on the developer repository, the caller's current working directory, `PATH`, or `PYTHONPATH`.

## Current release boundary

The current production ZIP contains:

- `RoboStudio.exe`
- application-local DLL dependencies
- `RoboStudio.cmd`
- application resources
- release metadata

The current implementation treats Python and PlatformIO as target-machine prerequisites. This is explicitly a current-state boundary under RSD-22; the final zero-development-machine target is owned by RSD-23.

## Launcher contract

`RoboStudio.cmd` must:

1. resolve `RoboStudio.exe` from `%~dp0`;
2. make the release directory the process working directory;
3. forward all user arguments with `%*`;
4. fail clearly when the executable is missing;
5. propagate the application exit code.

No repository path or developer-specific installation path may be embedded in the launcher.

## Verification

Run from the repository root:

```powershell
python tests\rsd_21_6\run_rsd_21_6.py
```

The regression suite verifies both the production distribution and the final release ZIP.
