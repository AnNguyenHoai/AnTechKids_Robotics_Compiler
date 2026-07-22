# robot-common

Shared core library for Robot Development Platform.

Provides:
- Opcode enumeration
- Operand (type‑safe variant)
- Instruction
- Function
- Program
- ConstantPool (deduplicated constants)
- OpcodeRegistry (meta‑information)
- ProgramPrinter (human‑readable disassembly)

All classes are header‑only except for the registry, pool, and printer.