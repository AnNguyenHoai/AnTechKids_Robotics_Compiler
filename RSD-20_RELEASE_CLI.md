# RSD-20 — Release CLI

## Purpose

RSD-20 provides the canonical command-line entrypoint for production RoboStudio release operations. Production releases contain the RoboStudio application and application-owned compiler/runtime resources. Python, PlatformIO, and hardware drivers are target-machine prerequisites and are not copied from the developer machine into the release.

## Commands

### Build

The production build command receives the application-owned build inputs required by the current assembly pipeline. Target-machine prerequisites are not installation payloads.

```powershell
python -m tools.release_cli build `
  --executable <production-RoboStudio.exe> `
  --runtime-bin <assembly-runtime-input> `
  --runtime-platformio <assembly-platformio-input> `
  --runtime-resources <runtime-resources> `
  --version-file <VERSION> `
  --output <release-output>
```

### Verify

```powershell
python -m tools.release_cli verify <RoboStudio-<version>-Windows.zip>
```

This validates the release artifact and runs the RSD-20-P portable dependency proof. The proof is an artifact/dependency gate; it is not a claim that host prerequisites have been installed.

### Inspect

```powershell
python -m tools.release_cli inspect <RoboStudio-<version>-Windows.zip>
```

This validates the release package and prints its manifest metadata.

### Accept — target machine

For the real production-user model, validate the target machine prerequisites with:

```powershell
python -m tools.release_cli accept <RoboStudio-<version>-Windows.zip> `
  --target-machine `
  --prerequisite-scope compile
```

For hardware deployment:

```powershell
python -m tools.release_cli accept <RoboStudio-<version>-Windows.zip> `
  --target-machine `
  --prerequisite-scope hardware
```

RSD-21.4 checks the declared host prerequisites without installing or modifying them. `compile` checks Python. `hardware` checks Python and PlatformIO automatically and records the board-specific ESP32/USB driver as a manual prerequisite.

Use `--report <path>` to write machine-readable target-machine qualification evidence and `--json` for JSON stdout.

### Accept — legacy portable-runtime gate

The existing command remains available for the legacy RSD-16 clean-machine runtime boundary:

```powershell
python -m tools.release_cli accept <RoboStudio-<version>-Windows.zip>
```

This mode validates the bundled-runtime model and is retained for historical regression coverage. It is not the target-user prerequisite model introduced by RSD-21.4.

## Release contract

```text
production artifact
    -> RSD-20 integrity/structure verification
    -> RSD-20-P dependency proof
    -> RSD-18 provenance
    -> RSD-21.4 target-machine prerequisite qualification
    -> RoboStudio + Compiler E2E
    -> hardware / OTA qualification
```

The target-machine qualification command never installs packages, downloads runtimes, mutates the developer environment, or falls back to a different tool when a declared prerequisite is missing. A missing automatically checkable prerequisite is a qualification failure.

GUI startup, USB/serial hardware, firmware upload, and OTA remain environment-specific production gates and are not silently claimed by the prerequisite check.
