# RUNTIME_ARCHITECTURE.md

Version: 1.0

Status: Architecture Freeze

Owner: Robot Platform Team

---

# 1. Purpose

This document defines the Runtime Architecture of the Robot Platform.

It is the official specification describing how Robot Programs execute after compilation.

This document is architecture only.

It intentionally avoids implementation details.

---

# 2. Runtime Philosophy

The Runtime is **NOT** the Virtual Machine.

The Runtime is the complete execution environment of a Robot Program.

Responsibilities include

- Bytecode execution
- Program lifecycle
- Variable management
- Function execution
- Timing
- Robot API dispatch
- Runtime services

The Virtual Machine is only one component of the Runtime.

---

# 3. Runtime Position

```

Robot Blockly

↓

Python

↓

Frontend

↓

Compiler

↓

Bytecode

↓

Runtime

↓

RobotAPI

↓

HAL

↓

Hardware

```

The Runtime bridges abstract robot programs and physical hardware.

---

# 4. Runtime Layers

The Runtime is divided into independent layers.

```

+---------------------------------------+

Program Execution

+---------------------------------------+

Execution Context

+---------------------------------------+

Runtime Services

+---------------------------------------+

Robot API Dispatcher

+---------------------------------------+

RobotAPI

+---------------------------------------+

HAL

+---------------------------------------+

Hardware

```

Each layer has only one responsibility.

---

# 5. Runtime Components

## 5.1 Virtual Machine

Responsibilities

- Fetch bytecode
- Decode opcode
- Dispatch execution

The VM SHALL NOT access hardware directly.

The VM SHALL NOT know motor drivers.

The VM SHALL NOT know GPIO.

The VM only executes instructions.

---

## 5.2 Execution Context

Stores execution state.

Contains

Program Counter

Stack Pointer

Call Stack

Variables

Loop Context

Temporary Values

Execution Flags

Execution Context represents one running program.

---

## 5.3 Runtime Services

Runtime Services provide execution support.

Includes

Timer Service

Scheduler

Memory Manager

Variable Manager

Function Manager

Program Loader

Event Queue

These services never access hardware directly.

---

## 5.4 RobotAPI Dispatcher

The dispatcher converts Runtime requests into RobotAPI calls.

Example

MoveForward

↓

RobotAPI::MoveForward()

Dispatcher knows RobotAPI.

Dispatcher does NOT know hardware.

---

## 5.5 RobotAPI

RobotAPI is the platform abstraction.

Categories

Motion

Sensor

LED

Audio

Display

System

RobotAPI SHALL NEVER expose GPIO.

RobotAPI SHALL NEVER expose PWM.

RobotAPI SHALL NEVER expose motor driver details.

---

## 5.6 HAL

HAL provides hardware abstraction.

Examples

TB6612

Ultrasonic

Line Sensor

LED

Buzzer

Servo

Each driver implements only hardware logic.

---

# 6. Runtime Execution Flow

```

Bytecode

↓

VM Fetch

↓

Decode

↓

Runtime

↓

Dispatcher

↓

RobotAPI

↓

HAL

↓

Hardware

```

Every instruction follows this pipeline.

---

# 7. Semantic Execution

Runtime behaviour depends on Semantic.

---

Native

↓

Execute RobotAPI.

---

Rewrite

↓

Never reaches Runtime.

Already transformed by Frontend.

---

NOP

↓

Do nothing.

Continue execution.

---

Stub

↓

Return "Not Implemented"

Continue execution.

Never crash.

---

Approximation

↓

Execute documented equivalent behaviour.

---

Dummy

↓

Return deterministic value.

---

Deprecated

↓

Execute supported behaviour.

Emit runtime warning if enabled.

---

# 8. Runtime Responsibilities

Runtime SHALL

Execute bytecode

Maintain execution context

Dispatch RobotAPI

Handle timing

Manage variables

Handle function calls

Maintain stack

Support future multitasking

---

Runtime SHALL NOT

Know GPIO

Know PWM

Know Motor Driver

Know ESP32 pins

Access hardware directly

Contain robot behaviours

---

# 9. Execution Context

Each running program owns one Execution Context.

Contains

Program Counter

Operand Stack

Call Stack

Variable Table

Temporary Registers

Flags

Future

Coroutine Context

Task Context

---

# 10. Memory Model

Memory divided into

Program Memory

Constant Pool

Global Variables

Local Variables

Stack

Temporary Memory

Runtime owns memory.

HAL owns hardware state.

---

# 11. RobotAPI Categories

Motion

Move

Stop

Turn

Sensor

Ultrasonic

Line Sensor

Future Sensors

Output

LED

Buzzer

Display

Future Display

System

Wait

Random

Timer

Version

---

# 12. HAL Principles

Every hardware driver

Owns one device.

No driver communicates with another driver.

Drivers never execute program logic.

Drivers never interpret bytecode.

Drivers only operate hardware.

---

# 13. Runtime State Machine

```

Load

↓

Initialize

↓

Ready

↓

Running

↓

Paused

↓

Running

↓

Finished

↓

Unload

```

Future

↓

Error Recovery

↓

Restart

---

# 14. Error Handling

Compiler errors

↓

Compiler

Runtime errors

↓

Runtime

Hardware errors

↓

HAL

Robot behaviour errors

↓

User Program

Every layer owns its own errors.

---

# 15. Future Extension

The Runtime architecture supports

Multitasking

Coroutines

Events

Interrupts

Simulation

Remote Execution

Multiple Robot Platforms

Without changing architecture.

---

# 16. Runtime Rules

Rule 1

VM never accesses hardware.

Rule 2

Runtime never accesses GPIO.

Rule 3

RobotAPI never exposes hardware implementation.

Rule 4

HAL never executes program logic.

Rule 5

Drivers never communicate directly.

Rule 6

Robot behaviours never belong inside Runtime.

---

# 17. Runtime Success Criteria

A Runtime implementation is considered complete when

✓ Executes all compiler bytecode.

✓ Fully follows Semantic Policy.

✓ Dispatches RobotAPI correctly.

✓ Hardware independent.

✓ Supports future platforms.

✓ Requires no architecture modification to add new devices.

---

# 18. Architecture Freeze

This document defines the official Runtime Architecture.

Future Runtime implementation SHALL follow this architecture.

Changes require architecture review before implementation.