# LINE-REG-01/02/03 — Physical Line Regression A/B Qualification

## Purpose

Localize the physical `basic_line` regression without changing the production `esp32dev` behavior. The two qualification profiles run the same latest code, hardware mapping, compiler contract, and line follower. They differ only at the TCRT5000 acquisition boundary.

LINE-REG-03 adds qualification-only wireless UDP capture so the robot can run untethered while the laptop records exactly the same `[LINE-REG]` records that were previously visible only over Serial.

## Profiles

### Current snapshot path

```text
esp32dev_line_snapshot_qualification
```

Build flags:

```text
LINE_REGRESSION_DIAGNOSTICS=1
LINE_REGRESSION_LEGACY_ACQUISITION=0
LINE_REGRESSION_UDP=1
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
LINE_REGRESSION_UDP=1
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

`env:esp32dev` defines no LINE-REG flags. `LINE_REGRESSION_DIAGNOSTICS` and `LINE_REGRESSION_UDP` default to `0` in firmware source, so normal production behavior remains the snapshot path with diagnostic transport disabled.

The control-critical sensor/follower path only formats and enqueues sparse records into a bounded RAM queue. UDP transmission is performed later in the firmware background phase after `RobotNetworkService::update()`. At most one queued record is transmitted per firmware loop.

## Wireless UDP capture

The robot reuses the existing Wi-Fi configuration already consumed by `RobotNetworkService`; no laptop IP is compiled into firmware. When connected, LINE-REG broadcasts records to the current subnet on UDP port `4211`. The sender binds source port `4212`. Robot discovery continues to use its existing UDP port `4210`.

Recommended topology:

```text
Phone hotspot / Wi-Fi AP
  |-- laptop
  `-- ESP32 robot
```

The laptop and robot must be on the same IPv4 subnet and local firewall rules must allow inbound UDP port `4211` for Python.

Start the receiver from repository root:

```bash
python tools/line_reg_udp_receiver.py --output snapshot.log
```

The receiver binds `0.0.0.0:4211`, prints received records to the console, and appends the raw `[LINE-REG]` lines to the requested log. Stop with `Ctrl+C`.

For the legacy run:

```bash
python tools/line_reg_udp_receiver.py --output legacy.log
```

If no packet appears, verify in this order:

1. robot Wi-Fi credentials are provisioned by the normal build/bootstrap flow;
2. laptop and robot are on the same Wi-Fi/hotspot;
3. Windows Firewall allows Python on the active network profile or explicitly allows UDP `4211`;
4. the flashed environment is one of the two LINE-REG qualification profiles, not production `esp32dev`;
5. `basic_line` is actually executing and producing sensor/follower diagnostic changes.

Serial output remains as a bench fallback when USB is attached, but physical dynamic qualification should use UDP so the robot can run untethered.

## Build and physical capture sequence

From `robot-platform`:

```bash
pio run -e esp32dev_line_snapshot_qualification -t upload
```

After flashing, unplug USB if required for free movement, power the robot normally, then start the laptop receiver from repository root:

```bash
python tools/line_reg_udp_receiver.py --output snapshot.log
```

Run the static matrix and then `basic_line`. Stop capture with `Ctrl+C`.

Flash the legacy profile:

```bash
pio run -e esp32dev_line_legacy_qualification -t upload
```

Do not adjust TCRT potentiometers or change the test track/battery setup. Capture:

```bash
python tools/line_reg_udp_receiver.py --output legacy.log
```

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

Use the same robot, track, sensor potentiometer adjustment, battery condition, and power arrangement for both profiles.

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

Do not close LINE-REG-01, LINE-REG-02, or LINE-REG-03 based on host tests alone. Physical evidence is required.
