# ROBOSIM_COMPATIBILITY_ARCHITECTURE.md

Version: 1.0

Status: Architecture Freeze

Owner: Robot Platform Team

Last Updated: 2026-08-09

---

# 1. Purpose

This document defines the official RoboSim Compatibility Architecture of the Robot Platform.

It is the single source of truth for all RoboSim compatibility development.

Every future sprint (M5.2+) must follow this architecture.

This document defines:

- Compatibility philosophy
- Compatibility layers
- API classification
- Semantic implementation rules
- Development priorities
- Compatibility metrics
- Future implementation workflow

This document is architectural only.

It does not describe implementation details.

---

# 2. Design Philosophy

## Robot Platform is NOT responsible for robot behaviors.

Robot Platform only provides:

- Frontend
- Compiler
- Bytecode VM
- Robot API
- HAL
- Hardware Drivers

Behaviors such as:

- Line Following
- Obstacle Avoidance
- Maze Solver
- Automatic Parking
- Robot Games

are created by users (students) by combining RoboSim blocks.

Therefore:

> Platform compatibility is measured by language compatibility, not behavior implementation.

---

# 3. Compatibility Goal

Ultimate Goal

> Every valid RoboSim program shall compile successfully and execute correctly on the Robot Platform without requiring source code modification.

This includes:

- Compiler compatibility
- Runtime compatibility
- Hardware compatibility

---

# 4. Compatibility Layers

Every RoboSim API passes through the following layers.

```

RoboSim Blockly

↓

Python Generator

↓

Frontend

↓

Compiler

↓

Bytecode

↓

Virtual Machine

↓

RobotAPI

↓

HAL

↓

Hardware

↓

Physical Verification

```

Layer descriptions

| Layer | Responsibility |
|---------|----------------|
| Frontend | Rewrite RoboSim APIs into Standard Robot API when required |
| Compiler | Python AST → Robot Bytecode |
| VM | Execute Robot Bytecode |
| RobotAPI | Platform abstraction |
| HAL | Hardware abstraction |
| Hardware | Physical devices |
| Verified | Confirmed on real robot |

---

# 5. Core Compatibility

Core Compatibility measures whether a normal RoboSim project can execute correctly.

Core APIs include:

- Motion
- Sensor
- LED
- Audio
- Utility
- Language Features

Core Compatibility SHALL NOT depend on optional hardware.

Examples

Servo

Steering

Lizard

Camera

must NOT reduce Core Compatibility.

---

# 6. Full Compatibility

Full Compatibility includes every RoboSim API.

Including

- Servo
- Steering
- Optional Hardware
- GUI APIs
- Future APIs

---

# 7. Semantic Classification

Every API belongs to one semantic class.

## Native

Implemented exactly.

Example

SetMoveRun()

---

## Rewrite

Frontend rewrites into native APIs.

Example

SetMoveRunSecond()

↓

forward()

↓

wait()

↓

stop()

---

## NOP

Compile succeeds.

Runtime ignores.

Example

UpdateVar()

DisplayVariable()

---

## Approximation

Equivalent implementation.

Example

SetMoveRunAngle()

↓

Time-based movement.

---

## Stub

API exists.

RobotAPI exists.

No hardware implementation.

Example

SetServo()

on robots without servo.

---

## Dummy

Query API returns deterministic value.

Example

Dummy Sensor.

---

# 8. Compatibility Rules

Rule 1

Every RoboSim API shall be recognised by the compiler.

Unknown Function is forbidden.

---

Rule 2

Compiler success SHALL NOT depend on hardware availability.

---

Rule 3

GUI-only APIs shall compile successfully.

Runtime executes NOP.

---

Rule 4

Optional hardware APIs shall compile successfully.

Runtime executes Stub until hardware becomes available.

---

Rule 5

Robot-specific APIs shall NEVER appear in the RoboSim layer.

Examples

DigitalWrite()

GPIOWrite()

PWMWrite()

MotorDriverWrite()

These belong only to RobotAPI or HAL.

---

# 9. Compatibility Metrics

Two independent KPIs shall be maintained.

## Core Compatibility

Measures only essential APIs.

Goal

100%

---

## Full Compatibility

Measures every RoboSim API.

Goal

100%

---

# 10. API Priority

Priority defines implementation order.

## P0

Critical

Language

Motion

Sensor

Utility

---

## P1

Important

Advanced Motion

Line APIs

Common Extensions

---

## P2

Optional

Servo

Steering

Motor Extensions

---

## P3

Future

Lizard

Rare Devices

Experimental APIs

---

# 11. API Lifecycle

Every new API follows exactly this lifecycle.

```

Survey

↓

Classification

↓

Semantic Decision

↓

Frontend

↓

Compiler

↓

VM

↓

RobotAPI

↓

HAL

↓

Hardware

↓

Physical Test

↓

Verified

```

No API may skip this process.

---

# 12. Compatibility Matrix

Each API shall be evaluated across these layers.

| Layer | Description |
|---------|-------------|
| Frontend | Rewrite Support |
| Compiler | Bytecode Generation |
| VM | Opcode Support |
| RobotAPI | Platform API |
| HAL | Driver |
| Physical | Hardware Installed |
| Verified | Tested |

Each API also records:

- Semantic
- Priority
- Status

---

# 13. Physical Verification Policy

Verified does NOT mean implemented.

Verified means:

- Executed on a real robot.
- Behaviour matches RoboSim expectation.
- Test report exists.

Accepted states:

- PASS
- FAIL
- NOT TESTED

Verification requires a physical test report.

---

# 14. API Policy

## Native

Full implementation.

---

## Rewrite

Frontend transformation.

---

## NOP

Compile PASS.

Runtime ignores.

---

## Approximation

Equivalent implementation.

Must be documented.

---

## Stub

Placeholder implementation.

No hardware.

---

## Dummy

Returns deterministic values.

---

## Deprecated

Compiler PASS.

Generate warning.

Suggest replacement API.

---

# 15. Development Principles

Platform developers implement:

- Compiler
- Runtime
- VM
- RobotAPI
- HAL

Users implement:

- Algorithms
- Behaviors
- Strategies

The Platform SHALL NEVER implement educational robot behaviors.

---

# 16. Sprint Strategy

M5.1

Architecture Freeze

Completed.

---

M5.2

Compiler Compatibility

Goal

No valid RoboSim API shall fail compilation.

---

M5.3

Runtime Compatibility

Goal

Implement Native / Rewrite / NOP / Stub policies.

---

M5.4

Physical Verification

Goal

Verify every supported API on real hardware.

---

# 17. Success Criteria

The RoboSim Compatibility project is complete when:

- Core Compatibility = 100%
- Full Compatibility = 100%
- No Unknown Function exists
- No Unsupported Function exists
- Every RoboSim API has a defined Semantic
- Every API follows the official lifecycle
- Every supported API has been physically verified

---

# 18. Architecture Freeze

This document is now the official Compatibility Architecture.

All future RoboSim compatibility development shall conform to this specification.

Changes require architecture review before approval.