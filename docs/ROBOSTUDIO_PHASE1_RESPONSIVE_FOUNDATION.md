# RoboStudio Phase 1 — Responsive Foundation

## Goal

Make the existing RoboStudio desktop UI remain usable under resize and Windows DPI pressure without changing compiler, deployment, discovery, hardware configuration, or serial-console behaviour.

## Responsive contract

The presentation layer follows one rule:

- when horizontal space becomes constrained, complex workspaces stack instead of forcing controls into one row;
- when vertical space becomes constrained, long content scrolls instead of being clipped;
- code/log text areas keep their own scrolling behaviour;
- business services and workflow state remain inherited from the existing widgets.

Central breakpoints live in `robostudio/ui/responsive.py`:

- Narrow: `<= 899 px`
- Compact: `900..1199 px`
- Wide: `>= 1200 px`
- Robot workspace switches from side-by-side to stacked when its own available width falls below `1080 px`.

## Implemented surfaces

### Program

- Main window minimum reduced from the previous near-1000px floor to `760x540`.
- Program content is vertically scrollable.
- Target description moved to its own row.
- Code editor and build output minimum heights are reduced and use expanding size policies.

### Hardware

- Existing `HardwareTab` behaviour is preserved through subclassing.
- Device configuration is vertically scrollable.
- Device descriptions are stacked under their checkboxes, so long text does not compete horizontally with the control.

### Robot

- Existing `RobotTab` behaviour is preserved through subclassing.
- The main Deployment/Console splitter is adaptive: side-by-side when wide, stacked when compact.
- Deployment workflow is vertically scrollable.
- First-flash USB selection and actions use separate rows instead of one overloaded horizontal row.
- Serial Console connection controls use two rows and no 230px hard minimum on the COM selector.
- Serial and deployment-log panes use a vertical splitter with smaller safe minimum heights.

## Regression gate

`robostudio/tests/test_responsive_layout.py` verifies:

- breakpoint classification;
- adaptive splitter orientation;
- removal of the serial toolbar hard-width pressure;
- Hardware tab scrolling contract.

## Manual acceptance matrix

The production UI should remain usable at:

| Window | Expected mode |
| --- | --- |
| 1440x900 | Wide |
| 1200x800 | Wide |
| 1100x700 | Compact |
| 960x680 | Compact |
| 820x600 | Narrow |

For every size:

- no widget overlap;
- no button/text collision;
- no application-level horizontal scrollbar;
- long content has a vertical scroll path;
- code/log panes remain independently scrollable;
- Robot Deployment/Console stacks when there is not enough width;
- COM descriptions do not force the Serial toolbar wider than its panel.

Windows 125% and 150% display scaling should be included in release smoke testing.
