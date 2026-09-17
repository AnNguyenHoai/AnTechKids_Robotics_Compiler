# RSD-21.6 — Production Release Launcher / Entry Point

> **RSD-22 authority notice:** This document defines the launcher mechanism only. RSD-23 owns application runtime packaging.

## Purpose

Provide a user-facing Windows entry point for the production RoboStudio release.

`RoboStudio.cmd` starts the application relative to the launcher's own directory. The copied release therefore does not depend on the developer repository, caller CWD, PATH, or PYTHONPATH.

## Current release boundary

The production ZIP contains `RoboStudio.exe`, application-local DLL dependencies, `RoboStudio.cmd`, application resources, compiler/frontend payload, application-owned Python under `runtime/bin`, and application-owned PlatformIO under `runtime/platformio`.

## Launcher contract

`RoboStudio.cmd` must resolve `RoboStudio.exe` from `%~dp0`, make the release directory the process working directory, forward `%*`, fail clearly when the executable is missing, and propagate the application exit code.

## Verification

```powershell
python tests\rsd_21_6\run_rsd_21_6.py
```
