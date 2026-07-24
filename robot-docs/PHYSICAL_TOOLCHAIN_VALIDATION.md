# Physical Toolchain Validation

Version: 1.0  
Date: 2026-07-24  
Status: READY FOR PHYSICAL EXECUTION

## Overview

This document validates the complete toolchain from RoboSim Python source to physical robot execution.

## Pipeline
RoboSim Python (.py)
│
▼
Frontend (rewrite.py)
│
▼
Standard Robot Python (.rewrite.py)
│
▼
Compiler (compile.py)
│
▼
program.h
│
▼
Firmware Build (PlatformIO)
│
▼
ESP32 Firmware (.bin)
│
▼
Flash (pio run -t upload)
│
▼
ESP32 Runtime
│
▼
Robot Hardware

text

## Commands Used

### 1. Rewrite
```bash
python tools/rewrite.py --input examples/physical/001_forward.py --output build/physical/001_forward/001_forward.rewrite.py
2. Compile
bash
python tools/compile.py --input build/physical/001_forward/001_forward.rewrite.py --output build/physical/001_forward/program.h --report build/physical/001_forward/compile_report.json
3. Copy header to platform
bash
cp build/physical/001_forward/program.h robot-platform/main/src/Application/generated_program.h
4. Build firmware
bash
pio run -d robot-platform
5. Flash
bash
pio run -t upload -d robot-platform --upload-port COM5
6. Monitor serial
bash
pio device monitor -b 115200 -p COM5
Physical Test Results
Program	Rewrite	Compile	Firmware Build	Flash	VM Execute	Physical Behavior
001_forward.py	PASS	PASS	PASS	PASS	PASS	PENDING
002_backward.py	PASS	PASS	PASS	PASS	PASS	PENDING
003_stop.py	PASS	PASS	PASS	PASS	PASS	PENDING
004_forward_wait_stop.py	PASS	PASS	PASS	PASS	PASS	PENDING
005_turn_left.py	PASS	PASS	PASS	PASS	PASS	PENDING
006_turn_right.py	PASS	PASS	PASS	PASS	PASS	PENDING
(Update after physical execution)

Serial Logs
See artifacts/physical/ for captured logs.

Timing Audit
rcu.SetWaitForTime(seconds) → wait(seconds) (no conversion; unit is milliseconds as per RoboSim behavior).

rcu.SetMoveRunSecond(direction, speed, seconds) → forward(speed); wait(seconds*1000); stop() (converts seconds to milliseconds).

This is consistent with the actual implementation and all tests pass.

Issues Found
(To be filled after physical testing)

Regression Protection
All fixes are covered by regression tests. Run:

bash
python run_all_tests.py