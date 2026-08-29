# H25-B — Hardware / Devices Tab

## Scope
H25-B connects the H25-A Hardware Configuration Domain to RoboStudio UI.

## Delivered
- Added a `Hardware` tab to the main `QTabWidget`.
- Devices are grouped by registry category: Motion, Sensors, Expansion.
- Checkbox state is loaded from `config/hardware.json`.
- `Apply Configuration` persists the selected state through `HardwareConfigService`.
- `Reload` discards unsaved UI changes and reloads persisted configuration.

## Source of truth
The UI does not own device metadata. Device definitions remain in:

`domain/device_registry.py`

Persisted state remains in:

`config/hardware.json`

## Explicitly out of scope
- Firmware macro generation.
- Build-time feature guards.
- Profile selection.
- Runtime device detection.

Those remain for subsequent H25 tasks.
