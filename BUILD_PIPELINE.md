# Build Pipeline

## Overview

The Robot Development Platform build pipeline transforms a RoboSim source file into a binary firmware image ready for deployment.

## Stages

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
Firmware Build (PlatformIO)
│
▼
Flash (ESP32)

## Stage Details

### 1. Frontend (Rewrite)

- **Input**: RoboSim Python source (e.g., `program.py`)
- **Process**: Parses AST, transforms RoboSim-specific API calls (`rcu.SetMoveRun`, etc.) to Standard Robot API (`forward`, `backward`, etc.)
- **Output**: Standard Robot API Python file with `.rewrite.py` extension
- **Tool**: `tools/rewrite.py`
- **Note**: Frontend does **not** compile; it only produces a `.rewrite.py` file.

### 2. Compiler

- **Input**: `.rewrite.py` file
- **Process**: Parses Standard Robot API, performs semantic analysis, generates bytecode, and emits a C++ header containing the program data.
- **Output**: `program.h` and `compile_report.json`
- **Tool**: `tools/compile.py`
- **Note**: Compiler accepts only `.rewrite.py` files; it knows nothing about the original RoboSim source.

### 3. Firmware Build

- **Input**: `program.h`
- **Process**: Copies the header into the ESP32 firmware project and builds the firmware using PlatformIO.
- **Output**: Firmware binary (`.bin`)
- **Tool**: `tools/flash.py` (build + upload)

### 4. Flash

- **Input**: Firmware binary
- **Process**: Uploads the firmware to the ESP32 via serial.
- **Tool**: `tools/flash.py`

## Artifacts

All intermediate and final artifacts are stored in a structured `build/` directory:
build/
<project_name>/
program.rewrite.py
program.h
compile_report.json

text

## Golden Build Validation

A separate tool `tools/golden_build.py` runs the entire pipeline on all golden programs (located in `robot-platform/golden/`) and produces a summary report.