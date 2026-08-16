# RoboSim API Inventory

**Version:** 1.0  
**Status:** Complete  
**Date:** 2026-08-09

## Overview

This document inventories every available RoboSim API based on:

- RoboSim Blockly definitions
- Python Generator output
- Official RoboSim API Specification
- Existing sample projects
- RC1 acceptance program

**Total APIs: 45** (including GUI-only and language features)

---

## API Categories

### 1. Motion (6)

| API | Arguments | Semantic | Priority |
|-----|-----------|----------|----------|
| `SetMoveInitialize` | (left, right, reverse) | Stub | P1 |
| `SetMoveRun` | (direction, speed) | Native | P0 |
| `SetMoveRunSecond` | (direction, speed, seconds) | Rewrite | P0 |
| `SetMoveRunAngle` | (direction, speed, angle) | Approximation | P1 |
| `SetMoveSpeed` | (left, right) | Native | P0 |
| `SetMoveStop` | () | Native | P0 |

### 2. Sensor (8)

| API | Arguments | Semantic | Priority |
|-----|-----------|----------|----------|
| `GetUltrasound` | (port) | Native | P0 |
| `GetTouch` | (port) | Native | P0 |
| `GetLightSensor` | (port) | Native | P0 |
| `GetLightSensorData` | (port) | Dummy | P2 |
| `GetTraceV2I2CState` | (port, channel) | Native | P0 |
| `GetTraceV2I2C` | (port, channel) | Dummy | P1 |
| `GetTraceV2I2CData` | (port) | Native | P0 |
| `GetTraceV2I2CChxState` | (port, channel) | Native | P0 |

### 3. LED (2)

| API | Arguments | Semantic | Priority |
|-----|-----------|----------|----------|
| `Set3CLed` | (port, state) | Native | P0 |
| `SetLightSensorLed` | (port, state) | Native | P0 |

### 4. Audio (1)

| API | Arguments | Semantic | Priority |
|-----|-----------|----------|----------|
| `SetMp3Play` | (index) | Approximation | P0 |

### 5. Servo / Steering (3)

| API | Arguments | Semantic | Priority |
|-----|-----------|----------|----------|
| `SetServo` | (port, angle) | Stub | P2 |
| `SetSeeringEngine` | (port, angle) | Stub | P2 |
| `SetSeeringEngineTime` | (port, angle, ms) | Stub | P2 |

### 6. Motor (DC) (3)

| API | Arguments | Semantic | Priority |
|-----|-----------|----------|----------|
| `SetMotor` | (port, speed) | Stub | P2 |
| `SetMotorServo` | (port, speed, angle) | Stub | P2 |
| `SetMotorStraightAngle` | (left, right, speed, angle) | Stub | P1 |

### 7. Line Following (6)

| API | Arguments | Semantic | Priority |
|-----|-----------|----------|----------|
| `line_basis` | (speed) | Native | P1 |
| `line_follow` | (speed) | Native | P1 |
| `line_stop` | () | Native | P1 |
| `line_millisecond` | (speed, ms) | Approximation | P1 |
| `line_intersection_stop` | (speed, type) | Stub | P1 |
| `line_turn_encounterline` | (speed, angle, direction) | Native | P1 |
| `line_for_bmp` | (speed, degree) | Approximation | P2 |
| `line_set_initialize` | (port, color, chassis) | Stub | P2 |

### 8. Peripheral (1)

| API | Arguments | Semantic | Priority |
|-----|-----------|----------|----------|
| `SetLizard` | (state) | Stub | P3 |

### 9. Utility (1)

| API | Arguments | Semantic | Priority |
|-----|-----------|----------|----------|
| `SetWaitForTime` | (seconds) | Rewrite | P0 |

### 10. GUI-Only (2)

| API | Arguments | Semantic | Priority |
|-----|-----------|----------|----------|
| `UpdateVar` | (name, value) | NOP | P3 |
| `DisplayVariable` | (name) | NOP | P3 |

### 11. Language Features (12)

| Feature | Semantic | Priority |
|---------|----------|----------|
| `while True` / `while 1` | Native | P0 |
| `if` / `else` | Native | P0 |
| `for i in range()` | Native | P0 |
| `break` / `continue` | Native | P0 |
| Global variables | Native | P0 |
| User-defined functions | Native | P0 |
| `_thread.start_new_thread` | Rewrite | P1 |

---

## Summary

| Category | Count |
|----------|-------|
| Motion | 6 |
| Sensor | 8 |
| LED | 2 |
| Audio | 1 |
| Servo/Steering | 3 |
| Motor | 3 |
| Line | 6 |
| Peripheral | 1 |
| Utility | 1 |
| GUI-Only | 2 |
| Language Features | 12 |
| **Total** | **45** |