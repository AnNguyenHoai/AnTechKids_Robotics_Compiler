# H23-C — Calibration & Diagnostic Fix

## Scope

H23-C completes the calibration ownership cleanup started by H23-A/B.

### Fixed

1. `motor calib test <speed>` no longer pre-applies calibration before calling `RobotAPI::setMotorsDirect()`.
2. Calibration settings are saved immediately after `set left`, `set right`, and `reset`.
3. `motor calib show` and `motor calib test` now display H23-B mapped outputs rather than the obsolete pre-mapped `effective` formula.
4. Added change-triggered motor mapping diagnostics.

## Single-calibration contract

```
Serial / Application logical command
        ↓
RobotAPI::setMotorsDirect()
        ↓
RobotAPI::_setMotors()
        ↓
MotorOutputMapper (speedScale + motor scale + minDrive)
        ↓
_setMotorsRaw()
        ↓
PWM
```

No caller may multiply by `leftMotorScale`, `rightMotorScale`, or `speedScale` before entering `setMotorsDirect()`.

## Diagnostic commands

- `motor diag on`
- `motor diag off`
- `motor diag status`

When enabled, output is emitted only when logical or mapped motor values change. This avoids per-cycle serial spam.

Example:

```
[MOTOR-DIAG] logical L=50 R=80 | scale global=1.000 L=0.900 R=1.000 | minDrive=65 | mapped L=78 R=93 | pwm L=198 R=237
```

## Validation checklist

1. `motor calib reset`
2. `motor calib test 10`
3. `motor calib test 50`
4. `motor calib set left <value>`
5. Repeat `motor calib test 50`
6. `motor diag on`
7. `speed 50 80`
8. Confirm the diagnostic shows calibration once and mapped outputs above `minDrive` for non-zero commands.
