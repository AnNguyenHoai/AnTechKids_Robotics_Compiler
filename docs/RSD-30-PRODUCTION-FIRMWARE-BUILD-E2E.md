# RSD-30 — Production Firmware Build E2E

## Purpose

Prove that a production RoboStudio ZIP can build the packaged ESP32 firmware using only the application-owned Python and PlatformIO runtime, without depending on developer-repository state, host PlatformIO state, or host Python.

## Qualification flow

```text
Production ZIP
    ↓
Safe extraction
    ↓
Production artifact closure validation
    ↓
firmware/robot-platform (read-only template)
    ↓
isolated writable firmware workspace
    ↓
optional generated_program.h
    ↓
runtime/bin/python.exe -m platformio run -e <environment>
    ↓
firmware.bin + SHA-256 + build evidence
```

## Contract

1. The system under test is the extracted production ZIP, not the repository checkout.
2. The build must execute through `runtime/bin/python.exe`.
3. PlatformIO core, platforms, and packages must resolve from `runtime/platformio`.
4. PlatformIO writable state must be outside the packaged firmware template and outside the packaged runtime.
5. The firmware template is copied to a temporary writable workspace before build.
6. Generated student-program headers are installed only into the writable workspace.
7. The supported production environments are `esp32dev`, `esp32dev_bootstrap`, and `esp32dev_ota`.
8. The build must produce a non-empty `firmware.bin`.
9. The report records the selected environment, bundled runtime paths, closure evidence, command, output size, and SHA-256.
10. Host `PLATFORMIO_HOME` is ignored and host Python/PlatformIO resolution is never used as the build command.
11. The packaged firmware template and packaged PlatformIO runtime must remain free of `.pio` build state.
12. This qualification does not claim USB upload, OTA deployment, or physical robot behavior; those are separate release gates.

## Tool

`tools/production_firmware_e2e.py` implements the contract and can be run on Windows with a real production ZIP:

```text
python tools/production_firmware_e2e.py --artifact RoboStudio-<version>-Windows.zip --environment esp32dev --report production-firmware-e2e.json
```

The `python` used to launch the harness is only the qualification harness interpreter. The actual firmware build command is always the extracted artifact's `runtime/bin/python.exe`.

## Evidence

A successful report uses schema `antechkids.robostudio.production-firmware-build-e2e` version 1 and contains a non-empty firmware size and SHA-256 digest.

## Limitation

The repository does not contain the actual Windows application-owned Python/PlatformIO runtime payload, so repository-only tests cannot honestly claim a real firmware build. The release gate is complete only after the harness is executed against the actual production ZIP on Windows and produces the required evidence.
