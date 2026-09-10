# RoboStudio Distribution Audit

## 1. Objective

Define a portable Windows distribution for RoboStudio that can run on a clean target machine without requiring the developer toolchain to be installed separately.

The audit distinguishes **development dependencies** from **end-user runtime dependencies**. It does not change the compiler or robot firmware contracts.

## 2. Current architecture to audit

```text
RoboStudio UI
    |
    +-- compiler / compiler artifacts
    |
    +-- robot deployment
    |      +-- USB/serial
    |      +-- bootstrap / firmware upload
    |      +-- OTA
    |
    +-- configuration / assets
    |
    +-- local project files
```

## 3. Distribution boundary

### Must be inside the RoboStudio distribution

- RoboStudio application entry point and all application Python/runtime code required by the UI.
- RoboSim compiler runtime required to compile user programs.
- Robot deployment runtime required for supported USB/serial and OTA operations.
- Firmware/artifact assets that are part of the supported release flow.
- Application assets and default configuration.
- A private writable data/config directory; the application must not require a repository checkout or a developer working directory.

### Development-only dependencies

These should not be prerequisites for an end-user machine:

- Git.
- Python installed globally.
- PlatformIO installed globally.
- ESP32 compiler/toolchain installed globally.
- Developer-only test runners and source-control tooling.

PlatformIO and its ESP32 toolchain may remain build-time dependencies for producing release artifacts, but they should not be exposed as installation prerequisites to teachers/students.

## 4. Packaging candidates

| Approach | Fit | Main issue |
|---|---:|---|
| PyInstaller folder bundle | High for first release | Need explicit handling of dynamic imports and external tools |
| PyInstaller one-file | Medium | Startup/extraction and external executable handling are less convenient |
| Nuitka standalone | High | More build complexity, but strong isolation from system Python |
| Tauri/Electron rewrite | Low for immediate milestone | Large UI/runtime migration; unnecessary before dependency boundary is proven |
| Browser app | Low for USB-first workflow | Local serial/USB access needs an additional agent or browser-specific constraints |

**Recommendation:** first deliver a **Windows portable directory bundle**. Do not require a literal single executable. Once the bundle is stable, an installer can be added without changing the runtime architecture.

## 5. Required runtime contract

RoboStudio should resolve resources relative to its installation/application root, never relative to the developer checkout and never through the machine's PATH.

The runtime contract should provide these logical services:

```text
CompilerService
DeploymentService
SerialService
OTAService
FirmwareArtifactService
ConfigService
```

The UI should call these services rather than invoking `python`, `pio`, or other developer commands directly.

## 6. Critical deployment finding

The current bootstrap/upload flow demonstrates why packaging must be treated as an application concern. A command such as:

```text
python -m platformio run -e esp32dev_bootstrap -t upload
```

is valid in the development environment but is **not** an acceptable end-user prerequisite.

The release design should therefore choose one of these implementations:

1. bundle the required PlatformIO/esptool runtime privately and invoke it through an application-owned absolute path; or
2. extract the minimal upload capability into an application-owned deployment executable/library.

Option 1 is the lower-risk first implementation because it preserves the existing upload behavior. Option 2 is the longer-term product architecture because it removes PlatformIO from the user-facing runtime boundary.

## 7. Configuration and data

Portable distribution must separate immutable application files from mutable user data:

```text
RoboStudio/
  RoboStudio.exe
  app/
  runtime/
  firmware/
  assets/

%APPDATA%/RoboStudio/
  config/
  projects/
  logs/
  cache/
```

If a truly portable USB distribution is required later, provide a portable-data mode explicitly rather than silently writing beside the executable.

## 8. Clean-machine acceptance criteria

A release candidate is acceptable only if, on a Windows machine with no development environment installed:

- RoboStudio starts without Python being installed globally.
- The UI opens all supported workspaces/pages.
- A RoboSim program compiles.
- A supported robot can be discovered.
- USB/serial connection works.
- Bootstrap/first-flash works through the packaged deployment runtime.
- OTA works when the robot is already provisioned for OTA.
- Logs and user configuration are writable without administrator privileges.
- No operation requires `git`, `pio`, `python`, or an ESP32 compiler to be present on PATH.

## 9. Recommended implementation phases

### Phase D1 — Dependency inventory

Create a machine-readable inventory of imports, subprocess commands, executable names, data files, firmware files, and environment variables used by RoboStudio.

### Phase D2 — Runtime abstraction

Introduce application-owned service boundaries for compiler, deployment, serial, OTA, and artifacts. All executable paths must be resolved from the packaged runtime directory.

### Phase D3 — Portable build

Produce a Windows standalone directory bundle and a smoke-test script that runs from a clean path outside the repository.

### Phase D4 — Clean-machine validation

Validate startup, compile, discover, USB flash, OTA, logging, and recovery on a clean Windows machine.

### Phase D5 — Installer

Only after D1-D4 are stable, create an installer and optional desktop shortcut/file associations.

## 10. Immediate next engineering task

**RSD-01 — RoboStudio Runtime Dependency Inventory**

Deliver:

- exact RoboStudio entry point;
- all Python modules imported at runtime;
- all subprocess/external executable calls;
- all paths currently tied to the repository/developer machine;
- all runtime data/assets/firmware dependencies;
- USB/serial/OTA dependencies;
- proposed packaged paths;
- clean-machine smoke-test checklist.

This inventory must be completed before selecting PyInstaller/Nuitka configuration so packaging does not hide unresolved runtime dependencies.
