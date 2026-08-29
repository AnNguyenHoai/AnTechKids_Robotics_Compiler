# C6 — Compiler ↔ Firmware ISA Contract Recovery

Implemented fixes:
- Firmware opcode header synchronized from `robot-language/generated/opcode.h`.
- VM Instruction ABI migrated to `opcode + p1 + p2 + p3 + p4`.
- `LineBasis`, `LineFollow`, and `LineStop` are dispatched by the VM.
- RobotAPI bridges line opcodes to `LineFollower` and applies the canonical sensor mask contract: bit2=Left, bit1=Center, bit0=Right.
- `tools/check_isa_contract.py` detects future opcode-map or Instruction ABI drift.

`LineBasis` and `LineFollow` are currently non-blocking control ticks. User loops remain responsible for repeated execution and timing.
