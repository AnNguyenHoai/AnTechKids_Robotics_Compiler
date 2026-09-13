# RSD-21.3 — Production Artifact Boundary Enforcement

Production ZIP boundary is now executable. RoboStudio + Compiler + application-owned resources/dependencies are packaged. Python and PlatformIO are target-machine prerequisites and are not bundled.

The boundary gate rejects runtime/bin, runtime/platformio, .venv, .pio, and penv payloads. Production compatibility metadata records host prerequisites as not bundled.

Regression coverage: tests/rsd_21_3/run_rsd_21_3.py
