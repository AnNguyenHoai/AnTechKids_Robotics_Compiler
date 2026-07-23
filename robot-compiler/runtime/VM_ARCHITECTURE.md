# Virtual Machine Architecture

## Overview

The Virtual Machine (VM) executes a `RuntimeProgram` produced by the `ProgramLoader`. It is a simple, deterministic, single-threaded interpreter that communicates with hardware through a `MockRobotAPI` (or later, a real RobotAPI).

## Execution Lifecycle

1. **Load**: `VM.load(RuntimeProgram)` – initializes context and sets up instruction iterator.
2. **Run**: `VM.run()` – executes instructions until the program finishes or is stopped.
3. **Step**: `VM.step()` – executes a single instruction.
4. **Stop**: `VM.stop()` – halts execution.
5. **Reset**: `VM.reset()` – resets the VM to initial loaded state.

## Components

### ExecutionContext

Holds the CPU state:
- `program_counter` – current instruction index.
- `call_stack` – return addresses for CALL/RETURN.
- `data_stack` – general-purpose stack.
- `current_function_id` – currently executing function.
- `state` – one of CREATED, LOADED, RUNNING, PAUSED, STOPPED, FINISHED.
- `flags` – condition flags (future).
- `registers` – optional general-purpose registers.

### InstructionIterator

Provides sequential access to instructions. Supports:
- `current()` – get current instruction.
- `next()` – advance and return next instruction.
- `seek(index)` – move to specific instruction.
- `jump(index)` – alias for `seek`.
- `has_next()` – check if more instructions exist.
- `peek(offset)` – look ahead.
- `reset()` – reset to beginning.

### Dispatcher

Maps `RobotOpcode` to a handler function and invokes it.

### Opcode Handlers

Each opcode family has its own handler module:
- `move_handler`: MOVE_RUN, MOVE_RUN_TIME, MOVE_STOP
- `wait_handler`: WAIT
- `jump_handler`: JUMP, JUMP_IF
- `call_handler`: CALL, RETURN

Handlers update `context.program_counter` appropriately and call `MockRobotAPI` methods.

### MockRobotAPI

Stub implementation of robot hardware control. Records actions and prints to console.

## State Machine
CREATED -> LOADED -> RUNNING -> (PAUSED) -> STOPPED -> FINISHED

text

Invalid transitions raise exceptions.

## Future Extensions

- Real RobotAPI integration.
- Multithreading / scheduler.
- Debugger and profiler.
- Interrupt handling.
- Optimizations (JIT?).

## Debugging

The VM supports single-step execution via `step()`, which can be used by a debugger without modifying the VM core.