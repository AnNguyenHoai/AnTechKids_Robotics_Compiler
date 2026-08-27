# H24-C — Encoder Driver

## Scope

H24-C adds the low-level incremental quadrature encoder subsystem required by Robot Hardware V2.
It does not implement wheel PID, closed-loop motor control, distance calibration, or public RoboSim APIs.

## Frozen GPIO contract

| Encoder signal | GPIO |
|---|---:|
| Left A | 34 |
| Left B | 35 |
| Right A | 36 |
| Right B | 39 |

These are ESP32 input-only pins. The firmware configures them as plain inputs. If the physical encoder uses open-collector outputs, external pull-ups must be provided because this contract does not depend on internal pull-ups.

## Architecture

```
Encoder A/B GPIO
      ↓ interrupts
Encoder (driver)
      ↓
SensorManager
      ↓
Future H24-D calibration / H24-F wheel controller
```

`Encoder` is an `ISensor` and therefore participates in the existing SensorManager lifecycle.

## Decoder

Both A and B edges trigger a shared decoder. The state transition table produces:

- `+1`: forward transition
- `-1`: reverse transition
- `0`: no movement or invalid transition

The driver exposes signed count, direction, counts/second and RPM.

## Counts per revolution

The initial value is deliberately `1.0` until H24-D measures the actual physical counts-per-wheel-revolution for the delivered JGA25-370 encoder and gearbox. RPM should therefore not be treated as physically calibrated until H24-D.

## Verification

Host-side unit test: `tests/test_quadrature_decoder.cpp`.
Physical bring-up checklist:

1. rotate each wheel manually forward and verify signed count increases;
2. rotate backward and verify count decreases;
3. verify both encoder channels change without cross-interference;
4. measure physical counts per wheel revolution;
5. update calibrated counts-per-revolution before enabling RPM-based control.
