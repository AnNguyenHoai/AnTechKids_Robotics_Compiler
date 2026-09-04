# H23-A — Motor Output Audit

## Scope

This task does not change deadband/PWM behavior. It establishes the current ownership boundary before H23-B changes motor mapping.

## Actual output paths found

### Normal direct motion

`Application / RobotAPI caller -> setMotorsDirect() or SetMotorSpeed() -> _setMotors() -> _setMotorsRaw() -> LEDC PWM`

### Line following

`Line sensor -> LineFollower::update() -> RobotAPI::setMotorsDirect() -> _setMotors() -> _setMotorsRaw() -> LEDC PWM`

### Heading control

Heading-generated commands ultimately use the same `_setMotors()` calibration boundary before raw output.

### Raw stop / safety paths

Several stop and safety paths call `_setMotorsRaw(0, 0)` directly. This is intentional because zero is an absolute stop command and must bypass calibration.

## H23-A ownership contract

### Domain 1 — Logical motor command

All behavior/controller code uses `[-100, 100]`.

- `0` = stop
- positive = forward
- negative = reverse
- magnitude = logical speed request

### Domain 2 — Calibration boundary

Only `RobotAPI::_setMotors()` applies:

- `speedScale`
- `leftMotorScale`
- `rightMotorScale`

No caller may pre-apply calibration or inverse calibration before calling `setMotorsDirect()` / `SetMotorSpeed()`.

### Domain 3 — Raw output

`_setMotorsRaw()` owns:

- command clamp
- PWM conversion
- direction pins
- hardware PWM diagnostic gate

It must not know line-following or behavior semantics.

## Source findings to preserve for H23-B/C

1. Current code maps `abs(speed) * pwmPerSpeed` directly to PWM.
2. The observed hardware dead zone means this direct 0–100 model is not a valid physical speed model.
3. Calibration is currently multiplicative and can reduce a non-zero logical command into the motor stall region.
4. `motor calib test` currently pre-applies calibration before calling `setMotorsDirect()`, which causes calibration to be applied again. This is intentionally left for H23-C because H23-A only establishes ownership and traceability.
5. LineFollower H22 is already intended to output command-domain values and should not own calibration.

## H23-B entry criteria

H23-B must replace the direct logical-speed-to-PWM assumption with a single motor mapper while preserving this ownership boundary.
