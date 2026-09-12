# H26-L — Capability-aware RoboStudio

## Goal

Make RoboStudio aware of the selected execution target and the canonical H26-K
capability profile before a build starts.

## Delivered

- Added a target selector to the Program tab.
- Targets are loaded from the canonical `packages/robot-isa/target_profiles.json`
  data rather than being hard-coded in the UI.
- Added a UI-facing target capability service that evaluates program requirements
  against the selected target.
- Reused `ProgramCapabilityAnalyzer` as the source-level program API view.
- Mapped recognized RoboSim API calls to the canonical capability IDs from the
  H26-E/H26-K model.
- The Program tab now shows:
  - selected target;
  - target description;
  - required hardware status from H25-J;
  - required canonical capabilities and target support status.
- Compilation is disabled when the selected target cannot satisfy the program's
  canonical capability requirements or the configured hardware requirements.
- Existing hardware capability validation remains authoritative at build time;
  H26-L adds an earlier target-aware UX signal and does not replace it.

## Boundary

The target selector is a RoboStudio build-time intent. H26-L does not perform
physical board auto-detection and does not change compiler opcodes, VM dispatch,
or firmware behavior.

## Validation

Run from the repository root:

```bash
python tests/h26_l/run_h26_l.py
python run_all_tests.py
```
