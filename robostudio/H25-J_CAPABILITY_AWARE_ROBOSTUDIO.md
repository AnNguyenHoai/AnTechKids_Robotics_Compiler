# H25-J — Capability-aware RoboStudio

## Goal

Make RoboStudio aware of the hardware capability contract while editing and
selecting examples, before the user starts a build.

## Delivered

- Added `ProgramCapabilityAnalyzer` as the single program-level capability view.
- The analyzer consumes `HardwareRequirementRegistry`, the same API → hardware
  mapping used by H25-F validation.
- The Program tab now shows:
  - hardware capabilities required by the current program;
  - capabilities enabled in `hardware.json`;
  - `READY` when all requirements are available;
  - `MISSING` when one or more required capabilities are disabled.
- Capability status refreshes whenever source code changes or Hardware
  Configuration is applied.
- Examples that require disabled hardware remain visible but are disabled and
  explain the missing capability in their tooltip.
- Existing H25-F compile-time rejection remains authoritative. H25-J adds an
  earlier UX signal; it does not replace validation or firmware guards.

## Boundary

RoboStudio uses the persisted hardware configuration as its current capability
view. The firmware runtime contract from H25-I remains the runtime source of
truth on the robot. This task does not invent physical auto-detection.

## Validation

Run from `robostudio`:

```bash
python -m pytest tests -q
```

Focused H25-J tests:

```bash
python -m pytest tests/test_program_capabilities.py -q
```
