# RSD-21.8 — Real RoboStudio ↔ Compiler Contract

> **RSD-22 authority notice:** This document defines the compiler/application contract only. RSD-23 owns application runtime packaging.

The production release exposes `compiler/robostudio_bridge.py` and the real compiler/frontend payload required by that bridge.

The production runtime now includes application-owned Python at `runtime/bin/python.exe` and application-owned PlatformIO at `runtime/platformio`. RoboStudio must resolve those components through the deterministic runtime path contract rather than PATH or user-local PlatformIO state.

RSD-24 remains the final clean Windows GUI qualification and H28 remains the real hardware E2E qualification.
