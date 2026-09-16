# Target Machine Setup Contract

## Purpose

This contract defines what a Windows target machine must provide before using an AnTechKids RoboStudio production release.

The production release contains the application-owned RoboStudio, Compiler, RoboSim frontend, and application resources. Host tooling is installed on the target machine and is **not** copied from the development machine.

## Supported target

- Windows 10/11 x64
- A target user account with permission to install Python, PlatformIO, and the required USB/UART driver

## Prerequisites

| Prerequisite | Scope | Policy | Validation |
|---|---|---|---|
| Python | Compile + Hardware | Python 3.10+ 64-bit | `python --version` |
| PlatformIO Core | Hardware | Supported PlatformIO Core release | `pio --version` |
| ESP32/USB driver | Hardware | Driver appropriate for the selected board's USB/UART bridge | Manual/device check |

### PATH policy

The `python` and `pio` commands must be resolvable from the target user's `PATH`. The application must not depend on a developer-specific absolute path.

## Recommended setup sequence

### 1. Install Python

Install a supported 64-bit Python 3.10+ release.

During installation, enable the option that makes the Python command available from the command line.

Verify:

```text
python --version
python -m pip --version
```

### 2. Install PlatformIO Core

PlatformIO is required only for hardware build/deployment. It is not part of the RoboStudio production payload.

Install with:

```text
python -m pip install --upgrade platformio
```

Verify:

```text
pio --version
```

### 3. Install the ESP32 USB/UART driver

Install the driver required by the USB/UART bridge used by the target ESP32 board. The exact driver depends on the board hardware.

After connecting the board, verify that Windows exposes the board through the expected USB/serial interface.

### 4. Copy the RoboStudio release

Copy/extract the release directory to any user-writable location, for example:

```text
D:\AnTechKids\RoboStudio\
```

Do not rely on the development repository path.

### 5. Qualify the machine

From the repository/release tooling environment, run the existing target-machine qualification for the required scope:

```text
python -m tools.release_cli accept <artifact> --target-machine --prerequisite-scope compile
```

For hardware deployment:

```text
python -m tools.release_cli accept <artifact> --target-machine --prerequisite-scope hardware
```

The qualification is read-only: it checks availability and reports prerequisites; it does not install or modify host tooling.

## Scope model

### Compile

Required:

- Python
- RoboStudio
- Compiler
- RoboSim frontend

PlatformIO and the ESP32 USB/UART driver are not required merely to compile a program.

### Hardware

Hardware use is cumulative with compile:

- Python
- PlatformIO Core
- ESP32 USB/UART driver
- RoboStudio
- Compiler
- RoboSim frontend

## Release boundary

The following must remain external to the production ZIP:

- Python installation
- PlatformIO installation
- Developer virtual environments
- Developer source repository

The release must contain the application-owned Compiler and RoboSim frontend needed by the RoboStudio → Compiler contract.

## Troubleshooting principles

1. If `python --version` fails, fix Python installation/PATH first.
2. If `pio --version` fails, fix PlatformIO installation/PATH before attempting hardware deployment.
3. If the ESP32 is not visible to Windows, check the board USB/UART driver and cable before debugging RoboStudio.
4. If RoboStudio or Compiler refers to a development-machine path, treat it as a portability defect rather than adding a machine-specific workaround.
