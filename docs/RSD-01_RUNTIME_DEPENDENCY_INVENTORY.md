# RSD-01 — RoboStudio Runtime Dependency Inventory

**Baseline:** `0d7754b12a2f76d744c8f35d0e721b1650670459`

## Purpose

This document is the release-engineering inventory for converting RoboStudio from a developer-environment application into a Windows portable distribution.

It deliberately separates **runtime requirements** from **development/build requirements**. An item is considered a release blocker when RoboStudio needs it on the target machine but the current design obtains it from the developer machine, PATH, repository checkout, or an undeclared environment variable.

## 1. Inventory model

| ID | Dependency class | Runtime role | Current risk | Packaging direction |
|---|---|---|---|---|
| R1 | RoboStudio application code | UI/workspace/application logic | Must be imported at runtime | Bundle |
| R2 | RoboSim compiler | Compile user programs | Must be available to RoboStudio | Bundle/embedded executable |
| R3 | Robot deployment | Bootstrap/firmware upload | Currently coupled to development tooling | Isolate behind DeploymentService |
| R4 | Serial transport | USB/COM robot communication | Target machine has variable COM ports | Bundle runtime library; discover dynamically |
| R5 | OTA transport | Wi-Fi deployment/recovery | Must not depend on developer CLI | Bundle application-owned implementation |
| R6 | Firmware/artifacts | Robot runtime payload | Release version must be deterministic | Bundle release artifacts |
| R7 | Assets/config | UI and application configuration | Relative-path assumptions can break outside checkout | Resolve from application root/data root |
| R8 | Python interpreter | Current development/runtime implementation | Global Python must not be required | Private runtime or compiled application |
| R9 | PlatformIO | Current ESP32 build/upload infrastructure | Must not be a user prerequisite | Build-time only initially; private runtime only if required for release upload |
| R10 | esptool | Low-level ESP32 flashing | Upload dependency | Bundle/private or replace with deployment library |
| R11 | ESP32 toolchain | Firmware compilation | Not required for end-user operation if firmware is prebuilt | Build/release machine only |
| R12 | Git | Source/repository operations | Never required to run released RoboStudio | Development only |

## 2. Application boundary

The target production boundary is:

```text
+----------------------------------------------------------+
|                     RoboStudio Bundle                    |
|                                                          |
|  RoboStudio application                                  |
|      |                                                   |
|      +-- Compiler runtime                                |
|      +-- Serial transport                                |
|      +-- OTA transport                                   |
|      +-- Deployment runtime                              |
|      +-- Firmware/artifacts                              |
|      +-- UI assets                                       |
|      +-- release configuration                           |
|                                                          |
+----------------------------------------------------------+
                         |
                    USB / Wi-Fi
                         |
                         v
                       ESP32
```

The following are **not** part of the target user's installed environment:

```text
Python from PATH
PlatformIO from PATH
pio from PATH
Git from PATH
ESP32 compiler/toolchain from PATH
repository checkout
```

## 3. Runtime dependency classes

### 3.1 Application/runtime code

RoboStudio's Python modules are application payload, not user-installed dependencies. The packaging system must collect all imports used by the GUI, compiler integration, deployment, configuration, and recovery paths.

Special attention is required for:

- dynamic imports;
- plugins discovered by filesystem scanning;
- Qt platform plugins;
- native Python extensions;
- subprocess-created child processes;
- data files loaded with relative paths.

A clean-machine test must prove that no import falls back to a globally installed package.

### 3.2 Compiler

The compiler is a first-class RoboStudio runtime component. Its public contract should be:

```text
source.py
   -> compiler service
   -> validated robot program / bytecode artifact
```

The user should not need to invoke the compiler through a shell command or install its Python environment separately.

### 3.3 USB / serial

USB/serial is an external OS resource, not a Python installation dependency. The application should:

1. enumerate available serial ports;
2. identify the supported robot where possible;
3. allow the user to select a port when multiple candidates exist;
4. open/close the port through the packaged serial runtime;
5. surface actionable connection errors.

The implementation must not hard-code `COM4` or any other development-machine port.

### 3.4 OTA

OTA requires only the packaged application-side network implementation and a reachable/provisioned robot. It must not require PlatformIO, Python CLI tools, or Git on the target machine.

The OTA artifact must come from a deterministic release artifact directory, not from an arbitrary developer build directory.

### 3.5 Firmware

Firmware is a release input. The distribution should contain the exact firmware/artifact set needed by the supported deployment flow, with version/build metadata sufficient to prevent accidental cross-version flashing.

Firmware compilation remains a build pipeline responsibility unless a future product requirement explicitly moves compilation onto the teacher/student machine.

## 4. External command inventory to enforce

The following command families are development/build concerns and must be treated as **forbidden direct runtime dependencies** in the final RoboStudio UI:

```text
python ...
pip ...
platformio ...
pio ...
git ...
xtensa-esp32-elf-* ...
```

If a release implementation temporarily bundles PlatformIO/esptool, RoboStudio must invoke the private executable using an application-owned absolute path and must not depend on PATH lookup.

## 5. Filesystem dependency rules

### Forbidden runtime assumptions

```text
D:\TINHOCTRE\...
C:\Users\...\AppData\Roaming\Python\...
%PATH%\python.exe
%PATH%\pio.exe
current working directory == repository root
```

### Required runtime model

Use an application root and explicit writable data root:

```text
<ApplicationRoot>/
    RoboStudio.exe
    app/
    runtime/
    compiler/
    firmware/
    assets/

<UserDataRoot>/RoboStudio/
    config/
    projects/
    logs/
    cache/
```

The exact Windows user-data location is an implementation decision for RSD-02; the important contract is that mutable data is not written into the installation directory unless an explicit portable mode is selected.

## 6. Environment-variable inventory

Any environment variable used by RoboStudio must be classified as one of:

- **release configuration** — supplied by the application/package;
- **user configuration** — entered/stored by the user;
- **development configuration** — allowed only in developer builds.

Variables that merely make the developer machine work must not silently become release prerequisites.

The bootstrap configuration used by PlatformIO is a build/deployment concern and must be resolved by the packaged deployment layer rather than requiring the user to set a shell variable manually.

## 7. Dependency matrix

| Capability | Required on clean machine | Current source of dependency | Release requirement |
|---|---|---|---|
| Start RoboStudio | Yes | Application + Python/Qt runtime | Private/bundled |
| Open project | Yes | Application filesystem | Bundle + user-data root |
| Compile RoboSim | Yes | Compiler + Python runtime | Private/bundled |
| Discover robot | Yes | OS serial/network APIs | Bundled runtime |
| Serial console | Yes | Serial library/driver | Bundled runtime + OS USB driver if hardware requires one |
| First flash/bootstrap | Yes | PlatformIO/esptool/toolchain today | Prebuilt firmware + private deploy runtime |
| OTA | Yes | Application network/upload code | Bundled |
| Recovery | Yes | Backup/recovery services + storage | Bundled |
| Logging | Yes | Application logging | Bundled + writable user-data root |
| Firmware build | No | PlatformIO + ESP32 toolchain | Build machine only |
| Git operations | No | Git | Development only |

## 8. Risk register

### P0 — Repository-coupled runtime paths

Any runtime code using absolute developer paths or assuming the repository is the current working directory will fail on another machine.

**Action:** RSD-02.

### P0 — CLI/toolchain coupling

Direct calls to `python`, `pio`, `platformio`, or Git from the UI make the application non-portable.

**Action:** RSD-02/RSD-03/RSD-04.

### P1 — Dynamic imports / native libraries

Packaging tools may omit dynamically imported modules or Qt/native components.

**Action:** dependency smoke test on clean Windows installation.

### P1 — Firmware artifact drift

A packaged UI can be portable while flashing an artifact produced from a different source/toolchain revision.

**Action:** release manifest with firmware/compiler versions and hashes.

### P1 — Mutable installation directory

Writing config/log/cache beside the executable can fail under protected installation locations.

**Action:** RSD-02 user-data contract.

### P2 — USB driver dependency

The application cannot eliminate an OS-level USB driver requirement when the selected ESP32/USB interface requires one. This must be identified explicitly rather than hidden as an application dependency.

**Action:** document supported hardware/driver matrix.

## 9. Acceptance tests for RSD-01

The following must become release-gate tests:

### Static

- [ ] No hard-coded developer filesystem paths in runtime code.
- [ ] No unclassified `subprocess` calls.
- [ ] No direct runtime dependency on `git`.
- [ ] No runtime dependency on globally installed `python`/`pio`.
- [ ] All runtime assets have explicit package locations.
- [ ] All compiler/deployment entry points are identifiable.

### Clean machine

- [ ] Launch from a path outside the repository.
- [ ] Launch without Python installed globally.
- [ ] Compile a representative RoboSim program.
- [ ] Detect a robot.
- [ ] Connect through serial.
- [ ] Perform bootstrap/first flash with packaged artifacts.
- [ ] Perform OTA with a provisioned robot.
- [ ] Execute recovery/backup workflow.
- [ ] Restart and retain user configuration/logs.

## 10. Implementation decision

RSD-01 establishes the boundary but does not yet replace the existing development toolchain.

The next implementation task is:

**RSD-02 — Runtime Path Isolation & Application-Owned Tool Resolution**

RSD-02 should first make runtime resource and executable resolution deterministic. Only after that should the project build a PyInstaller/Nuitka portable bundle.

This sequencing prevents packaging from masking architectural coupling and gives us a reproducible clean-machine acceptance test.