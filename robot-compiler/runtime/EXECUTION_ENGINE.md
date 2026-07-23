# Execution Engine

## Overview

The Execution Engine is the core of the Virtual Machine. It manages the runtime state, including:

- Program counter
- Call stack and stack frames
- Data stack
- Variable tables (global and local)
- Control flow (jumps, calls, returns)
- Arithmetic and comparison operations

The engine is independent of the dispatcher and opcode handlers.

## Components

### ExecutionContext

Holds all runtime state:
- `program_counter`: current instruction index
- `call_stack`: list of `StackFrame` objects
- `data_stack`: stack for temporary values
- `global_vars`: `VariableTable` for global variables
- `local_vars`: current function's local variables
- `state`: execution state (CREATED, LOADED, RUNNING, ...)

### StackFrame

Represents a function activation:
- `function_id`: ID of the function
- `return_address`: instruction index to return to
- `local_vars`: `VariableTable` for local variables

### VariableTable

A hierarchical table for variables:
- `get(name)`: retrieve value
- `set(name, value)`: update value
- `define(name, value)`: create new variable
- Supports parent chain for scoping

### RuntimeValue

Type-safe value hierarchy:
- `IntegerValue`, `FloatValue`, `BooleanValue`, `StringValue`, `ReferenceValue`

### ExecutionEngine

Provides high-level operations:
- Stack: `push()`, `pop()`, `peek()`
- Variables: `get_variable()`, `set_variable()`, `get_variable_by_index()`, `set_variable_by_index()`
- Control: `jump()`, `call()`, `return_()`
- Arithmetic: `add()`, `sub()`, `mul()`, `div()`, `mod()`, `pow()`, `neg()`
- Comparison: `compare()`

## Execution Lifecycle

1. `VirtualMachine.load()` loads a `RuntimeProgram` into the engine.
2. `VirtualMachine.run()` repeatedly calls `step()`.
3. `step()` fetches the current instruction via `InstructionIterator`.
4. `Dispatcher` finds the appropriate handler and invokes it with the engine.
5. The handler uses engine methods to manipulate state and control flow.
6. The engine updates `program_counter` and iterator.

## Memory Management

- Variables are stored in `VariableTable` (owned by frames or global).
- Temporary values are stored on the `DataStack`.
- No garbage collection is needed; frames are popped on return.