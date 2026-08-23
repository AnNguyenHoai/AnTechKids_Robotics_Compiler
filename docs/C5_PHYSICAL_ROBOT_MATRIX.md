# C5 Physical ESP32 / Robot Validation Matrix

## Scope

C5 prepares and validates representative RoboSim programs through the physical deployment boundary:

`RoboSim source -> rewrite -> compiler -> generated_program.h -> ESP32 firmware -> flash -> real robot behavior`

The current development environment can execute the first compiler-side stages but cannot observe the user's ESP32 or robot. Therefore **physical behavior is intentionally PENDING until real-hardware execution is performed**.

| Test ID | Program | Category | Rewrite | Compile | Firmware | Flash | Physical Behavior |
|---|---|---|---|---|---|---|---|
| C5-MOVE-001 | `C5_MOVE_WAIT_STOP.py` | movement | PASS | PASS | READY | PENDING | PENDING_REAL_ROBOT |
| C5-LED-001 | `C5_LED_TOGGLE.py` | LED | PASS | PASS | READY | PENDING | PENDING_REAL_ROBOT |
| C5-ULTRA-001 | `C5_ULTRASONIC_LED.py` | sensor -> decision -> actuator | PASS | PASS | READY | PENDING | PENDING_REAL_ROBOT |
| C5-ULTRA-002 | `C5_ULTRASONIC_MOTOR.py` | sensor -> decision -> actuator | PASS | PASS | READY | PENDING | PENDING_REAL_ROBOT |
| C5-LINE-001 | `C5_LINE_QUERY_LED.py` | line sensor | PASS | PASS | READY | PENDING | PENDING_REAL_ROBOT |
| C5-LINE-002 | `C5_LINE_FOLLOW.py` | line following | PASS | PASS | READY | PENDING | PENDING_REAL_ROBOT |

## How to execute on the robot

Prepare all representative programs:

```text
python tools/c5_validate.py
```

Build one program for ESP32 firmware:

```text
python tools/c5_validate.py --test C5-MOVE-001 --firmware
```

Flash it:

```text
python tools/c5_validate.py --test C5-MOVE-001 --flash --port COMx
```

Each `--flash` invocation intentionally rebuilds and flashes one program at a time because the current firmware uses one generated program header.

## Physical acceptance

For each test, record:

- expected behavior
- actual behavior
- serial log
- PASS / FAIL
- failure layer: compiler, bytecode, VM, RobotAPI, firmware, hardware, behavior

## Known limitation

Ultrasonic may occasionally return `-1` for timeout. C5 does not reopen that investigation unless it makes the representative program's intended behavior fail completely.
