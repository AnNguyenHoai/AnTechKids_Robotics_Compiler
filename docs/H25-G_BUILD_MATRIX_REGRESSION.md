# H25-G — ON/OFF Build Matrix + Regression

## Goal
Prevent hardware configuration regressions by testing every registered device in both ON and OFF states.

## Matrix
For every `DeviceRegistry` device, the regression matrix verifies:

- `device = OFF` generates `ROBOT_FEATURE_* 0`
- `device = ON` generates `ROBOT_FEATURE_* 1`
- all generated macros remain deterministic
- representative program APIs pass when required hardware is enabled
- representative program APIs are rejected when required hardware is disabled

## Scope
The RoboStudio regression suite is intentionally toolchain-independent. It validates:

`HardwareConfig -> generated_device_config.h -> program dependency validation`

Firmware compilation of the generated header remains a separate target because the local Python test environment does not contain the ESP32 Arduino toolchain.

## Run

```bash
cd robostudio
python -m pytest tests/test_hardware_build_matrix.py -q
```

Or run the full regression suite:

```bash
python -m pytest tests -q
```
