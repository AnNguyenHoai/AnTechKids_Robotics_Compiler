# EXECUTION_ENGINE_MODEL.md

Version: 1.0

Status: Architecture Freeze

Owner: Robot Platform Team

---

# 1. Purpose

This document defines the execution model of the Robot Platform.

It specifies how Robot Bytecode is executed by the Execution Engine.

This document is independent of

- MCU
- HAL
- Hardware
- Operating System

It describes execution semantics only.

---

# 2. Execution Philosophy

The Execution Engine is responsible for transforming Robot Bytecode into observable robot behaviour.

The Execution Engine is NOT

- a compiler
- a hardware driver
- a robot algorithm

It is a deterministic virtual execution environment.

The same bytecode shall always produce the same logical behaviour on every supported platform.

---

# 3. Execution Pipeline

Every Robot Program follows exactly one execution pipeline.

```

Blockly

↓

Python

↓

Frontend

↓

Compiler

↓

Robot Bytecode

↓

Execution Engine

↓

RobotAPI

↓

HAL

↓

Hardware

```

Execution begins only after compilation has completed successfully.

---

# 4. Program Lifecycle

Every program follows the same lifecycle.

```

Compiled

↓

Loaded

↓

Initialized

↓

Ready

↓

Running

↓

Paused

↓

Running

↓

Completed

↓

Unloaded

```

Failure transitions

```

Running

↓

Runtime Error

↓

Terminated

↓

Unloaded

```

---

# 5. Runtime Instance

Every running program owns one Runtime Instance.

A Runtime Instance contains

Execution Context

Runtime Services

Scheduler State

Program State

RobotAPI Reference

Timer State

The Runtime Instance represents one executing robot program.

---

# 6. Execution Context

Execution Context represents the logical state of execution.

It owns

Program Counter

Operand Stack

Call Stack

Variable Table

Temporary Registers

Flags

Execution Context SHALL NEVER own hardware resources.

---

# 7. Program Counter

Program Counter (PC) identifies the next instruction.

Execution flow

```

PC = 0

↓

Fetch

↓

Execute

↓

PC++

↓

Fetch

```

Jump instructions modify the Program Counter explicitly.

---

# 8. Instruction Cycle

The Execution Engine repeatedly executes

```

Fetch

↓

Decode

↓

Validate

↓

Dispatch

↓

Execute

↓

Update Context

↓

Next Instruction

```

This cycle continues until

Program Finished

or

Runtime Error

---

# 9. Instruction Categories

Instructions belong to one category.

Movement

Sensor

Arithmetic

Logic

Variable

Function

Branch

Loop

System

Each category follows dedicated execution rules.

---

# 10. Function Execution

Function execution follows

```

CALL

↓

Push Return Address

↓

Create Stack Frame

↓

Jump

↓

Execute

↓

RETURN

↓

Restore Frame

↓

Continue

```

Every function owns an independent local execution scope.

---

# 11. Variable Model

Variables are managed by Runtime.

Lifecycle

```

Declare

↓

Initialize

↓

Read

↓

Write

↓

Destroy

```

HAL shall never access Runtime variables.

---

# 12. Operand Stack

Arithmetic instructions use Operand Stack.

Example

```

LOAD A

↓

PUSH

↓

LOAD B

↓

PUSH

↓

ADD

↓

POP

↓

STORE

```

The Operand Stack is temporary.

---

# 13. Call Stack

Call Stack stores

Return Address

Local Variables

Frame Pointer

Temporary Data

Every function invocation creates exactly one frame.

---

# 14. Control Flow

Conditional execution

```

Compare

↓

Condition

↓

Jump

↓

Continue

```

Loop execution

```

Compare

↓

Branch

↓

Loop Body

↓

Jump Back

```

---

# 15. RobotAPI Invocation

Robot instructions execute through RobotAPI only.

```

Opcode

↓

Execution Engine

↓

RobotAPI

↓

HAL

↓

Hardware

```

The Execution Engine SHALL NEVER invoke HAL directly.

---

# 16. Sensor Query

Sensor instructions execute

```

Opcode

↓

RobotAPI

↓

HAL

↓

Driver

↓

Sensor

↓

Value

↓

Runtime

```

Returned values are platform independent.

---

# 17. Motion Execution

Movement instructions execute

```

Opcode

↓

RobotAPI

↓

Motion HAL

↓

Motor Driver

↓

Motor

```

The Execution Engine never controls motors directly.

---

# 18. Timing Model

Timing belongs to Runtime.

```

WAIT

↓

Runtime Timer

↓

Scheduler

↓

Resume

```

Execution SHALL NOT block hardware unnecessarily.

---

# 19. Scheduler

Current implementation

Single Task

Future architecture supports

Multiple Tasks

Coroutines

Events

Timers

Architecture shall remain unchanged.

---

# 20. Semantic Execution

Execution depends on Semantic.

Native

↓

Execute RobotAPI.

Rewrite

↓

Resolved before Runtime.

NOP

↓

Ignore.

Continue.

Stub

↓

Return "Not Implemented".

Approximation

↓

Execute documented equivalent.

Dummy

↓

Return deterministic value.

Deprecated

↓

Execute.

Generate warning if enabled.

---

# 21. Runtime Error Model

Errors are classified into

Execution Error

Memory Error

Stack Error

API Error

RobotAPI Error

HAL Error

Hardware Error

Every layer owns its own errors.

Errors propagate upward only as Runtime Status.

---

# 22. Memory Model

Execution Engine owns

Program Memory

Constant Pool

Variable Table

Call Stack

Operand Stack

HAL owns hardware memory.

The two domains never overlap.

---

# 23. State Machine

```

Load

↓

Initialize

↓

Ready

↓

Running

↓

Waiting

↓

Running

↓

Completed

↓

Unload

```

Future

```

Suspended

↓

Resumed

```

Architecture already supports these states.

---

# 24. Platform Independence

Execution Engine shall remain identical on

ESP32

STM32

RP2040

RP2350

Linux

Only HAL implementation changes.

---

# 25. Extension Rules

Adding

New Opcode

↓

Compiler

↓

Execution Engine

↓

RobotAPI

Adding

New Hardware

↓

HAL only.

Execution Engine remains unchanged.

---

# 26. Determinism

Execution shall be deterministic.

Given identical

Bytecode

Variables

Inputs

The logical execution result shall be identical on every supported platform.

Hardware timing differences shall not alter logical behaviour.

---

# 27. Future Evolution

This execution model supports

Multitasking

Remote Execution

Simulation

Cloud Runtime

Distributed Robots

Plugin Runtime

Without changing the architecture.

---

# 28. Definition of Done

The Execution Engine is complete when

✓ Every compiler opcode executes correctly.

✓ Execution Context is maintained correctly.

✓ Semantic rules are respected.

✓ RobotAPI is the only platform boundary.

✓ Runtime remains hardware independent.

✓ New hardware requires HAL changes only.

---

# 29. Architecture Freeze

This document defines the official Execution Engine Model.

Every Runtime implementation shall conform to this specification.

Any deviation requires architecture review before implementation.