# RSD-21.4 — Target-Machine-Aware Release Qualification

## Purpose

RSD-21.4 qualifies a production RoboStudio release against the environment that a real target user is expected to have. It does **not** require the developer's Python installation, PlatformIO installation, virtual environment, or source checkout to be copied into the release.

The release boundary is:

```text
Production ZIP
  ├── RoboStudio
  ├── application-owned compiler
  ├── application-owned resources/dependencies
  └── release evidence

Target machine
  ├── Python          (compile prerequisite)
  ├── PlatformIO Core (hardware prerequisite)
  └── ESP32/USB driver (hardware prerequisite)
```

## Qualification scopes

### Compile scope

```powershell
python -m tools.production_release_qualification <artifact.zip> --target-machine --prerequisite-scope compile
```

This verifies the prerequisites needed to use the release for compilation. Python is checked using the declared `python --version` command.

### Hardware scope

```powershell
python -m tools.production_release_qualification <artifact.zip> --target-machine --prerequisite-scope hardware
```

This verifies Python and PlatformIO automatically and records the ESP32/USB driver as a manual check. Driver availability is intentionally not inferred because the correct USB/UART driver depends on the selected board.

## What this gate does

1. Validates the release ZIP and release manifest.
2. Verifies the existing RSD-20 portable dependency/provenance boundaries.
3. Checks target-machine prerequisites without installing or mutating them.
4. Records executable paths and version command output as qualification evidence.
5. Produces a machine-readable target-machine qualification section in the RSD-21 report.

## What this gate does not do

This task does not install Python, PlatformIO, drivers, or any other host prerequisite. It also does not claim that GUI startup, physical USB access, firmware flashing, or OTA has been completed. Those remain later production/hardware acceptance gates.

## Release rule

A target machine is qualified only when all automatically checkable prerequisites for the requested scope are available. Manual hardware prerequisites are explicitly reported rather than silently treated as verified.
