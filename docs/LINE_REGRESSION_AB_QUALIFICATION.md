# LINE-REG-01/02 — Physical Line Regression A/B Qualification

## Purpose

Localize the physical `basic_line` regression without changing the production `esp32dev` behavior. The two qualification profiles run the same latest code, hardware mapping, compiler contract, and line follower. They differ only at the TCRT5000 acquisition boundary.

## Profiles

### Current snapshot path

```text
esp32dev_line_snapshot_qualification
```

Build flags:

```text
LINE_REGRESSION_DIAGNOSTICS=1
LINE_REGRESSION_LEGACY_ACQUISITION=0
```

Behavior:

```text
BeginCycle
  -> first line consumer samples coherent L/C/R snapshot
  -> later TCRT consumers reuse that snapshot
  -> LineFollower receives the resulting mask
```

### Legacy direct-read path

```text
esp32dev_line_legacy_qualification
```

Build flags:

```text
LINE_REGRESSION_DIAGNOSTICS=1
LINE_REGRESSION_LEGACY_ACQUISITION=1
```

Behavior:

```text
every TCRT5000::update()
  -> immediate GPIO read
  -> cached level updated
  -> existing GetTraceRaw/LineFollower code continues unchanged
```

This restores only the pre-snapshot acquisition boundary for qualification. It does not revert the compiler, VM, opcode table, LineFollower, motor mapping, network, or deployment stack.

## Production safety

`env:esp32dev` defines neither LINE-REG flag. Both flags also default to `0` in firmware source, so normal production behavior remains the snapshot path with diagnostics disabled.

## Diagnostic records

### Sensor transition

Emitted only when a physical sensor level changes:

```text
[LINE-REG][SENSOR] mode=snapshot name=line_center raw=1 cache=1 detected=1 threshold=1
```

Fields:

- `mode`: `snapshot` or `legacy`
- `name`: `line_left`, `line_center`, `line_right`
- `raw`: immediate digital GPIO level
- `cache`: TCRT cached level after acquisition
- `detected`: threshold interpretation used by line logic
- `threshold`: configured active level

### Line decision

Emitted on mask/follower-state changes and at most as a 10 Hz heartbeat otherwise:

```text
[LINE-REG][FOLLOW] mode=snapshot mask=010 snapshot={valid:1,mask:010,seq:42} lineState=2 followerState=0 error=0.00 cmd={L:35,R:35}
```

Fields:

- `mask`: mask actually received by `LineFollower::update()`; for `LineBasis` this is the `GetTraceRaw()` result
- `snapshot.valid`, `snapshot.mask`, `snapshot.seq`: current cycle-owned snapshot evidence
- `lineState`: numeric `LineState`
- `followerState`: numeric `FollowerState`
- `error`: semantic line error before PID update
- `cmd`: logical left/right motor commands returned by the follower

The numeric enum values are diagnostic evidence only. The primary comparison is raw GPIO -> detected state -> mask -> motor command.

## Static qualification matrix

Use the same robot, track, sensor potentiometer adjustment, battery condition, and USB/power arrangement for both profiles.

| Physical condition | Expected mask |
| --- | --- |
| No sensor on line | `000` |
| Left only | `100` |
| Center only | `010` |
| Right only | `001` |
| Left + Center | `110` |
| Center + Right | `011` |

For each row, record the `[LINE-REG][SENSOR]` transitions and the next `[LINE-REG][FOLLOW]` record.

## Dynamic qualification

Run the same `basic_line` program using both profiles. Start at low speed before normal speed.

Suggested sequence:

```text
25 -> 35 -> 50
```

Do not readjust the sensor potentiometers between A and B.

## Interpretation

### Legacy works, snapshot fails

```text
legacy:   raw correct -> mask correct -> follows
snapshot: raw correct -> snapshot/mask wrong or stale -> fails
```

Root-cause scope: `LineSensorSnapshot` lifecycle / cache projection / firmware-cycle acquisition timing.

### Both modes show correct masks but both fail dynamically

Root-cause scope moves downstream to:

```text
LinePerception
FollowerStateMachine
LineErrorEstimator
PID
MotorMixer
motor mapping
```

### Both modes show wrong raw GPIO

Do not change VM or follower logic. Recheck physical sensor output, active level, wiring/pin mapping, supply, and comparator calibration.

### Raw GPIO correct, `detected` inverted

Root-cause scope is the TCRT active-level/threshold contract.

## Evidence to retain

For each profile capture:

- firmware commit SHA
- PlatformIO environment name
- exact `basic_line` source
- speed
- sensor calibration unchanged confirmation
- static matrix log
- dynamic run log
- short note: follows / does not follow / unstable

Do not close LINE-REG-01 or LINE-REG-02 based on host tests alone. Physical evidence is required.
