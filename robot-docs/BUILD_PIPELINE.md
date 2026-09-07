# Build Pipeline

## Overview

The canonical deployment pipeline transforms a RoboSim source file into firmware ready for deployment to the ESP32.

## Canonical stages

```text
RoboSim Source (.py)
│
▼
Frontend (Rewrite)
│
▼
Standard Robot API (.rewrite.py)
│
▼
Compiler
│
▼
Bytecode / Header (.h)
│
▼
Deployment Manifest + validation
│
▼
Firmware Build (PlatformIO)
│
▼
Deploy (`tools/deploy_robot.py`)
│
├── USB (recovery / first install)
└── OTA (normal classroom deployment)
```

## Canonical deployment entry point

Use `tools/deploy_robot.py` for the complete student-program deployment flow. It owns rewrite, compile, capability inference, manifest creation/validation, firmware build, USB/OTA upload, and OTA health verification.

```bash
python tools/deploy_robot.py --input <source.py> --mode build
python tools/deploy_robot.py --input <source.py> --mode usb --port COM4 --ssid <ssid> --wifi-password <password>
python tools/deploy_robot.py --input <source.py> --mode ota --robot robot-XXXXXX.local --ssid <ssid> --wifi-password <password>
```

`tools/flash.py` remains a low-level/recovery primitive. It is not the canonical student-facing deployment workflow.

## Stage details

### 1. Frontend (Rewrite)

- **Input**: RoboSim Python source
- **Process**: Transforms RoboSim-specific API calls to Standard Robot API.
- **Output**: `.rewrite.py`
- **Tool**: `tools/rewrite.py`

### 2. Compiler

- **Input**: `.rewrite.py`
- **Process**: Performs semantic analysis, generates bytecode, and emits a C++ header.
- **Output**: `program.h` and `compile_report.json`
- **Tool**: `tools/compile.py`

### 3. Deployment contract

- **Input**: compiled artifact and target information
- **Process**: validates target/capabilities and artifact integrity.
- **Output**: `deployment_manifest.json`
- **Tool**: `tools/deployment_contract.py`

### 4. Firmware build and deployment

- **Tool**: `tools/deploy_robot.py`
- **USB**: supported as first-install/recovery path.
- **OTA**: supported as the normal network deployment path.

## Artifacts

All intermediate and final artifacts are stored in a structured `build/<project_name>/` directory:

```text
build/
└── <project_name>/
    ├── <project_name>.rewrite.py
    ├── program.h
    ├── compile_report.json
    └── deployment_manifest.json
```

## Golden Build Validation

A separate tool `tools/golden_build.py` runs the golden programs under `robot-platform/golden/` and produces a summary report.

## Architecture rule

There is one supported student-facing path: `tools/deploy_robot.py`. Do not reintroduce parallel deployment scripts or runtime implementations. Low-level tools may remain as internal primitives when they are required by the canonical flow or recovery procedures.
