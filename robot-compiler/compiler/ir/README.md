# Platform Intermediate Representation (IR)

## Why Platform IR?

The Robot Compiler must support multiple frontends (RoboSim, Blockly, Scratch, etc.)
and multiple backends (ESP32, Arduino, etc.). Connecting frontends directly to
backends creates tight coupling and makes the system hard to extend.

Platform IR is the **canonical internal language** of the compiler.

Every frontend lowers its source to Platform IR.
Every backend consumes Platform IR.

## Why Not Generate Robot ISA Directly?

RoboSim and other frontends represent high‑level robot missions
(e.g., "move forward 50 cm"). Lowering directly to low‑level Robot ISA
(such as PWM, motor control) would embed algorithm details into the compiler.

Platform IR preserves the semantic intent of the mission.
Optimization, analysis, and transformation happen on IR.
Robot ISA is generated at the very end.

## Architecture Position
Frontend (RoboSim, Blockly, ...)
│
▼
AST
│
▼
Platform IR ←── This package
│
▼
Optimizer (future)
│
▼
Robot ISA (future)
│
▼
Binary

text

## Future Extensions

- Optimizations (constant folding, dead code elimination)
- Static analysis (variable liveness, type inference)
- Multiple backends (ESP32, Arduino, simulator)
- Debug information

## Package Contents

- `IRProgram`: top‑level container
- `IRFunction`: one function
- `IRBasicBlock`: sequence of instructions
- `IRInstruction`: one operation
- `IRValue`: typed value (constant, variable, temporary)
- `IRBuilder`: helper to build IR
- `IRPrinter`: human‑readable output