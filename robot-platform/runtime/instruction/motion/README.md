# Motion Instruction Package

This package implements the Motion instruction family for the Robot Runtime.

## Instructions

| Instruction | Opcode | Operands | Description |
|-------------|--------|----------|-------------|
| `MOVE` | Opcode::FORWARD / BACKWARD / TURN_LEFT / TURN_RIGHT | direction (int), speed (int), [duration (int)] | Move robot in given direction at speed. |
| `STOP` | Opcode::STOP | none | Stop all motion. |
| `TURN` | Opcode::TURN_LEFT / TURN_RIGHT | direction (int), speed (int), [angle (int)] | Turn robot left/right at speed. |
| `SET_SPEED` | Opcode::SET_SPEED | left_speed (int), right_speed (int) | Set individual motor speeds. |

## Execution Flow

Each Motion Instruction:

1. Validates operands (type, range).
2. Builds a `RobotApiRequest` with the appropriate `ApiId` and parameters.
3. Dispatches via `InstructionContext::apiDispatcher()`.
4. Advances Program Counter on success.
5. Returns `ExecutionResult`.

## Validation

- Speed range: [-100, 100]
- Direction: 0=Forward, 1=Backward, 2=Left, 3=Right (for MOVE)
- Turn direction: 0=Left, 1=Right (for TURN)
- Duration and angle are optional and not validated (passed through).

## Dependencies

- `RobotApiDispatcher` (for API invocation)
- `ExecutionContext` (for stack and PC)
- No HAL, no hardware, no GPIO.

## Testing

Unit tests in `tests/runtime/motion_instruction_test.cpp` verify:
- Operand validation.
- Correct `RobotApiRequest` creation.
- Error handling.
- PC advancement.

End-to-end tests in `tests/runtime/motion_pipeline_test.cpp` verify the complete pipeline from Program to DummyRobotAPI.

## Future Extensions

- Add more motion commands (e.g., `MOVE_TIME`, `MOVE_ANGLE`).
- Support duration and angle semantics.
- Add calibration parameters.