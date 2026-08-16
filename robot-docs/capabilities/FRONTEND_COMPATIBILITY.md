# Frontend Compatibility

**Version:** 1.0  
**Status:** Complete  
**Date:** 2026-08-09

## Overview

The Frontend (`robot-frontend-robosim`) transforms RoboSim-specific Python code into Standard Robot API calls. This document defines all rewrite rules and alias mappings.

---

## Rewrite Rules

### 1. Direct Mappings

| RoboSim API | Canonical API | Notes |
|-------------|---------------|-------|
| `SetMoveRun("forward", speed)` | `forward(speed)` | Direction normalized |
| `SetMoveRun("backward", speed)` | `backward(speed)` | Direction normalized |
| `SetMoveRun("left", speed)` | `turn_left(speed)` | Direction normalized |
| `SetMoveRun("right", speed)` | `turn_right(speed)` | Direction normalized |
| `SetMoveStop()` | `stop()` | Direct |
| `Set3CLed(port, state)` | `set_3c_led(port, state)` | Direct |
| `SetLightSensorLed(port, state)` | `set_light_sensor_led(port, state)` | Direct |
| `SetMp3Play(index)` | `set_mp3_play(index)` | Direct |
| `SetServo(port, angle)` | `set_servo(port, angle)` | Direct |
| `SetMotorStraightAngle(l,r,s,a)` | `set_motor_straight_angle(l,r,s,a)` | Direct |
| `SetMotor(port, speed)` | `set_motor(port, speed)` | Direct |
| `SetMotorServo(port, speed, angle)` | `set_motor_servo(port, speed, angle)` | Direct |
| `SetSeeringEngine(port, angle)` | `set_seering_engine(port, angle)` | Direct |
| `SetSeeringEngineTime(p, a, ms)` | `set_seering_engine_time(p, a, ms)` | Direct |
| `SetLizard(state)` | `set_lizard(state)` | Direct |

### 2. Expansion (Rewrite)

| RoboSim API | Expansion |
|-------------|-----------|
| `SetMoveRunSecond(dir, speed, seconds)` | `forward(speed); wait(seconds*1000); stop()` |
| `SetWaitForTime(seconds)` | `wait(int(seconds*1000))` |

### 3. Sensor Mappings

| RoboSim API | Canonical API | Arg Mapping |
|-------------|---------------|-------------|
| `GetUltrasound(port)` | `read_ultrasonic()` | Port dropped |
| `GetTouch(port)` | `read_touch(port)` | Preserved |
| `GetLightSensor(port)` | `read_light(port)` | Preserved |
| `GetLightSensorData(port)` | `get_light_sensor_data(port)` | Preserved |
| `GetTraceV2I2CChxState(port, channel)` | `read_line(channel)` | Port dropped |
| `GetTraceV2I2CState(port, channel)` | `get_trace_state(port, channel)` | Preserved |
| `GetTraceV2I2C(port, channel)` | `get_trace_value(port, channel)` | Preserved |
| `GetTraceV2I2CData(port)` | `get_trace_raw(port)` | Preserved |

### 4. Threading

| RoboSim API | Rewrite |
|-------------|---------|
| `_thread.start_new_thread(func, ())` | `func()` (inlined) |

### 5. GUI-Only (NOP)

| RoboSim API | Rewrite |
|-------------|---------|
| `UpdateVar(name, value)` | `update_var(name, value)` (NOP at runtime) |
| `DisplayVariable(name)` | `display_variable(name)` (NOP at runtime) |

---

## Alias Rules

Directions are normalized to lowercase and aliases resolved:

| Input | Normalized |
|-------|------------|
| `"forward"` | `forward` |
| `"backward"` | `backward` |
| `"left"`, `"turnleft"` | `turn_left` |
| `"right"`, `"turnright"` | `turn_right` |

All direction strings are case-insensitive.

---

## Future TODO

- [ ] `SetMoveInitialize` – lower `reverse` string to enum
- [ ] `SetMoveRunAngle` – lower `direction` string to enum
- [ ] `line_set_initialize` – lower `color` and `chassis_type` strings to enums
- [ ] True threading support (`_thread.start_new_thread` → ThreadStart opcode)