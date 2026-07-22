# BYTECODE_SPEC.md

> Version: 1.0
> Status: Draft
> Owner: Robot Runtime Team
> Milestone: RoboSim → Real Robot MVP

---

# 1. Purpose

This document defines the executable bytecode format of the Robot Development Platform.

Bytecode is the interface between

- Compiler
- Virtual Machine

The bytecode is

- platform independent
- deterministic
- compact
- versioned

---

# 2. Design Philosophy

Robot Bytecode is **API-Centric**.

The VM is responsible for

- control flow
- execution
- scheduling

The Robot Runtime is responsible for

- motion
- sensors
- PID
- hardware

Therefore

Robot algorithms SHALL NOT be expanded into primitive instructions.

Example

```

LINE_FOLLOW

```

instead of

```

READ

COMPARE

PWM

...

```

---

# 3. Bytecode Architecture

```

Compiler

↓

Platform IR

↓

Bytecode

↓

VM

↓

RobotAPI

↓

HAL

↓

Hardware

```

---

# 4. Bytecode Image

A bytecode image contains

```

Header

Constant Pool

Function Table

Instruction Stream

Metadata

```

---

# 5. Header

```

Magic Number

Version

Instruction Count

Function Count

Constant Count

Checksum

```

---

# 6. Constant Pool

Contains

```

Integer

Float

String

Boolean

```

Constants are deduplicated.

---

# 7. Function Table

Each function stores

```

Function ID

Entry Offset

Instruction Count

```

---

# 8. Instruction Format

Every instruction

```

Opcode

Operand Count

Operands

```

Variable length encoding.

---

# 9. Operand Types

```

Immediate

Constant Index

Variable Index

Function ID

Label

API Enum

```

---

# 10. Instruction Categories

Robot Instructions

VM Instructions

Memory Instructions

Control Instructions

Thread Instructions

---

# 11. Robot Instructions

Motion

```

MOVE_INITIALIZE

MOVE_RUN

MOVE_RUN_TIME

MOVE_RUN_DISTANCE

MOVE_SPEED

MOVE_STOP

```

---

Servo

```

SERVO_SET

STEERING_SET

STEERING_HOLD

```

---

Motor

```

MOTOR_SET

MOTOR_SERVO

MOTOR_STRAIGHT

```

---

Sensor

```

READ_TRACE

```

---

Line

```

LINE_FOLLOW

LINE_TIME

LINE_STOP_INTERSECTION

LINE_TURN

LINE_BITMAP

```

---

Peripheral

```

LED

RGB

BUZZER

```

---

Timing

```

WAIT

```

---

# 12. VM Instructions

```

LOAD_CONST

LOAD_VAR

STORE_VAR

```

Arithmetic

```

ADD

SUB

MUL

DIV

MOD

```

Comparison

```

EQ

NE

GT

LT

GE

LE

```

Logical

```

AND

OR

NOT

```

---

# 13. Control Flow

```

JUMP

JUMP_IF_TRUE

JUMP_IF_FALSE

CALL

RETURN

```

---

# 14. Thread

```

THREAD_START

THREAD_END

```

---

# 15. Variable Model

Variables referenced by ID.

```

v0

v1

v2

```

---

# 16. Execution Cycle

```

Fetch

↓

Decode

↓

Dispatch

↓

Execute

↓

Next

```

---

# 17. Blocking Instruction

Blocking instructions suspend the current thread.

Examples

```

WAIT

MOVE_RUN_TIME

LINE_FOLLOW

```

Scheduler switches to another READY thread.

---

# 18. Non Blocking Instruction

Examples

```

MOVE_RUN

SERVO

LED

```

Execution continues immediately.

---

# 19. Versioning

Every bytecode image stores

```

Major

Minor

Patch

```

VM rejects incompatible versions.

---

# 20. Validation

VM validates

Magic Number

Version

Checksum

Instruction Range

Opcode Validity

Function Table

before execution.

---

# 21. Determinism

Same bytecode

+

Same sensor input

↓

Same robot behavior.

---

# 22. Backward Compatibility

New instructions

↓

New opcodes

Existing opcodes never change semantics.

---

# 23. Opcode Allocation

```

0x0000

Reserved

0x0001~0x00FF

VM

0x0100~0x01FF

Motion

0x0200~0x02FF

Motor

0x0300~0x03FF

Servo

0x0400~0x04FF

Sensor

0x0500~0x05FF

Line

0x0600~0x06FF

Peripheral

```

---

# 24. Execution Boundary

Compiler produces bytecode.

VM executes bytecode.

RobotAPI controls hardware.

These responsibilities never overlap.

---

# 25. Success Criteria

The bytecode specification is complete when

- every Platform IR instruction lowers into bytecode
- VM executes every opcode
- Robot behavior matches RoboSim