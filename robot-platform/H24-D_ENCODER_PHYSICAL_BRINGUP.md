# H24-D — Encoder Physical Bring-up & Calibration

## Scope
Physical validation support for JGA25-370 quadrature encoders. This task does not implement wheel PID.

## Pin contract
- Left A/B: GPIO34/GPIO35
- Right A/B: GPIO36/GPIO39
GPIO34-39 are input-only and do not provide internal pull-ups. Encoder outputs must provide valid logic levels.

## Serial workflow
1. `encoder show` at rest; counts should remain stable.
2. `encoder reset all`.
3. Turn each wheel forward by hand or run a low speed motor command; `encoder show` must change count.
4. Reverse; count sign must reverse. If logical forward is negative, use `encoder invert left 1` or `encoder invert right 1`.
5. Mark the wheel, reset the count, rotate exactly one wheel revolution, read the absolute count. Repeat 3 times and use the stable decoded count.
6. Set with `encoder cpr <left> <right>`.
7. Run the wheel at a steady command and verify `cps`/`rpm` are non-zero and stable.

## Important
- CPR values are runtime only in this task; persistence is intentionally deferred until physical values are confirmed.
- `rpm` is only meaningful after CPR is calibrated.
- Wheel PID / closed-loop motor control is explicitly out of scope for H24-D.
