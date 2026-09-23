# RoboStudio Phase 2 — Production UX

## Goal

Build on Phase 1 responsive safety and reduce cognitive load for teachers/students without changing compiler, discovery, first-flash, OTA, hardware, or serial service contracts.

## Daily golden path

The Robot tab is organized around the task users perform most often:

1. Select a known robot.
2. Confirm connection credentials.
3. Run the current program.

One-time setup and diagnostics are secondary actions rather than permanent peers of the Run action.

## First-flash setup flow

`Setup New Robot` opens a two-step flow:

1. **Network** — Wi-Fi SSID, optional Wi-Fi password, robot/OTA password.
2. **USB Flash** — select COM port, refresh USB inventory, flash robot.

The former separate `Generate Config` action is no longer exposed. RoboStudio generates bootstrap configuration immediately before the existing first-flash deployment path is invoked. A stale previous configuration is never reused.

The existing `RobotTab` service-facing field names remain mapped to the dialog widgets so deployment behavior and runtime contracts stay inherited.

## Diagnostics

Serial Console and Deployment Log are now tabs inside one Diagnostics area. They no longer compete vertically at the same time.

- `Serial Console` is for direct robot diagnostics/commands.
- `Deployment Log` contains PlatformIO/deployment output.

## Information hierarchy

### Robot

- `My Robot` summary card
- semantic status badge (`Online · Ready`, `Needs attention`, `Offline`)
- robot technical details collapsed by default
- primary `RUN ON ROBOT` action
- `Setup New Robot` secondary action

### Program

- `Compile Program` is the primary action
- capability/target detail text is collapsed under `Show readiness details`
- `Open Firmware` is moved to the `Advanced` menu

### Navigation

Primary tabs follow the daily task order:

`Program → Robot → Hardware`

## Design-system primitives

Central presentation tokens live in `robostudio/ui/theme.py` and reusable UI components in `robostudio/ui/components.py`.

Current primitives:

- semantic `StatusBadge`
- `DisclosureButton`
- `SummaryCard`
- primary/secondary button styles
- shared text, border, surface, success/warning/error tokens

The design system is intentionally modest and desktop-native; it is a consistency contract, not a decorative theme.

## Regression gate

`tests/ui_production/run_ui_production.py` verifies:

- guided first-flash is exactly two user steps;
- bootstrap generation is hidden from the user;
- setup flow reaches USB inventory and one Flash action;
- semantic status components retain text + tone meaning;
- Robot details start collapsed;
- diagnostics are tabs;
- Robot is second in primary navigation;
- firmware editing is under Advanced;
- Program readiness details start collapsed.

## Phase 2 acceptance

- Everyday Run workflow does not require viewing first-flash controls.
- `Generate Config` is not a user-facing action.
- First Flash still calls the same deployment services and preserves explicit COM selection.
- Serial and deployment logs remain available but do not consume space simultaneously.
- Technical robot details are available on demand.
- Program/Robot/Hardware ordering reflects the common user flow.
- Phase 1 responsive behavior remains intact.
