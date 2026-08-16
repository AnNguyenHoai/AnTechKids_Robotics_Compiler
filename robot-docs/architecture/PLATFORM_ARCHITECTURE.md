# RUNTIME_CONTRACT.md

Version: 1.0

Status: Architecture Freeze

Owner: Robot Platform Team

---

# 1. Purpose

This document defines the contracts between Runtime components.

A contract specifies

- Responsibilities
- Allowed dependencies
- Forbidden dependencies
- Ownership
- Communication rules

This document prevents architectural violations.

Implementation details are intentionally excluded.

---

# 2. Runtime Philosophy

Every Runtime layer owns exactly one responsibility.

No layer may perform work belonging to another layer.

Communication is strictly hierarchical.

```

VM

↓

Runtime

↓

RobotAPI

↓

HAL

↓

Hardware

```

Reverse communication is forbidden.

---

# 3. Layer Contract

## Virtual Machine

### Responsibilities

Execute bytecode.

Maintain Program Counter.

Dispatch instructions.

Manage operand stack.

Manage execution state.

---

### Allowed Dependencies

Execution Context

Runtime Services

Opcode Registry

---

### Forbidden Dependencies

RobotAPI

HAL

GPIO

PWM

Hardware Drivers

ESP32 SDK

FreeRTOS APIs

---

### Ownership

Opcode execution.

Nothing else.

---

# 4. Execution Context Contract

Execution Context owns

Program Counter

Stack Pointer

Call Stack

Variable Table

Temporary Values

Flags

Execution Context SHALL NOT

Execute RobotAPI.

Access HAL.

Allocate hardware resources.

Execution Context is passive state.

---

# 5. Runtime Service Contract

Runtime Services provide execution support.

Examples

Timer

Scheduler

Memory

Variable Manager

Function Manager

Loader

Event Queue

Runtime Services SHALL NOT

Access hardware.

Know RobotAPI implementation.

Interpret hardware drivers.

---

# 6. RobotAPI Contract

RobotAPI is the Platform Boundary.

Everything below RobotAPI is hardware.

Everything above RobotAPI is platform.

RobotAPI categories

Motion

Sensor

LED

Audio

Display

System

RobotAPI SHALL NOT expose

GPIO

PWM

ADC

UART

ESP32

TB6612

Pin Numbers

RobotAPI SHALL hide implementation completely.

---

# 7. HAL Contract

HAL owns hardware abstraction.

Each HAL driver owns one physical device.

Examples

Motor Driver

Ultrasonic

Line Sensor

Servo

LED

Buzzer

HAL SHALL NOT

Interpret bytecode.

Store variables.

Execute algorithms.

Know Runtime.

Know VM.

HAL only controls hardware.

---

# 8. Hardware Contract

Hardware executes electrical operations.

Hardware SHALL NEVER

Know Runtime.

Know RobotAPI.

Know Bytecode.

Hardware SHALL expose only

Read()

Write()

Initialize()

Shutdown()

Driver-specific operations.

---

# 9. Dependency Matrix

| Layer | VM | Runtime | RobotAPI | HAL | Hardware |
|--------|----|----------|----------|------|-----------|
| VM | ✓ | ✓ | ✗ | ✗ | ✗ |
| Runtime | ✗ | ✓ | ✓ | ✗ | ✗ |
| RobotAPI | ✗ | ✗ | ✓ | ✓ | ✗ |
| HAL | ✗ | ✗ | ✗ | ✓ | ✓ |
| Hardware | ✗ | ✗ | ✗ | ✗ | ✓ |

Every dependency outside this table is forbidden.

---

# 10. Ownership Matrix

| Component | Owns |
|------------|------|
| VM | Opcode Execution |
| Execution Context | Program State |
| Runtime Services | Runtime Utilities |
| RobotAPI | Platform APIs |
| HAL | Hardware Abstraction |
| Driver | Physical Device |

Ownership shall never overlap.

---

# 11. Error Ownership

Compiler Errors

↓

Compiler

Runtime Errors

↓

Runtime

Hardware Errors

↓

HAL

Electrical Failures

↓

Hardware

Each layer owns its own failures.

Errors shall not propagate upward as implementation details.

---

# 12. Semantic Contract

Native

↓

Execute RobotAPI.

Rewrite

↓

Resolved before Runtime.

NOP

↓

Ignore safely.

Stub

↓

Return "Not Implemented".

Approximation

↓

Execute documented equivalent behaviour.

Dummy

↓

Return deterministic value.

Deprecated

↓

Execute.

Generate warning.

Semantic behaviour SHALL be consistent across all robot platforms.

---

# 13. Timing Contract

Runtime owns logical timing.

HAL owns physical timing.

Example

```

Wait(1000)

↓

Runtime Timer

↓

HAL Delay

```

VM SHALL NEVER call hardware delay directly.

---

# 14. Memory Contract

Runtime owns

Variables

Stack

Temporary Values

Program Memory

HAL owns

Peripheral State

GPIO State

PWM State

Sensor State

Memory ownership SHALL NEVER overlap.

---

# 15. Extension Contract

Adding a new RobotAPI requires

Language

↓

Compiler

↓

Runtime

↓

RobotAPI

↓

HAL

Adding new hardware SHALL NOT modify

VM

Execution Context

Runtime Services

Compiler

---

# 16. Thread Safety

Future Runtime may support

Multiple Tasks

Coroutines

Events

Interrupts

Current architecture SHALL remain valid.

No architectural redesign required.

---

# 17. Platform Independence

Runtime SHALL NOT depend on

ESP32

STM32

Linux

RP2040

RP2350

Only HAL is platform-specific.

---

# 18. Design Rules

Rule 1

Dependencies only point downward.

---

Rule 2

Every layer owns exactly one responsibility.

---

Rule 3

No direct hardware access above HAL.

---

Rule 4

No bytecode interpretation below Runtime.

---

Rule 5

No robot behaviours inside Runtime.

---

Rule 6

Platform APIs remain hardware-independent.

---

Rule 7

Generated code shall follow the same contracts.

---

# 19. Anti-patterns

Forbidden

VM calling GPIO.

Runtime reading ADC.

RobotAPI exposing pin numbers.

HAL executing algorithms.

Driver storing user variables.

Cross-driver communication.

Business logic inside HAL.

These are architectural violations.

---

# 20. Architecture Freeze

This document defines the official Runtime Contracts.

Every Runtime implementation must satisfy these contracts.

Any violation requires architectural review before acceptance.