# ROBOT_EXECUTION_MODEL.md

> Version: 1.0
> Status: Draft
> Owner: Robot Runtime Team
> Milestone: RoboSim → Real Robot MVP

---

# 1. Purpose

This document defines how a robot program executes after compilation.

It specifies:

- Program lifecycle
- Execution model
- Thread model
- Scheduler
- Blocking behavior
- Runtime responsibilities
- VM interaction
- Robot API execution

This specification is independent of:

- RoboSim
- Python
- Compiler implementation
- Hardware platform

---

# 2. Design Philosophy

The Robot Runtime follows a very simple principle.

> **Robot programs describe missions, not CPU instructions.**

The Runtime is responsible for converting those missions into actual hardware behavior.

Compiler responsibilities end after generating bytecode.

Runtime responsibilities begin when bytecode starts executing.

---

# 3. Overall Execution Architecture

```
Robot Program

        │

        ▼

Bytecode Image

        │

        ▼

Virtual Machine

        │

        ▼

Scheduler

        │

        ▼

Robot API

        │

        ▼

Hardware Abstraction Layer

        │

        ▼

Drivers

        │

        ▼

ESP32 Hardware
```

---

# 4. Runtime Components

```
Program Loader

↓

Thread Manager

↓

Virtual Machine

↓

Scheduler

↓

Robot API

↓

HAL

↓

Drivers
```

Each component has a single responsibility.

---

# 5. Program Lifecycle

Every robot program follows the same lifecycle.

```
Power On

↓

Initialize Runtime

↓

Load Program

↓

Create Threads

↓

Start Scheduler

↓

Execute Mission

↓

Program Never Ends
```

Robot applications are expected to run continuously.

---

# 6. Program Structure

Typical RoboSim program

```python
robot_initialize()

_thread.start_new_thread(task1)

_thread.start_new_thread(task2)

while 1:
    pass
```

Execution becomes

```
Initialization

↓

Spawn Threads

↓

Main Thread Idle

↓

Worker Threads Execute Forever
```

---

# 7. Execution Unit

The smallest execution unit is

```
Instruction
```

Instructions are grouped into

```
Basic Block
```

Blocks are grouped into

```
Function
```

Functions belong to

```
Thread
```

Threads belong to

```
Program
```

Hierarchy

```
Program

↓

Thread

↓

Function

↓

Basic Block

↓

Instruction
```

---

# 8. Main Thread

Thread 0 is always

```
Main Thread
```

Responsibilities

- execute global initialization
- create worker threads
- remain alive

Normally

```
while(1)
```

is executed forever.

---

# 9. Worker Thread

Worker threads execute robot missions.

Example

```
Task Line Follow

Task Arm Control

Task LED Animation
```

Each thread has

- Program Counter
- Stack
- Local Variables
- Execution State

---

# 10. Thread States

A thread can be

```
READY

RUNNING

BLOCKED

WAITING

TERMINATED
```

Normally

TERMINATED never occurs.

---

# 11. Scheduler

Scheduler selects

```
READY

↓

RUNNING
```

Only one thread executes VM instructions at a time.

---

# 12. Scheduling Policy

Version 1.0

```
Round Robin
```

Future versions may support

- Priority
- Event Driven
- RTOS Integration

---

# 13. Time Slice

Each thread executes

```
N Instructions
```

before scheduler switches.

Default

```
10 Instructions
```

Future configurable.

---

# 14. Blocking API

Some APIs block execution.

Example

```
wait(1)

move.run_time()

line.follow()
```

During blocking

```
Current Thread

↓

BLOCKED

↓

Scheduler

↓

Next Thread
```

---

# 15. Non Blocking API

Example

```
move.run()

servo.set()

motor.set()
```

Execution continues immediately.

---

# 16. Why Blocking Exists

Example

```
move.run_time(1 second)
```

The thread should not execute

```
move.stop()
```

immediately.

Therefore

```
Run

↓

Wait

↓

Continue
```

---

# 17. API Execution

Instruction

```
CALL_API
```

Execution

```
VM

↓

RobotAPI

↓

HAL

↓

Driver
```

VM never touches hardware directly.

---

# 18. Robot API

Robot API is divided into

```
Motion

Sensor

Servo

Motor

Line

LED

Peripheral
```

Each API owns its hardware.

---

# 19. Hardware Abstraction Layer

HAL hides

- ESP32
- GPIO
- PWM
- UART
- I2C
- ADC

Compiler never depends on HAL.

---

# 20. Instruction Execution

VM executes

```
Fetch

↓

Decode

↓

Dispatch

↓

Execute

↓

Next Instruction
```

Every instruction completes before next instruction.

---

# 21. Program Counter

Every thread owns

```
PC
```

Execution

```
Instruction

↓

PC++

↓

Next Instruction
```

Jump modifies PC.

---

# 22. Stack

Each thread owns

```
Call Stack
```

Stores

- Return Address
- Local Variables
- Parameters

---

# 23. Function Call

```
CALL

↓

Push Return Address

↓

Jump

↓

Execute

↓

RETURN

↓

Pop Address
```

---

# 24. Variable Lifetime

Global Variables

```
Entire Program
```

Local Variables

```
Function Scope
```

Temporary Values

```
Single Instruction
```

---

# 25. Wait Instruction

Example

```
WAIT

1.0
```

Execution

```
Current Thread

↓

Sleep Timer

↓

BLOCKED

↓

Scheduler

↓

Resume
```

---

# 26. Sensor Reading

Example

```
READ_SENSOR

↓

RobotAPI

↓

HAL

↓

ADC

↓

Return Value
```

Sensor read is synchronous.

---

# 27. Motion Command

Example

```
MOVE_RUN
```

Execution

```
RobotAPI

↓

Motion Controller

↓

Motor Driver

↓

PWM
```

Instruction completes immediately.

---

# 28. Line Following

Example

```
LINE_FOLLOW
```

Execution

```
RobotAPI

↓

Line Algorithm

↓

PID

↓

Motor Driver
```

Compiler never implements PID.

---

# 29. Servo

Execution

```
SERVO_SET

↓

Servo Driver

↓

PWM
```

Servo movement may continue after API returns.

---

# 30. Error Handling

Runtime errors

```
Invalid Opcode

Stack Overflow

Division By Zero

Unknown API
```

Runtime enters

```
FAULT
```

state.

---

# 31. Runtime States

```
BOOT

↓

INITIALIZE

↓

READY

↓

RUNNING

↓

FAULT
```

---

# 32. Watchdog

Runtime periodically

- feeds watchdog
- checks scheduler
- verifies thread health

---

# 33. Determinism

Given

Same Bytecode

Same Inputs

↓

Robot behavior must be identical.

Determinism is mandatory.

---

# 34. Thread Communication

Version 1.0

```
No IPC
```

Shared globals are supported.

Future

- Message Queue
- Event
- Mutex

---

# 35. Memory Ownership

```
VM

Instruction Memory

RobotAPI

Hardware State

HAL

Peripheral State
```

Ownership never overlaps.

---

# 36. Runtime Boundary

Runtime SHALL

- execute bytecode
- manage threads
- dispatch Robot APIs

Runtime SHALL NOT

- parse source code
- compile programs
- optimize bytecode

---

# 37. Compatibility

Runtime guarantees compatibility with

```
BYTECODE_SPEC.md
```

and

```
PLATFORM_API_SPEC.yaml
```

---

# 38. Future Extensions

Future versions may support

- RTOS backend
- Priority Scheduler
- Event Loop
- Interrupt Service API
- Network Stack
- OTA Runtime

---

# 39. Success Criteria

Runtime implementation is complete when

- Programs load successfully.
- Threads execute correctly.
- Blocking APIs behave correctly.
- Robot APIs control hardware correctly.
- Scheduler remains deterministic.
- Robot behavior matches RoboSim simulation.

---

# 40. Execution Summary

```
Robot Program

        │

        ▼

Bytecode

        │

        ▼

Program Loader

        │

        ▼

Virtual Machine

        │

        ▼

Scheduler

        │

        ▼

Robot API

        │

        ▼

HAL

        │

        ▼

Driver

        │

        ▼

ESP32 Hardware

        │

        ▼

Robot Mission
```

---

# Appendix A — Thread Execution Example

```
Thread 0

Initialize

↓

Spawn Task1

↓

Spawn Task2

↓

Idle Forever


Thread 1

Line Follow

↓

Wait

↓

Line Follow

↓

Wait


Thread 2

Servo

↓

Motor

↓

Wait

↓

Repeat
```

---

# Appendix B — Core Principle

The Runtime is **mission-oriented**, not instruction-oriented.

The Compiler decides **what** should happen.

The Runtime decides **when** and **how** it happens.

This separation allows the same compiled program to execute on different robot platforms while preserving identical mission behavior.