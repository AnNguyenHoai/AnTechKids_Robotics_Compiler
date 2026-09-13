# RSD-21.2 — Target Machine Requirements

## Purpose

A production RoboStudio release is a distributable application package. The ZIP contains **RoboStudio + Compiler + application-owned resources and dependencies**. It does not contain a developer's Python or PlatformIO installation.

The target user prepares the machine once, according to this document, then extracts and runs the production release.

## Target Machine Contract

| Prerequisite | Required for | Packaged in ZIP | Target validation |
|---|---|---:|---|
| Windows x64 | IDE / Compile / Hardware | No | Supported Windows host |
| Python >= 3.10 | Compile | **No** | `python --version` |
| PlatformIO Core | Hardware | **No** | `pio --version` |
| ESP32/USB driver | Hardware | **No** | Driver/device check when hardware is connected |

Exact PlatformIO and driver versions are intentionally controlled by the supported toolchain rather than copied from the developer machine. When an exact production version is pinned, this contract must be updated together with the release toolchain.

## Installation Responsibilities

### Target user

The target user is responsible for installing:

1. A supported 64-bit Python 3.10+ installation.
2. PlatformIO Core when hardware build/deployment is required.
3. The USB/UART driver required by the selected ESP32 board when hardware deployment is required.

After installation, `python` and, when hardware is required, `pio` must be available from the user's command shell.

### Production release

The release package is responsible for delivering:

- RoboStudio IDE/application.
- Application-owned Compiler.
- Compiler and IDE resources.
- Application-local libraries and non-system PE dependencies.
- Release manifest, provenance, and integrity evidence.

The release package must **not** copy or depend on the developer machine's Python installation, PlatformIO installation, virtual environment, source repository, or absolute host paths.

## Installation Check

Before using RoboStudio:

```powershell
python --version
```

Expected: Python 3.10 or a later supported version.

For hardware workflows:

```powershell
pio --version
```

Expected: a supported PlatformIO Core release.

Connect the ESP32 only after its USB/UART driver has been installed.

## Operational Boundary

The target machine may provide host prerequisites, but the installed RoboStudio release must not require:

- a clone of the source repository;
- the developer's `.venv` or another developer virtual environment;
- files from the developer's Python installation;
- files from the developer's PlatformIO installation;
- developer-specific absolute paths;
- IDE/development tools that are not declared as release prerequisites.

## Evidence

The machine-readable source of truth is:

```text
tools/target_machine_prerequisites.py
```

RSD-21 qualification and later release assembly/acceptance tasks should consume that contract instead of maintaining separate prerequisite lists.
