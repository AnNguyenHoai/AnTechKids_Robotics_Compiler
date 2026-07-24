# Motion Calibration

## Calibration Parameters
- **speedScale**: Overall speed multiplier (default 1.0).
- **leftMotorScale**: Compensation for left motor (default 1.0).
- **rightMotorScale**: Compensation for right motor.
- **turnCompensation**: Additional factor for turning speeds (affects turning radius).
- **pwmPerSpeed**: Maps speed (0-100) to PWM duty (0-255). Default 2.55.

## Procedure
1. Run the `forward` golden program and measure actual distance travelled in 1 second.
2. If distance is less than expected, increase `speedScale`; if more, decrease.
3. For turning, run `turn_left` and measure angle. Adjust `turnCompensation` to get 90° per second (approximate).

## Saving Calibration
Use `config save` to store current config (currently placeholder; future EEPROM support).