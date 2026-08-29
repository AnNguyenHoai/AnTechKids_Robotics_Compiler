# Sensor Instruction Package

This package implements sensor reading instructions for the Robot VM.

## Instructions

| Instruction | Opcode | Operands | Description |
|-------------|--------|----------|-------------|
| `READ_ULTRASONIC` | ReadUltrasonic | port (int) | Read ultrasonic distance in cm, push integer |
| `READ_LINE` | ReadLine | port (int), channel (int) | Read line sensor (0/1), push integer |
| `READ_LIGHT` | ReadLight | port (int) | Read light sensor raw value, push integer |
| `READ_TOUCH` | ReadTouch | port (int) | Read touch sensor state (0/1), push integer |
| `READ_COLOR` | ReadColor | none | Read color sensor, push integer |

## Execution Semantics

Each sensor instruction:
1. Pops required operands from the operand stack.
2. Builds a `RobotApiRequest` with appropriate `ApiId`.
3. Dispatches via `RobotApiDispatcher`.
4. On success, pushes the returned `RuntimeValue` onto the operand stack.
5. Advances the program counter.

## Operand Stack Usage

- Ultrasonic: `[port]` → `[distance]`
- Line: `[port, channel]` → `[value]`
- Light: `[port]` → `[value]`
- Touch: `[port]` → `[value]`
- Color: `[]` → `[value]`

## Validation

- Port must be valid (currently only port 1 is supported).
- Port and channel must be integers.
- Sufficient operands must be present.

## Dependencies

- `RobotApiDispatcher` (for API invocation)
- `ExecutionContext` (for stack and PC)
- No HAL, no hardware, no GPIO.

## Testing

End-to-end tests verify:
- Sensor values are correctly pushed onto operand stack.
- Comparison and jump instructions work with sensor values.
- Invalid ports are handled gracefully.
- RobotAPI failures are propagated.