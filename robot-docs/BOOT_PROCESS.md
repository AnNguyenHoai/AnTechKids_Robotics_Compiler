# Boot Process

## Sequence
1. **Power On**: ESP32 boots.
2. **Serial Init**: Baud rate 115200.
3. **Hardware Init**: `RobotAPI::Initialize()` configures PWM and GPIO.
4. **Diagnostics**: Battery, memory, flash checks.
5. **Program Load**: `ProgramLoader::LoadFromGenerated()` copies instructions.
6. **VM Init**: Program counter set to 0.
7. **Execution Started**: VM begins stepping through instructions.

## Logging
All stages are logged with timestamps:
- `[BOOT]`: System startup.
- `[DIAG]`: Hardware checks.
- `[EXEC]`: Program execution.
- `[ERROR]`: Fatal issues.
- `[STABILITY]`: Test iterations.

## Error Codes
| Code | Meaning |
|------|---------|
| 1    | Invalid opcode |
| 2    | Program overflow |
| 3    | Invalid jump target |
| 4    | Call stack overflow |
| 5    | Return without call |
| 6    | Division by zero |
| 7    | Modulo by zero |