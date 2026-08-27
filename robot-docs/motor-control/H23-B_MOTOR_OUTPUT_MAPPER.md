# H23-B — Motor Output Mapper

## Contract

All application layers issue logical motor commands in `[-100, 100]`.

- `0` is always a true stop.
- Any non-zero command is calibrated once.
- Any non-zero calibrated command is mapped into `[minSpeed, 100]`.
- The default `minSpeed` is `65`, based on the observed hardware stall boundary.

## Mapping

For a non-zero command:

1. Clamp logical command to `[-100, 100]`.
2. Apply `speedScale * motorScale` once in the logical domain.
3. Map the resulting magnitude from `1..100` into `minSpeed..100`.
4. Apply direction sign.
5. Convert the mapped speed to PWM in `_setMotorsRaw()`.

## Ownership

`MotorOutputMapper` is the only H23-B component that combines calibration with minimum-drive mapping.

`LineFollower`, heading control, behaviors and serial callers must not pre-apply calibration.

## Important

The existing `minSpeed` persisted value is now interpreted as the minimum physical run-domain speed. Old stored values of `0` will preserve `0` and disable the guard until recalibrated/reset. A later migration may be needed if deployed robots already persist `0`.
