# H23-D — Line Response Latency Trace

Purpose: measure the synchronous software path from line sampling to motor-output submission.

Enable with `line diag on`. Logs only when the 3-channel line mask changes.

Fields:
- `loop`: time between consecutive `RobotAPI::LineBasis()` calls.
- `sensor`: `GetTraceRaw(1)` duration.
- `control`: `LineFollower::update()` duration.
- `output`: `setMotorsDirect()` duration, including mapping and low-level PWM submission.
- `total`: sensor read completion path through motor submission.

Interpretation:
- Large `loop` => VM/API invocation cadence is slow.
- Large `sensor` => sensor acquisition is slow.
- Large `control` => line algorithm is slow.
- Large `output` => motor software path is slow.
- Small total with poor physical tracking => investigate motor/mechanical response rather than software latency.

This diagnostic does not measure physical motor acceleration or vehicle inertia; it measures software response and PWM command submission.
