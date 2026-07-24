# Perception Validation

## Validation Framework
Run `python robot-platform/validation/sensor_validation.py` to execute all golden sensor programs.

## Golden Programs
| Program | Description |
|---------|-------------|
| 001_touch_stop.py | Stop when touch sensor pressed |
| 002_line_detect.py | Stop when line detected |
| 003_obstacle_stop.py | Stop when obstacle < 20cm |
| 004_light_trigger.py | Trigger on light level |
| 005_color_detect.py | Placeholder |
| 006_sensor_monitor.py | Monitor all sensors |

## Acceptance Criteria
- Each program executes without crash.
- Expected behavior observed.
- Logs show sensor readings.
- Regression report generated.