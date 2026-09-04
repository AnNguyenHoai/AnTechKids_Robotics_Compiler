# H26-O — Legacy Cleanup & Canonical Path Consolidation

## Objective

Retire production-adjacent legacy paths now that the canonical compiler/runtime/deployment path has been validated on real ESP32 hardware.

## Canonical production path

The supported deployment path is:

```text
Student RoboSim source
  -> tools/deploy_robot.py
  -> rewrite.py
  -> compile.py
  -> deployment manifest validation
  -> firmware build
  -> USB or ESP32 OTA upload
  -> robot health verification (OTA mode)
```

`tools/deploy_robot.py` is the single host entry point for normal deployment. `tools/flash.py` remains an internal/recovery primitive and is not a second student-facing deployment workflow.

## Retired legacy paths

The following obsolete paths are removed by H26-O:

- `robot-platform/legacy/runtime_cpp_prototype/` — historical parallel C++ runtime/execution-engine implementation.
- `robot-platform/deploy.py` — older deployment script that bypassed the current manifest/OTA flow.
- `robot-platform/deploy_program.py` — sample source used only by the retired deployment script.

The legacy runtime was previously explicitly outside the PlatformIO production source filter. The real hardware validation of the canonical runtime/deployment path now satisfies the prerequisite for deletion.

## Cleanup rule

Future features must target canonical ownership under `robot-platform/main/` and the root `tools/` deployment pipeline. New parallel runtime, loader, dispatcher, or deployment implementations must not be introduced.

## Validation

H26-O must preserve the existing software regression suite and the hardware-proven Golden Path. No compiler bytecode semantics, VM behavior, or hardware behavior is intentionally changed by the cleanup.

## Status

- Canonical deployment path: established
- Real hardware validation: completed before H26-O
- Legacy prototype retirement: completed
- Legacy deployment script retirement: completed
- Student-facing deployment entry point: `tools/deploy_robot.py`
