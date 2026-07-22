# Robot Runtime

This package provides the runtime representation of a compiled robot program, independent from the compiler internals.

## Components

### RuntimeProgram
Immutable container for a complete program ready for execution. Contains:
- Constant pool
- Function table
- Flat list of instructions
- Entry function ID

### RuntimeFunction
Represents a function in the program, with its instruction range and metadata.

### RuntimeInstruction
Decoded instruction with opcode and operand values (all types resolved). The VM will execute these directly.

### ProgramLoader
Converts a `BinaryProgram` (from compiler) into a `RuntimeProgram`. Performs validation, decoding, and resolution. Throws specific exceptions for invalid binaries.

### InstructionIterator
Provides iteration over instructions of a function or the entire program. Supports `current()`, `next()`, `jump()`, `seek()`, `has_next()`, `peek()`. This is the single interface for instruction access by the VM.

## Object Lifecycle

1. Compiler produces `BinaryProgram`.
2. `ProgramLoader.load(binary_prog)` -> `RuntimeProgram`.
3. `InstructionIterator` created from `RuntimeProgram` to traverse instructions.
4. VM uses iterator to fetch and execute instructions.

## Ownership

- `RuntimeProgram` is immutable and can be shared.
- `InstructionIterator` holds a reference to the program and maintains a cursor; it is not thread-safe.

## Future Extensions

- Debugger and profiler can hook into `InstructionIterator`.
- Additional metadata can be added to `RuntimeProgram` without breaking compatibility.