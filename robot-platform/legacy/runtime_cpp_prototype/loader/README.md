# Program Loader

This module loads compiled bytecode into an executable Runtime Program.

## Architecture
Bytecode (binary)
|
v
BytecodeReader (reads header, constants, instructions)
|
v
InstructionDecoder (decodes raw instructions into internal format)
|
v
ProgramLoader (validates, builds Program)
|
v
Program (immutable runtime representation)
|
v
ExecutionEngine (executes)

text

## Components

- **BytecodeReader**: Reads raw byte stream, validates magic, version, checksum. Extracts header, constant pool, and raw instructions.

- **InstructionDecoder**: Converts raw `BytecodeInstruction` to `DecodedInstruction` with operands. Validates opcode against known set.

- **ProgramLoader**: Orchestrates the loading pipeline. Validates header, decodes instructions, builds constant pool, and creates an immutable `Program`.

- **Program**: Immutable container holding instructions, constant pool, entry point, and metadata.

- **ConstantPool**: Stores constants (integers, booleans, future types) accessible by index.

## Validation Rules

- Magic number must match `MAGIC_NUMBER`.
- Major version must match `BYTECODE_VERSION_MAJOR`.
- Entry point must be within instruction range.
- All opcodes must be known.

## Error Handling

All errors are returned as `ExecutionResult` with descriptive messages.

## Future Extensions

- Support debug symbols.
- Add source mapping.
- Support breakpoint tables.
- Add line information.
- Extend constant pool with float, string, array.