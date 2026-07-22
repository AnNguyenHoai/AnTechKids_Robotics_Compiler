# COMPILER_PIPELINE.md

> Version: 1.0  
> Status: Draft  
> Owner: Robot Compiler Team  
> Milestone: RoboSim → Real Robot MVP

---

# 1. Purpose

This document defines the complete compilation pipeline of the Robot Development Platform.

It specifies:

- Compiler architecture
- Compilation stages
- Data flow
- Intermediate representations
- Responsibilities of each stage
- Inputs and outputs
- Extension points

This document is the blueprint for implementing the Robot Compiler.

---

# 2. Design Goals

The compiler is designed with the following principles:

- Frontend independent
- Hardware independent
- Deterministic
- Incrementally extensible
- Easy to test
- Easy to optimize

The compiler must never depend directly on RoboSim.

RoboSim is only one possible frontend.

---

# 3. Overall Architecture

```
                    RoboSim

                       │

             Python Robot DSL

                       │

                Source Reader

                       │

                     Parser

                       │

                       AST

                       │

              Semantic Analyzer

                       │

              RoboSim API Resolver

                       │

             Platform API Mapping

                       │

                  Platform IR

                       │

                  IR Optimizer

                       │

                Bytecode Builder

                       │

                 Binary Linker

                       │

           generated_program.h

                       │

                  ESP32 Firmware
```

---

# 4. Compiler Responsibilities

The compiler is responsible for

- Reading source files
- Parsing syntax
- Semantic validation
- API resolution
- IR generation
- Optimization
- Bytecode generation
- Symbol resolution
- Binary generation

The compiler is NOT responsible for

- Robot motion
- Line following
- PID
- Servo control
- Hardware drivers
- Thread scheduling

These belong to Runtime.

---

# 5. Compiler Stages

The compiler consists of eight stages.

```
Stage 1

Source Reader

↓

Stage 2

Parser

↓

Stage 3

Semantic Analysis

↓

Stage 4

API Resolution

↓

Stage 5

Platform IR Generation

↓

Stage 6

Optimization

↓

Stage 7

Bytecode Generation

↓

Stage 8

Linking
```

---

# 6. Stage 1 – Source Reader

Input

```
Python Source File
```

Responsibilities

- Read UTF-8 source
- Normalize line endings
- Record source locations
- Handle multiple files (future)

Output

```
Source Buffer
```

---

# 7. Stage 2 – Parser

Input

```
Source Buffer
```

Responsibilities

- Build Python AST
- Detect syntax errors
- Preserve source locations

Output

```
Python AST
```

No semantic checking occurs here.

---

# 8. Stage 3 – Semantic Analysis

Input

```
Python AST
```

Responsibilities

Validate

- function existence
- variable declarations
- constant usage
- thread entry points
- supported statements
- supported expressions

Reject

- class
- lambda
- async
- generator
- unsupported imports
- unsupported builtins

Output

```
Validated AST
```

---

# 9. Stage 4 – RoboSim API Resolution

Purpose

Convert RoboSim API into Platform API.

Example

```
rcu.SetMoveRun()

↓

move.run()
```

Example

```
rcu.line_basis()

↓

line.follow()
```

The compiler no longer remembers RoboSim names.

Output

```
Platform API Tree
```

---

# 10. Stage 5 – Platform IR Generation

Purpose

Generate compiler intermediate representation.

Input

```
Platform API Tree
```

Output

```
Platform IR
```

Example

```
CALL_API

move.run

direction

speed
```

IR contains

- Functions
- Basic Blocks
- Instructions
- Variables
- Labels

---

# 11. Stage 6 – Optimization

Input

```
Platform IR
```

Output

```
Optimized Platform IR
```

Current optimizations

### Constant Folding

```
5+5

↓

10
```

### Dead Code Removal

```
WAIT 0

↓

Remove
```

### Constant Propagation

```
speed=70

↓

Replace
```

### Instruction Merge

```
Servo(90)

Servo(90)

↓

Servo(90)
```

### Empty Block Removal

```
Block

Jump

↓

Remove
```

Future optimizations may be added without changing the frontend.

---

# 12. Stage 7 – Bytecode Generation

Input

```
Platform IR
```

Responsibilities

- Assign opcode
- Encode operands
- Resolve labels
- Build constant pool
- Allocate function IDs

Output

```
Bytecode Image
```

---

# 13. Stage 8 – Linking

Responsibilities

- Merge functions
- Resolve references
- Generate metadata
- Generate header file

Output

```
generated_program.h
```

Example

```cpp
const uint8_t program[]={
...
};
```

---

# 14. Compiler Data Flow

```
Source

↓

AST

↓

Validated AST

↓

Platform API

↓

Platform IR

↓

Optimized IR

↓

Bytecode

↓

Header
```

Each stage has a single input and a single output.

---

# 15. Error Handling

Compiler errors are divided into

### Syntax Error

Parser stage

Example

```
Missing :
```

---

### Semantic Error

Example

```
Undefined Function
```

---

### API Error

Example

```
Unknown RoboSim API
```

---

### Type Error

Example

```
Expected Integer

Got String
```

---

### Internal Error

Compiler bug.

Should never occur.

---

# 16. Symbol Table

Compiler maintains

```
Functions

Variables

Constants

Labels

API References
```

Symbol table exists only during compilation.

It is not stored inside bytecode.

---

# 17. Constant Pool

Compiler stores

```
0

1

50

70

1000

"forward"

"backward"
```

Instructions reference constants by index.

Duplicate constants are merged.

---

# 18. Function Management

Each function receives

```
Function ID
```

Example

```
0

robot_initialize
```

```
1

task1
```

```
2

task2
```

Calls reference IDs instead of names.

---

# 19. Thread Registration

Compiler records

```
THREAD_START

Function ID
```

Example

```
task1

↓

Thread 0
```

```
task2

↓

Thread 1
```

Runtime decides scheduling.

---

# 20. Source Mapping

Every instruction keeps

```
Source File

Line Number

Column
```

Useful for

- Debugging
- Error reporting
- Simulator integration

---

# 21. Generated Artifacts

Compiler produces

```
generated_program.h

program.map

(optional)

program.json

(optional)
```

Future

```
Debug Symbols

Coverage Data
```

---

# 22. Extension Points

Future frontends

```
Scratch

Blockly

Visual Programming

Python SDK
```

Only need to generate

```
Platform API
```

Compiler remains unchanged.

---

# 23. Compiler Layers

```
Frontend

↓

Semantic

↓

Platform

↓

Optimization

↓

Backend
```

Each layer only communicates with adjacent layers.

---

# 24. Testing Strategy

Every stage has independent tests.

### Parser Tests

AST correctness.

### Semantic Tests

Language validation.

### API Tests

Mapping correctness.

### IR Tests

Instruction generation.

### Optimizer Tests

Transformation correctness.

### Backend Tests

Bytecode generation.

### Integration Tests

Compile complete RoboSim programs.

---

# 25. Performance Goals

Compilation should satisfy

- Deterministic output
- Linear complexity for typical RoboSim projects
- No runtime reflection
- Minimal heap allocation
- Incremental optimization ready

---

# 26. Compatibility Policy

The compiler guarantees compatibility with

```
ROBOSIM_LANGUAGE_SPEC.md
```

and

```
ROBOSIM_API_SPEC.yaml
```

It does not guarantee compatibility with arbitrary Python code.

---

# 27. Design Principles

The compiler shall

- Never access hardware.
- Never implement robot algorithms.
- Never perform motor control.
- Never execute user code.

Its only responsibility is transforming source code into executable bytecode.

---

# 28. Future Evolution

The architecture allows future additions without redesign.

Possible extensions

- Multiple robot platforms
- Multiple bytecode versions
- JIT execution
- Native code backend
- LLVM backend
- Static analysis
- Visual debugger
- Source-level debugging

---

# 29. Success Criteria

The compiler pipeline is considered complete when:

- All RoboSim-generated programs parse successfully.
- Semantic validation is deterministic.
- Every RoboSim API maps to Platform API.
- Platform IR is generated correctly.
- Optimizer preserves program semantics.
- Bytecode is generated successfully.
- Firmware builds without modification.
- Robot behavior matches RoboSim simulation.

---

# 30. Pipeline Summary

```
           RoboSim

              │

      Python Robot DSL

              │

        Source Reader

              │

           Parser

              │

             AST

              │

     Semantic Analyzer

              │

   RoboSim API Resolver

              │

    Platform API Mapping

              │

        Platform IR

              │

        IR Optimizer

              │

     Bytecode Generator

              │

      Binary Linker

              │

    generated_program.h

              │

        ESP32 Firmware

              │

          Real Robot
```

---

# Appendix A — Compiler Boundaries

| Component | Responsibility |
|-----------|----------------|
| Frontend | Parse RoboSim DSL |
| Semantic | Validate language rules |
| API Resolver | Convert RoboSim API to Platform API |
| IR Generator | Produce canonical compiler IR |
| Optimizer | Improve IR without changing semantics |
| Backend | Generate bytecode |
| Linker | Produce firmware-ready artifacts |

---

# Appendix B — Philosophy

The Robot Compiler is **not a Python compiler**.

It is a **Robot DSL Compiler** whose current frontend happens to use Python syntax.

This distinction keeps the compiler small, deterministic, and focused on executing robot behaviors rather than supporting the full Python language.