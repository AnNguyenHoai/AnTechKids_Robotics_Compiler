# Line‑Following Control Pipeline

## Overview

The line‑following control pipeline is a strictly layered architecture that transforms raw sensor readings into motor commands. Each layer has a single responsibility, and data flows only in one direction.
┌─────────────┐
│ Sensor │ (hardware)
│ Mask (3‑bit)│
└──────┬──────┘
▼
┌─────────────┐
│ LinePerception│ mask → LineState
│ │ (semantic interpretation)
└──────┬──────┘
▼
┌─────────────┐
│LineErrorEstimator│ LineState → error
│ │ (continuous value, -1..1)
└──────┬──────┘
▼
┌─────────────┐
│PIDController │ error → correction
│ │ (proportional‑integral‑derivative)
└──────┬──────┘
▼
┌─────────────┐
│ MotorMixer │ (baseSpeed, correction) → (left, right)
│ │ (speed mixing with clamping)
└──────┬──────┘
▼
┌─────────────┐
│ RobotAPI │ (left, right) → PWM hardware
└─────────────┘

text

## Error Convention

| LineState         | Error Value |
|-------------------|------------:|
| LEFT, LEFT_CENTER |        -1.0 |
| CENTER            |         0.0 |
| RIGHT, CENTER_RIGHT|        +1.0 |
| LOST, INTERSECTION|         0.0 |

Negative error → turn left.  
Positive error → turn right.  
Zero → straight.

## Motor Mixing

Given a `baseSpeed` and a `correction` (PID output), motor speeds are computed as:
left = baseSpeed - correction * scaleFactor
right = baseSpeed + correction * scaleFactor

text

Where `scaleFactor` = 0.8 (configurable).  
Outputs are clamped to the range `[-100, 100]`.

## PID Integration

- PID receives only the `error` float.
- Returns a `correction` float.
- It does not know about masks, sensors, or hardware.

## Extensibility

The pipeline is designed to support more sensors (e.g., 8‑eye arrays) without changing PID or MotorMixer:

1. Extend `LinePerception` to produce a position index (e.g., -3…+3).
2. Update `LineErrorEstimator` to map that index to an error value.
3. All downstream modules remain unchanged.

## Design Principles

- **Single Responsibility** – each module does exactly one thing.
- **Single Source of Truth** – one function per transformation.
- **Loose Coupling** – modules communicate via simple data types, not shared state.
- **Hardware Independence** – no hardware dependencies in the pipeline.

## Acceptance

This pipeline is considered stable and will not be refactored during future feature development (Recovery, Intersection, State Machine).