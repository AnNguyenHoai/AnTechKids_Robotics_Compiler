# Behavior Architecture – Line Following

## Overview

The line‑following behavior is implemented as a layered state machine that decouples perception, decision, and motion control. This architecture ensures maintainability and extensibility for advanced missions (Warehouse, Maze, Smart Delivery).

## State Diagram
┌─────────────┐ mask==0 ┌─────────────┐
│ FOLLOWING │ ─────────────────▶ │ LOST │
└─────────────┘ └─────────────┘
│ │
│ intersection && stopRequested │ timeout (500ms)
▼ ▼
┌─────────────┐ ┌─────────────┐
│ INTERSECTION│ │ SEARCHING │
└─────────────┘ └─────────────┘
│ │
│ stopRequested cleared │ mask!=0
▼ ▼
┌─────────────┐ ┌─────────────┐
│ FOLLOWING │ ◀───────────────── │ FOLLOWING │
└─────────────┘ └─────────────┘
│
│ turnRequested
▼
┌─────────────┐ mask!=0 ┌─────────────┐
│ TURNING │ ─────────────────▶│ FOLLOWING │
└─────────────┘ └─────────────┘

text

## Motion Intent

The state machine outputs one of the following intents:

| Intent     | Description                        |
|------------|------------------------------------|
| `FOLLOW`   | Normal line following with PID     |
| `TURN_LEFT`| Rotate left at base speed          |
| `TURN_RIGHT`| Rotate right at base speed         |
| `STOP`     | Stop motors                        |
| `RECOVER`  | Execute recovery search strategy   |

## Module Responsibilities

| Module                  | Responsibility                                                                 |
|-------------------------|--------------------------------------------------------------------------------|
| `LinePerception`        | Converts 3‑bit sensor mask to `LineState` (semantic interpretation).           |
| `LineErrorEstimator`    | Maps `LineState` to a continuous error value in [-1, 1].                       |
| `PIDController`         | Computes a correction from error using PID gains.                              |
| `MotorMixer`            | Mixes base speed and correction to produce left/right motor speeds.            |
| `FollowerStateMachine`  | Maintains state (FOLLOWING, LOST, SEARCHING, INTERSECTION, TURNING) and emits `MotionIntent` based on events. |
| `MotionController`      | Translates `MotionIntent` + speed (+ error for FOLLOW) into actual motor commands. For FOLLOW it uses PID and MotorMixer; for turns/stop it sets speeds directly. |
| `RecoveryStrategy`      | Provides search patterns (left, right, spiral) when line is lost.              |
| `IntersectionDetector`  | Detects intersections using pattern persistence (history of masks) to reduce noise. |
| `LineFollower`          | Coordinates all components: reads mask, updates state machine, computes motor speeds, and applies commands. |

## Recovery Flow

1. When `mask == 0` for > 500ms, state transitions to `SEARCHING`.
2. `RecoveryStrategy` is activated (`MotionIntent::RECOVER`).
3. It executes a search pattern (left, right, spiral) until line is found.
4. Upon finding line, state returns to `FOLLOWING` and recovery resets.

## Turn Flow

1. `turnEncounterLine(direction)` is called → `_turnRequested = true`, direction set.
2. State machine transitions to `TURNING`.
3. `MotionIntent` becomes `TURN_LEFT` or `TURN_RIGHT`.
4. `MotionController` produces differential motor speeds.
5. When `mask != 0` (line found), state returns to `FOLLOWING`.

## Intersection Flow

1. `stopAtIntersection()` sets `_stopRequested`.
2. `IntersectionDetector` detects pattern.
3. State machine transitions to `INTERSECTION`.
4. `MotionIntent` becomes `STOP` → motors stop.
5. When `stopRequested` cleared, state returns to `FOLLOWING`.

## Design Principles

- **Single Responsibility**: Each module does exactly one thing.
- **Loose Coupling**: Modules communicate via simple data types (enums, structs).
- **No Direct Hardware Access in State Machine**: State machine only outputs intents.
- **Deterministic**: Given same inputs, output is predictable.

## Acceptance

This architecture is frozen as the official line‑following behavior layer for M2. Future features (Warehouse, Maze) will build on this foundation.