# Toolchain Overview

This document describes the developer tools provided for building and deploying robot programs.

## Tools Directory

All tools are located in the `tools/` directory at the repository root.

### `rewrite.py`

Converts RoboSim source to Standard Robot API.

**Usage:**
```bash
python tools/rewrite.py --input <source.py> --output <output.rewrite.py>
```
Output: Only the `.rewrite.py` file. No compilation occurs.

### `compile.py`

Compiles Standard Robot API source (`.rewrite.py`) to a C++ header.

```bash
python tools/compile.py --input <source.rewrite.py> [--output <program.h>] [--report <report.json>]
```

If `--output` is omitted, the output is placed in `build/<basename>/program.h` and `build/<basename>/compile_report.json`.

### `build.py`

Full build pipeline: rewrite + compile.

```bash
python tools/build.py --input <source.py> [--build-dir <dir>] [--output <program.h>]
```

### `deployment_contract.py`

Creates and validates the deployment manifest, including target/capability compatibility and artifact integrity.

### `deploy_robot.py`

**Canonical one-click deployment entry point.** It owns the complete student-program flow: rewrite, compile, capability inference, manifest validation, firmware build, USB/OTA upload, and OTA health verification.

```bash
python tools/deploy_robot.py --input <source.py> --mode build
python tools/deploy_robot.py --input <source.py> --mode usb --port COM4
python tools/deploy_robot.py --input <source.py> --mode ota --robot robot-XXXXXX.local --ssid <ssid> --wifi-password <password>
```

### `flash.py`

Low-level firmware build/upload primitive retained for internal and recovery use. It is not a second student-facing deployment workflow.

### `physical_validation.py`

Performs the safe network-side physical-validation preflight. It does not replace real hardware acceptance testing.

### `golden_build.py`

Validates all golden programs by building each one and collecting statistics.

## Architecture Reminder

Frontend (`rewrite.py`) only generates `.rewrite.py`. Compiler (`compile.py`) only accepts `.rewrite.py`. The canonical student-facing deployment entry point is `deploy_robot.py`.

Do not add parallel runtime or deployment implementations when a canonical owner already exists.

## Regression Tests

After toolchain changes, run:

```bash
python run_all_tests.py
```
