# RobotAPI Sensor Specification

## Overview

RobotAPI provides high-level sensor access for the VM. It delegates hardware interaction to `SensorManager`.

## Line Sensor API

### `int16_t ReadLine(int channel)`

V1 Line5 preserves the original public channel numbering and appends the two new outer sensors:

| Channel | Sensor | GPIO |
|---:|---|---:|
| 0 | Left | 18 |
| 1 | Center | 16 |
| 2 | Right | 17 |
| 3 | Far Left | 34 |
| 4 | Far Right | 35 |

Channels `0..2` are intentionally unchanged for backward compatibility with existing lessons and RoboSim programs. Invalid channels fail safe and return `0`.

- **Returns**: `1` if line (black) is detected, `0` otherwise.

### `GetTraceValue(port, channel)` / `GetTraceState(port, channel)`

These functions use the same channel contract `0=L, 1=C, 2=R, 3=FL, 4=FR`. `port` remains transport-compatible and is currently ignored by the V1 direct TCRT5000 implementation.

### `GetTraceRaw(port)`

`GetTraceRaw()` returns the canonical five-bit spatial mask:

```text
bit4  bit3  bit2  bit1  bit0
 FL     L     C     R     FR
```

Mask constants:

```text
FL = 0x10
L  = 0x08
C  = 0x04
R  = 0x02
FR = 0x01
```

Representative values:

```text
10000 = Far Left
01000 = Left
00100 = Center
00010 = Right
00001 = Far Right
11000 = Far Left + Left
01100 = Left + Center
00110 = Center + Right
00011 = Right + Far Right
00000 = Lost
11111 = all sensors active
```

The API channel numbering and the raw-mask bit order are intentionally different: channel numbering preserves V1 compatibility, while the raw mask is spatially ordered for algorithms and diagnostics.

## Line-following interpretation

The steering estimator uses weights `FL=-2, L=-1, C=0, R=+1, FR=+2` and returns the average weight of all active sensors. `00000` is handled separately as line lost and returns a neutral numeric estimate to avoid division by zero.

Intersection candidacy starts at four or more active sensors and remains subject to the existing temporal-persistence filter. Final intersection thresholds, PID gains, recovery threshold and turn/reacquire policy require physical robot validation.

## Other Sensor APIs

The following APIs are unchanged by V1-LINE5-01:

- `ReadUltrasonic()` – ultrasonic driver path.
- `ReadTouch(int port)` – touch sensor path.
- `ReadLight(int channel)` – light sensor path.
- `ReadColor()` – color sensor path.
