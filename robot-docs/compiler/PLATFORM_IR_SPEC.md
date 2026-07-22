# PLATFORM_IR_SPEC.md

> Version: 1.0
> Status: Draft
> Milestone: RoboSim → Real Robot MVP
> Owner: Robot Compiler Team

---

# 1. Purpose

This document defines the **Platform Intermediate Representation (Platform IR)** used by the Robot Compiler.

Platform IR is the canonical internal representation between the Frontend and the Bytecode Generator.

It is completely independent of:

- RoboSim
- Python AST
- Blockly
- Scratch
- Robot Hardware

Every frontend must be translated into Platform IR.

Every backend consumes Platform IR.

---

# 2. Compiler Pipeline

```

RoboSim

↓

Python AST

↓

Semantic Analysis

↓

Platform API

↓

Platform IR

↓

Optimizer

↓

Bytecode

↓

VM

```

Platform IR is the only representation optimized by the compiler.

---

# 3. Design Goals

Platform IR is designed to be

- Small
- Strongly Typed
- Deterministic
- Easy to Optimize
- Easy to Serialize

Platform IR is NOT designed to be human friendly.

---

# 4. IR Structure

A program consists of

```

Program

├── Function

│ ├── BasicBlock

│ │ ├── Instruction

│ │ ├── Instruction

│ │ └── ...

│ └── ...

└── ...

```

---

# 5. Program

```

Program

```

Contains

- Global Constants
- Functions
- Metadata

Example

```

Program

Functions:

robot_initialize

task1

task2

```

---

# 6. Function

A function contains

```

Function

Name

Parameters

Basic Blocks

```

Example

```

Function

Name:

task1

```

---

# 7. Basic Block

Basic Block

Definition

> A sequence of instructions with

- one entry

- one exit

Example

```

Block 0

MoveRun

Wait

Jump

```

No branch exists inside a block.

---

# 8. Instruction

Instruction is the smallest executable unit.

Structure

```

Opcode

Operands

Result

Metadata

```

Example

```

MOVE_RUN

forward

50

```

---

# 9. Operand

Operand types

```

Immediate

Constant

Variable

Label

API

```

Example

```

Immediate

70

```

```

Variable

sensor

```

---

# 10. Value Types

Supported types

```

Integer

Float

Boolean

String

Void

```

---

# 11. Variables

Variables are represented by IDs.

Example

```

v0

v1

v2

```

Compiler keeps symbol table separately.

---

# 12. Constants

Constant Pool

```

0

1

50

70

1000

"forward"

```

Instructions reference constants by ID.

---

# 13. Labels

Every branch target has a label.

Example

```

L0

L1

L2

```

---

# 14. Control Flow

Supported

```

Jump

Conditional Jump

Return

Call

```

Example

```

IF

↓

JUMP_TRUE L3

```

---

# 15. API Call

High level robot APIs become

```

CALL_API

```

Example

```

CALL_API

move.run

direction

speed

```

Platform IR never stores RoboSim names.

---

# 16. Arithmetic

Supported

```

ADD

SUB

MUL

DIV

MOD

```

---

# 17. Comparison

Supported

```

EQ

NE

GT

LT

GE

LE

```

---

# 18. Logical

Supported

```

AND

OR

NOT

```

---

# 19. Memory Operations

Supported

```

LOAD_CONST

LOAD_VAR

STORE_VAR

```

---

# 20. Function Call

Supported

```

CALL

RETURN

```

Compiler resolves addresses later.

---

# 21. Thread

Thread creation

```

THREAD_START

function_id

```

VM decides scheduling policy.

---

# 22. Optimizer Input

Optimizer receives Platform IR.

```

Platform IR

↓

Optimizer

↓

Platform IR

```

Optimizer never edits AST.

---

# 23. Optimizations

Examples

### Constant Folding

```

5+5

↓

10

```

---

### Dead Code

```

WAIT 0

↓

Remove

```

---

### Instruction Merge

```

Servo(90)

Servo(90)

↓

Servo(90)

```

---

### Empty Block Removal

```

Block

Jump

↓

Remove

```

---

### Constant Propagation

```

speed=70

↓

Replace

```

---

# 24. Lowering

Lowering converts Platform IR

↓

Bytecode

Example

```

CALL_API

↓

MOVE_RUN

```

---

# 25. Debug Information

Platform IR keeps

```

Source File

Line Number

Function

```

Useful for debugging.

---

# 26. Validation

IR Validator checks

- Missing Labels
- Invalid Types
- Invalid API
- Unreachable Block
- Empty Function

Compilation stops if validation fails.

---

# 27. Serialization

Platform IR can be serialized.

Future formats

```

Binary

JSON

YAML

```

---

# 28. Compatibility

Every frontend must generate equivalent Platform IR.

Example

RoboSim

```

SetMoveRun()

```

Scratch

```

Move Forward

```

Blockly

```

Drive Forward

```

↓

All become

```

CALL_API

move.run

```

---

# 29. Relationship

```

AST

↓

Platform API

↓

Platform IR

↓

Bytecode

↓

VM

```

Platform IR is the canonical compiler representation.

---

# 30. Success Criteria

Platform IR implementation is complete when

- Every supported frontend generates Platform IR.
- Optimizer operates only on Platform IR.
- Bytecode generator consumes Platform IR.
- Runtime behavior matches RoboSim simulation.