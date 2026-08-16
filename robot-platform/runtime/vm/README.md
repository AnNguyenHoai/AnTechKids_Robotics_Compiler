# Virtual Machine

This module implements the core Virtual Machine that executes a loaded Program.

## Architecture
Program
|
v
VirtualMachine
|
+--- FetchStage (fetches instruction at PC)
| |
| v
+--- ExecuteStage (dispatches to InstructionDispatcher)
| |
| v
+--- InstructionDispatcher
| |
| v
+--- InstructionHandler
| |
| v
+--- ExecutionResult
|
+--- VMStatistics (tracks instructions, time, errors)
|
+--- VMState (state machine)

text

## Execution Loop

1. `run()` calls `start()` then loops:
   - Check if running
   - `step()`: fetch, execute, update statistics
   - Check for completion/error/pause/stop
2. `step()` can be called individually for single-stepping.
3. `pause()`/`resume()` control execution.

## States

- `Created` – VM created, no program.
- `Loaded` – Program loaded.
- `Ready` – Program initialized, ready to start.
- `Running` – Executing instructions.
- `Paused` – Temporarily halted.
- `Completed` – Program finished (END instruction).
- `Stopped` – Explicitly stopped.
- `Error` – Fatal error during execution.

## Statistics

- Instruction count
- Execution time (microseconds)
- Error count

## Callback

A step callback can be registered for debugging/tracing.

## Integration

The `ExecutionEngine` delegates to `VirtualMachine` for all execution operations. The VM is independent of RobotAPI and HAL.

## Future Extensions

- Breakpoint support
- Debugger interface
- Profiling/tracing
- Multi-threading