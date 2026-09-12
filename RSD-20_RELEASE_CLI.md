# RSD-20 — Release CLI

## Purpose

RSD-20 provides the canonical command-line entrypoint for production RoboStudio release operations. It does not discover Python, PlatformIO, or other developer tools from the host. Production build inputs remain explicit and are passed to the RSD-20-P.1 assembly boundary.

## Commands

### Build

```powershell
python -m tools.release_cli build `
  --executable <production-RoboStudio.exe> `
  --runtime-bin <portable-python-runtime> `
  --runtime-platformio <application-owned-platformio-runtime> `
  --runtime-resources <runtime-resources> `
  --version-file <VERSION> `
  --output <release-output>
```

The command assembles the distribution, creates the deterministic ZIP, writes provenance, runs portable dependency proof, and fails if the resulting release is not portable.

### Verify

```powershell
python -m tools.release_cli verify <RoboStudio-<version>-Windows.zip>
```

This validates the release artifact and runs the RSD-20-P portable proof. Exit code is `0` only when the proof passes.

### Inspect

```powershell
python -m tools.release_cli inspect <RoboStudio-<version>-Windows.zip>
```

This validates the release package and prints its manifest metadata.

### Accept

```powershell
python -m tools.release_cli accept <RoboStudio-<version>-Windows.zip>
```

This runs the final automated clean-machine acceptance boundary defined by RSD-16: validate the release, relocate it to a fresh temporary directory, execute the application-owned portable Python runtime from an external working directory, and prove hostile host Python/PlatformIO settings do not replace the packaged runtime. `--timeout` controls the bounded runtime probe and `--json` emits the machine-readable acceptance report.

## Release contract

```text
production inputs
    -> RSD-17 distribution
    -> RSD-09 deterministic ZIP
    -> RSD-18 provenance
    -> RSD-20-P dependency/portability proof
    -> RSD-20 release CLI
    -> RSD-16 automated clean-machine acceptance
    -> hardware / OTA qualification
```

The CLI intentionally does not install packages, download runtimes, mutate the developer's environment, or fall back to host Python/PlatformIO. A missing required input is a release failure.

Automated acceptance does not replace the final human qualification of the actual shipped ZIP: GUI startup, USB/serial hardware, firmware upload, and OTA remain environment-specific release gates.
