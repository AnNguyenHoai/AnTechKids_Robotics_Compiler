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

This validates the release package and prints its manifest metadata. `--json` is available on all commands for machine-readable output.

## Release contract

```text
production inputs
    -> RSD-17 distribution
    -> RSD-09 deterministic ZIP
    -> RSD-18 provenance
    -> RSD-20-P dependency/portability proof
    -> release-ready artifact
```

The CLI intentionally does not install packages, download runtimes, mutate the developer's environment, or fall back to host Python/PlatformIO. A missing required input is a release failure.
