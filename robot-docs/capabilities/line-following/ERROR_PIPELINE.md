# Line Error Pipeline

## Architecture

The line‑following control pipeline separates concerns into well‑defined modules:
Sensor Mask (3-bit)
│
▼
LinePerception::interpret(mask) → LineState (semantic)
│
▼
LineErrorEstimator::estimate(state) → error ∈ [-1, 1]
│
▼
PIDController::update(error) → correction ∈ [-max, max]
│
▼
MotorMixer::mix(baseSpeed, correction) → (leftSpeed, rightSpeed)
│
▼
RobotAPI::setMotorsDirect(left, right)

text

## Error Convention

| LineState         | Error |
|-------------------|------:|
| LEFT, LEFT_CENTER | -1.0  |
| CENTER            |  0.0  |
| RIGHT, CENTER_RIGHT| +1.0  |
| LOST, INTERSECTION|  0.0  |

- Negative error → turn left.
- Positive error → turn right.
- Zero → straight.

## Motor Mixing
left = baseSpeed - correction * scale
right = baseSpeed + correction * scale

text

- `scale` = 0.8 (tunable)
- Clamped to [-100, 100]

## PID Integration

- PID receives only the `error` float.
- Returns `correction` float.
- No knowledge of masks or hardware.

## Extension to 8‑Sensor Arrays

The pipeline is designed to be hardware‑independent. To support 8 sensors:

1. Extend `LinePerception` to produce a position index (e.g., -3…+3).
2. Modify `LineErrorEstimator` to map that index to an error value.
3. PID and MotorMixer remain unchanged.

## Unit Test Coverage

- `LineErrorEstimator`: all states map to expected errors.
- `MotorMixer`: mixing and clamping work correctly.
- Integration test: pipeline produces expected motor outputs for given masks.

## Design Principles

- Single responsibility per module.
- No hardcoded bitmasks in PID or MotorMixer.
- Clear data flow with unambiguous interfaces.