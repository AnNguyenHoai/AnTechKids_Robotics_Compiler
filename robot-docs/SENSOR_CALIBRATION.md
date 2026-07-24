
### `robot-docs/SENSOR_CALIBRATION.md`

```markdown
# Sensor Calibration

## Calibration Parameters
- `lightGain`: multiplier for light sensor raw value
- `lightOffset`: offset added
- `lineInverted`: invert line sensor logic
- `ultrasonicTimeoutMs`: timeout for ultrasonic pulse

## Procedure
1. Place robot in controlled environment.
2. Run `006_sensor_monitor.py` and observe raw values.
3. Adjust parameters using Serial commands (future).
4. Save calibration via `saveSensorConfigToStorage()` (placeholder).