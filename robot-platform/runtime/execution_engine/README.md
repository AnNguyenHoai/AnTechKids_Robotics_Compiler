# Execution Engine

This directory contains the Execution Engine components of the Robot Runtime.

## Architecture Overview

The Execution Engine is a composition of focused, single‑responsibility components that together form the runtime state container for executing robot bytecode.

### Component Diagram
+---------------------+
| ExecutionEngine |
+---------------------+
|
+---------------------------+
| |
v v
+-----------------+ +----------------------+
| ExecutionContext | | Scheduler |
+-----------------+ +----------------------+
|
+---------------------------+
| |
v v
+------------------+ +------------------+
| ProgramCounter | | OperandStack |
+------------------+ +------------------+
| CallStack | | VariableTable |
+------------------+ +------------------+
| ExecutionFlags | | (State) |
+------------------+ +------------------+

text

### Dispatcher Architecture

The instruction dispatch flow follows a clean pipeline:
InstructionDispatcher
|
v
InstructionRegistry (metadata lookup)
|
v
InstructionFactory (create handler)
|
v
InstructionHandler (execute)
|
v
ExecutionResult (diagnostic)

text

**Components:**

- **InstructionRegistry**: Stores metadata (opcode, name, category, semantic, operand count, supported, deprecated). Uses enums (`InstructionCategory`, `Semantic`) instead of strings for type safety.
- **InstructionFactory**: Creates the appropriate `InstructionHandler` for a given opcode. Currently always returns `UnknownInstructionHandler`.
- **InstructionHandler**: Abstract interface for executing instructions. Each opcode will have its own concrete handler in future sprints.
- **InstructionContext**: Provides handlers with access to `ExecutionContext`, `RuntimeServices`, and `RobotAPIDispatcher` in a controlled manner.
- **UnknownInstructionHandler**: Default handler for unsupported opcodes; returns a failure result without crashing.

### Error Flow

1. Dispatcher receives opcode.
2. Looks up metadata in Registry (optional).
3. Factory creates handler.
4. Handler validates (currently stub).
5. Handler executes (currently stub).
6. ExecutionResult is returned with status, error code, program counter, layer, opcode ID, and execution time.

All errors are reported via `ExecutionResult`; no exceptions are thrown in the dispatch path.

## Runtime Exceptions

The execution engine defines a hierarchy of exceptions for fatal errors (stack overflow, variable not found, etc.), but the dispatcher uses `ExecutionResult` for expected error conditions.

## Future Sprints

After this implementation, the following components will be implemented:

1. **Opcode Handlers** – concrete implementations for each instruction.
2. **RobotAPI Dispatcher** – API call routing.
3. **Runtime Services** – timer, memory, loader, etc.
4. **Scheduler** – actual scheduling logic.

## Build & Test

The engine compiles successfully and unit tests pass. No hardware or external dependencies are required.

# Execution Engine

## Core Instruction Set

The following core instructions are implemented:

- `NOP` – No operation, advances PC.
- `END` – Terminates execution.
- `WAIT` – Non-blocking wait (sets waiting flag; does not block MCU).
- `JUMP` – Unconditional jump to target address.
- `JUMP_IF` – Conditional jump based on boolean condition.
- `LOAD_CONST` – Load constant onto operand stack.
- `STORE` – Store value from operand stack to variable.
- `LOAD` – Load variable value onto operand stack.
- `RETURN` – Return from function (restores call stack).

All handlers follow the `InstructionHandler` interface and are registered via `InstructionFactory`.

## Execution Flow

1. Program is loaded into `ExecutionEngine`.
2. `initialize()` sets PC to 0.
3. `execute()` repeatedly calls `executeStep()`.
4. `executeStep()` fetches instruction from program, dispatches via `InstructionDispatcher`.
5. Dispatcher looks up metadata, creates handler via Factory, and executes.
6. Handler modifies `ExecutionContext` (PC, stacks, variables, flags).
7. Result is returned as `ExecutionResult`.

## Testing

Unit tests verify each instruction's behavior, including stack operations, variable access, and control flow.

## Future Extensions

- Add robot instructions (Move, Sensor, etc.)
- Implement actual WAIT with scheduler.
- Add more data types to RuntimeValue.