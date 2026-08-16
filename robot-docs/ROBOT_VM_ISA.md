**Robot Virtual Machine Instruction Set Architecture**

**Version:** 1.0  
**Status:** Architecture Freeze  
**Date:** 2026-08-10  
**Owner:** Robot Platform Team  

---

## Revision History

| Version | Date       | Author      | Changes          |
|---------|------------|-------------|------------------|
| 1.0     | 2026-08-10 | DeepSeek    | Initial release  |

---

## Table of Contents

1. Introduction
2. Design Philosophy
3. Architecture Overview
4. Program Model
5. Execution Model
6. Instruction Model
7. RuntimeValue Specification
8. Operand Model
9. Instruction Categories
10. Opcode Specification
11. Stack Semantics
12. Execution Semantics
13. RobotAPI Mapping
14. Versioning
15. Examples
Appendix A: Terminology
Appendix B: Opcode Summary
Appendix C: RuntimeValue Summary
Appendix D: Stack Effect Summary
Appendix E: Future Reserved ISA

---

# Chapter 1 – Introduction

## 1.1 Purpose

This document defines the **Robot Virtual Machine Instruction Set Architecture (ISA)** . It is the official specification of the executable format, instruction set, execution model, and runtime contracts of the Robot Development Platform.

The ISA is the **single source of truth** for all components that produce, consume, or execute Robot bytecode:

- Compiler
- Program Loader
- Virtual Machine
- Instruction Dispatcher
- RobotAPI Dispatcher
- Debugger
- Profiler
- Simulation Environment

## 1.2 Scope

This specification covers:

- The binary format of a Robot Program
- The instruction set and encoding
- RuntimeValue types and semantics
- Operand stack and call stack semantics
- Execution flow and control transfer
- Instruction categories and their effects
- Mapping from instructions to RobotAPI requests
- Versioning and evolution guarantees

It does **not** cover:

- Compiler frontend implementation
- RobotAPI or HAL implementation
- Hardware-specific details
- Performance optimizations
- Operating system or MCU specifics

## 1.3 Goals

The Robot VM ISA is designed to achieve:

| Goal | Description |
|------|-------------|
| **Hardware Independence** | The same bytecode executes identically on any platform with a compliant VM. |
| **Determinism** | Given identical inputs, execution produces identical outputs and side effects. |
| **Simplicity** | The instruction set is minimal, orthogonal, and easy to implement. |
| **Extensibility** | New instructions can be added without breaking existing programs. |
| **Safety** | Invalid programs are rejected before execution; runtime errors are contained. |

## 1.4 Non-Goals

- **Performance tuning**: The ISA is not optimized for any specific hardware.
- **OS integration**: The VM does not provide system calls or OS services.
- **Dynamic code generation**: Self-modifying code is not supported.
- **Concurrency**: The current specification supports a single execution thread.

## 1.5 Terminology

| Term | Definition |
|------|------------|
| **Bytecode** | The binary representation of a Robot Program, consisting of a sequence of Instructions. |
| **Instruction** | The smallest executable unit; contains an Opcode and Operands. |
| **Opcode** | A numeric identifier that determines the operation to perform. |
| **Operand** | A parameter to an Instruction; can be immediate or stack-based. |
| **Program Counter (PC)** | The index of the next Instruction to execute. |
| **Operand Stack** | A LIFO stack for temporary values during execution. |
| **Call Stack** | A stack of activation frames for function calls. |
| **RuntimeValue** | A type-safe container for data manipulated by the VM. |
| **RobotAPI** | The platform boundary through which the VM requests hardware operations. |
| **HAL** | The Hardware Abstraction Layer that implements RobotAPI on specific hardware. |
| **ExecutionResult** | The outcome of executing an Instruction, containing status and diagnostics. |

## 1.6 References

- `api.yaml` – Robot Language Specification
- `PLATFORM_ARCHITECTURE.md` – Platform Architecture
- `EXECUTION_ENGINE_MODEL.md` – Execution Engine Model
- `RUNTIME_ARCHITECTURE.md` – Runtime Architecture
- `VM_ABI.md` – VM ABI (Legacy; superseded by this document)

---

# Chapter 2 – Design Philosophy

## 2.1 Hardware Independence

The VM SHALL NOT depend on any specific microcontroller, CPU architecture, or hardware platform.

- All instructions operate on abstract state (Program Counter, Operand Stack, Call Stack, Variables).
- Hardware interaction occurs exclusively through the RobotAPI boundary.
- The VM SHALL NOT contain hardware-specific code, headers, or conditional compilation.

## 2.2 Platform Independence

The VM SHALL be identical across all supported platforms.

- The same VM source code shall compile for ESP32, STM32, RP2040, Linux, and any future platform.
- Only HAL implementations differ per platform.
- The VM does not use OS-specific APIs, threading, or file I/O.

## 2.3 Deterministic Execution

Execution SHALL be fully deterministic.

- Given the same Program, same initial VariableTable, and same sensor inputs, the VM SHALL produce the same motor commands, LED states, and audio output.
- Floating-point operations SHALL follow IEEE 754 semantics where supported.
- Random or non-deterministic operations are forbidden at the ISA level.

## 2.4 Instruction Isolation

Each Instruction SHALL be self-contained and independent.

- An Instruction SHALL NOT rely on prior Instruction state except through explicit VM state (PC, stacks, variables).
- Instructions SHALL NOT have side effects beyond documented changes to VM state and RobotAPI requests.
- The execution of one Instruction SHALL NOT affect the execution of subsequent Instructions except through control flow and data flow.

## 2.5 Open/Closed Principle

The ISA is designed for extension without modification.

- New Opcodes MAY be added without changing existing Opcode semantics.
- New RuntimeValue types MAY be added without affecting existing Instructions.
- New RobotAPI methods MAY be added without changing the VM.
- Deprecation SHALL NOT remove Opcodes or RuntimeValue types.

## 2.6 Execution Consistency

All compliant VMs SHALL execute the same bytecode identically.

- Instruction semantics are strictly defined in this specification.
- Allowed differences are limited to performance and resource constraints.
- No VM is permitted to change the logical outcome of a program.

---

# Chapter 3 – Architecture Overview

## 3.1 System Pipeline
┌─────────────────┐
│ Robot Language │ (Source: api.yaml)
└────────┬────────┘
▼
┌─────────────────┐
│ Compiler │ (AST → Bytecode)
└────────┬────────┘
▼
┌─────────────────┐
│ Bytecode │ (Binary Program)
└────────┬────────┘
▼
┌─────────────────┐
│ Program Loader │ (Deserialize → Runtime Program)
└────────┬────────┘
▼
┌─────────────────┐
│ Virtual Machine │ (Interpretation Loop)
└────────┬────────┘
▼
┌─────────────────┐
│ Dispatcher │ (Opcode → Handler)
└────────┬────────┘
▼
┌─────────────────┐
│ Instruction │ (Execution Logic)
│ Handler │
└────────┬────────┘
▼
┌─────────────────┐
│ RobotAPI │ (Platform Boundary)
│ Dispatcher │
└────────┬────────┘
▼
┌─────────────────┐
│ RobotAPI │ (Abstract Robot Control)
└────────┬────────┘
▼
┌─────────────────┐
│ HAL │ (Hardware Implementation)
└────────┬────────┘
▼
┌─────────────────┐
│ Hardware │ (Physical Robot)
└─────────────────┘

text

## 3.2 Layer Responsibilities

| Layer | Responsibilities | Inputs | Outputs | Dependencies | Forbidden Dependencies |
|-------|------------------|--------|---------|--------------|------------------------|
| **Compiler** | Translate source to Bytecode | Source code (Python AST) | Bytecode (Program) | Language Spec | Runtime, RobotAPI, HAL |
| **Program Loader** | Validate and decode Bytecode | Bytecode binary | Runtime Program | Bytecode format | Compiler, RobotAPI, HAL |
| **Virtual Machine** | Fetch and dispatch Instructions | Runtime Program | Execution Result | Execution Context | RobotAPI, HAL, GPIO |
| **Dispatcher** | Map Opcode to Handler | Opcode, Execution Context | Handler invocation | Instruction Registry | RobotAPI, HAL |
| **Instruction Handler** | Execute one Instruction | Instruction, Execution Context | State changes, RobotAPI requests | Execution Context, RobotAPI Dispatcher | HAL, GPIO |
| **RobotAPI Dispatcher** | Route VM requests to RobotAPI | RobotApiRequest | RobotApiResponse | RobotAPI | HAL, Hardware |
| **RobotAPI** | Abstract hardware control | RobotApiRequest | Hardware operation | HAL | VM, Compiler |
| **HAL** | Implement hardware abstraction | RobotAPI calls | GPIO/PWM/I2C/etc. | Hardware | VM, Compiler |

## 3.3 Dependency Rules

1. **Dependencies SHALL flow only downward.**
2. **No layer SHALL depend on layers above it.**
3. **The VM SHALL NOT include any HAL header.**
4. **Compiler SHALL NOT include any Runtime or RobotAPI header.**
5. **RobotAPI SHALL NOT expose GPIO numbers or pin names.**

---

# Chapter 4 – Program Model

## 4.1 Program Structure

A Robot Program consists of:

- **Header**: Magic number, version, flags, and metadata.
- **Constant Pool**: Deduplicated constants (integers, floats, strings, booleans).
- **Function Table**: Metadata for each function (entry point, instruction count).
- **Instruction Stream**: Flat sequence of Instructions.
- **Metadata**: Optional debugging and source mapping information.

### 4.1.1 Program Header

| Field | Size | Description |
|-------|------|-------------|
| Magic | 4 bytes | `0x52424F54` ("RBOT") |
| ABI Version | 2 bytes | Major.Minor (currently 1.0) |
| Instruction Set Version | 2 bytes | ISA version |
| Program Size | 4 bytes | Total size in bytes |
| Constant Count | 4 bytes | Number of constants |
| Function Count | 2 bytes | Number of functions |
| Entry Point | 4 bytes | Instruction index of entry function |
| Flags | 4 bytes | Reserved for future |
| Checksum | 4 bytes | Simple checksum (optional) |

### 4.1.2 Instruction Stream

The Instruction Stream is a linear array of Instructions. Each Instruction has a fixed size of **16 bytes** to simplify decoding and alignment.

### 4.1.3 Constant Pool

The Constant Pool is an array of typed constants. Each entry includes a type tag and the value.

Supported types:
- `0x01`: Integer (32-bit signed)
- `0x02`: Float (32-bit IEEE 754)
- `0x03`: Boolean (0 or 1)
- `0x04`: String (UTF-8, length-prefixed)
- `0x05`: Null (reserved)

### 4.1.4 Function Table

Each function is described by:

| Field | Size | Description |
|-------|------|-------------|
| Function ID | 2 bytes | Unique identifier |
| Entry Offset | 4 bytes | Byte offset in Instruction Stream |
| Instruction Count | 2 bytes | Number of Instructions in function |
| Local Variable Count | 1 byte | Number of local variables |
| Stack Size | 1 byte | Maximum operand stack depth (reserved) |

## 4.2 Program Lifetime

A Program goes through these stages:
Compiled ──► Loaded ──► Initialized ──► Ready ──► Executing ──► (Paused/Continued) ──► Completed/Stopped/Error

text

- **Compiled**: Bytecode exists in binary form.
- **Loaded**: Bytecode has been validated and deserialized into a Runtime Program.
- **Initialized**: The Program Loader has set up the VM state.
- **Ready**: The Program is loaded and the entry point is set.
- **Executing**: The VM is stepping through Instructions.
- **Completed**: Execution reached the end or an END instruction.
- **Stopped**: Execution was externally halted.
- **Error**: Execution encountered a fatal error.

## 4.3 Program Immutability

Once loaded, a Program SHALL be immutable.

- The Program does not change during execution.
- Constants and Instructions are read-only.
- The VM does not modify the Program.

---

# Chapter 5 – Execution Model

## 5.1 Fetch–Decode–Dispatch–Execute

The VM executes Instructions using a standard pipeline:
┌──────────┐
│ Fetch │ Read Instruction at PC
└────┬─────┘
▼
┌──────────┐
│ Decode │ Extract Opcode and Operands
└────┬─────┘
▼
┌──────────┐
│ Dispatch │ Find the Handler for the Opcode
└────┬─────┘
▼
┌──────────┐
│ Execute │ Invoke Handler; update PC
└──────────┘

text

## 5.2 Execution Context

The VM maintains an Execution Context for each running Program:

| Component | Description |
|-----------|-------------|
| Program Counter (PC) | Index of the next Instruction to execute. |
| Operand Stack | LIFO stack for temporary values. |
| Call Stack | LIFO stack of activation frames. |
| Variable Table | Mapping from variable IDs to RuntimeValues. |
| Flags | Execution state flags (running, paused, waiting, completed, error). |
| Registers | Optional temporary storage (reserved). |

## 5.3 VM Lifecycle States

| State | Description |
|-------|-------------|
| Created | VM instance created, no Program loaded. |
| Loaded | Program loaded into memory. |
| Ready | Program initialized, entry point set. |
| Running | Executing Instructions. |
| Paused | Temporarily stopped (e.g., waiting for a sensor). |
| Completed | Execution finished normally. |
| Stopped | Execution stopped externally. |
| Error | Execution encountered a fatal error. |

Transitions:
Created
│
▼
Loaded ──► Ready ──► Running ──► Completed
│ │
▼ ▼
Error Paused ──► Running
│ │
▼ ▼
Stopped Error

text

## 5.4 Instruction Cycle

For each Instruction, the VM SHALL:

1. Read the Instruction at PC.
2. Validate the Opcode and operands.
3. Execute the Instruction through its Handler.
4. Advance or modify PC according to the Instruction semantics.
5. Handle any RuntimeValue that may be produced.
6. Check for error conditions and update state accordingly.

## 5.5 Termination

A Program terminates when:

- An `END` Instruction is executed.
- PC exceeds the Instruction Stream length.
- An error occurs and cannot be recovered.
- `STOP` is invoked by the VM or external request.

Termination SHALL set the VM state to `Completed` or `Error`.

---

# Chapter 6 – Instruction Model

## 6.1 Instruction Format

An Instruction has a fixed size of **16 bytes** (128 bits).

| Field | Offset | Size | Description |
|-------|--------|------|-------------|
| Opcode | 0 | 4 bytes | 32-bit Opcode identifier. |
| Flags | 4 | 4 bytes | Reserved for metadata (e.g., conditional, branch type). |
| Operand 1 | 8 | 4 bytes | First operand (immediate or constant index). |
| Operand 2 | 12 | 4 bytes | Second operand. |

**Note:** The fixed-size format is chosen for simplicity and deterministic decoding. Future extensions may introduce variable-length instructions, but the current format SHALL remain supported.

## 6.2 Opcode

The Opcode is a 32-bit unsigned integer. Values are defined in Chapter 10.

- 0x00000000–0x0000FFFF: Reserved for internal and core instructions.
- 0x00010000–0x0001FFFF: Robot API commands.
- 0x00020000–0x0002FFFF: Future extensions.

## 6.3 Operands

Each Instruction has up to two operands. Operands MAY be:

- **Immediate**: A literal value embedded in the Instruction (e.g., speed, direction).
- **Constant Pool Index**: Index into the Constant Pool.
- **Variable ID**: Index into the Variable Table.
- **Label**: Target address (resolved during linking).

Operands are typed; the type is determined by the Opcode.

## 6.4 Flags

The Flags field is reserved for future use (e.g., conditional execution, alignment hints). All bits SHALL be zero in version 1.0.

## 6.5 Instruction Identity

Every Instruction is uniquely identified by its Opcode. The combination of Opcode and operands defines its semantics.

## 6.6 Instruction Metadata

The VM SHALL maintain metadata for each Opcode:

| Field | Description |
|-------|-------------|
| Name | Mnemonic for the Instruction. |
| Category | One of the defined Instruction Categories (Chapter 9). |
| Operand Count | Number of operands (0, 1, or 2). |
| Stack Effect | How the Operand Stack changes. |
| Semantic | Native, Rewrite, NOP, Stub, Approximation, Dummy, Deprecated. |
| Version | Introduced version. |
| Deprecated | If set, the Instruction may be removed in a future version. |

---

# Chapter 7 – RuntimeValue Specification

## 7.1 Supported Types

The VM supports the following primitive types:

| Type | Tag | C++ Equivalent | Description |
|------|-----|----------------|-------------|
| Integer | 0x01 | `int32_t` | 32-bit signed integer. |
| Float | 0x02 | `float` | 32-bit IEEE 754 floating-point. |
| Boolean | 0x03 | `bool` | Logical true/false. |
| String | 0x04 | `std::string` or `const char*` | UTF-8 encoded string (immutable). |
| Null | 0x05 | `nullptr` | Absence of a value (reserved). |
| Array | 0x06 | (future) | Variable-length sequence of RuntimeValues. |

## 7.2 Type Conversion Rules

| From → To | Integer | Float | Boolean | String |
|-----------|---------|-------|---------|--------|
| **Integer** | — | `(float)value` | `value != 0` | `str(value)` |
| **Float** | `(int)value` | — | `value != 0.0f` | `str(value)` |
| **Boolean** | `value ? 1 : 0` | `value ? 1.0f : 0.0f` | — | `value ? "true" : "false"` |
| **String** | `parseInt()` | `parseFloat()` | `!empty()` | — |

Conversion SHALL be explicit; no implicit conversion is permitted in the VM.

## 7.3 Comparison Rules

Comparisons are defined for compatible types:

- **Integer** and **Float**: numeric comparison after promotion to float.
- **Boolean**: equality only (`==`, `!=`).
- **String**: lexicographic comparison using Unicode code points.
- **Mixed types**: NOT permitted; SHALL raise an error.

## 7.4 Truthiness

The following values are considered **false** in boolean contexts:

- Integer `0`
- Float `0.0f`
- Boolean `false`
- Empty string `""`
- Null
- Empty array

All other values are **true**.

## 7.5 Memory Semantics

- RuntimeValues are **immutable**.
- When a value is copied, a new RuntimeValue is created (pass-by-value semantics).
- Strings and arrays are immutable; copying is a shallow reference to the same data, but the VM guarantees read-only access.
- Ownership: The VM owns all RuntimeValues; no external ownership is allowed.

---

# Chapter 8 – Operand Model

## 8.1 Immediate Operands

**Immediate operands** are literals embedded directly in the Instruction stream.

**Examples:**
- `FORWARD 50` → speed = 50
- `WAIT 1000` → milliseconds = 1000
- `JUMP 12` → target address = 12

**Characteristics:**
- Fixed at compile time.
- Read directly from the Instruction.
- No stack involvement.
- Limited to the size of the operand field (32 bits).

## 8.2 Operand Stack

The **Operand Stack** is a LIFO stack of RuntimeValues. It is used for:

- Temporary values during expression evaluation.
- Passing arguments to instructions that take variable operands.
- Storing results of arithmetic and comparison operations.
- Sensor readings and function return values.

**Operand Stack Semantics:**

- `push(value)`: Adds a value to the top of the stack.
- `pop()`: Removes and returns the top value.
- `peek()`: Returns the top value without removing it.

**Stack Effect:**

Every Instruction documents its effect on the Operand Stack.

Example:

- `LOAD_CONST 42`: Push integer 42 onto stack.
- `ADD`: Pop two values, add them, push result.
- `JUMP_IF_TRUE`: Pop condition and target, branch if condition true.

## 8.3 Distinction Between Immediate and Stack Operands

The VM SHALL maintain a clear distinction:

| Aspect | Immediate Operand | Operand Stack |
|--------|-------------------|---------------|
| Source | Embedded in Instruction | Runtime stack |
| Lifetime | Entire program | Instruction-local |
| Modification | Cannot be modified | Pushed/popped dynamically |
| Use Case | Constants, addresses, flags | Expressions, temporary values |

**Important Rule:**  
The Compiler SHALL NOT push metadata (e.g., type information, source location) onto the Operand Stack. The stack is exclusively for runtime data.

## 8.4 Variable Access

Variables are stored in the Variable Table and accessed via variable IDs. The VM provides two instructions for variable access:

- `LOAD` – Load value from variable onto Operand Stack.
- `STORE` – Store value from Operand Stack into variable.

---

# Chapter 9 – Instruction Categories

## 9.1 Core Instructions

**Purpose:** Basic VM operations, control flow, and program lifecycle.

**Dependencies:** None.

**Examples:**
- `NOP`
- `END`
- `WAIT` (non-blocking; sets waiting flag)
- `LOAD_CONST`
- `STORE`
- `LOAD`

**Future Extensions:**
- `NOP2`, `BREAKPOINT`

## 9.2 Motion Instructions

**Purpose:** Control robot movement.

**Dependencies:** RobotAPI Dispatcher.

**Examples:**
- `FORWARD`
- `BACKWARD`
- `TURN_LEFT`
- `TURN_RIGHT`
- `STOP`
- `SET_MOTOR_SPEED`
- `MOVE_INITIALIZE`
- `MOVE_RUN_ANGLE`

**Future Extensions:**
- `MOVE_TO_POSITION`, `TURN_ABSOLUTE`

## 9.3 Sensor Instructions

**Purpose:** Read sensor data from the robot.

**Dependencies:** RobotAPI Dispatcher.

**Examples:**
- `READ_ULTRASONIC`
- `READ_LINE`
- `READ_LIGHT`
- `READ_TOUCH`
- `READ_COLOR`
- `GET_TRACE_VALUE`
- `GET_TRACE_STATE`
- `GET_TRACE_RAW`
- `GET_LIGHT_SENSOR_DATA`

**Future Extensions:**
- `READ_GYRO`, `READ_ACCEL`, `READ_CAMERA`

## 9.4 Control Instructions

**Purpose:** Control program flow.

**Dependencies:** None (pure VM state).

**Examples:**
- `JUMP`
- `JUMP_IF_TRUE`
- `JUMP_IF_FALSE`
- `COMPARE_EQ`
- `COMPARE_NE`
- `COMPARE_LT`
- `COMPARE_LE`
- `COMPARE_GT`
- `COMPARE_GE`
- `RETURN`
- `CALL`

**Future Extensions:**
- `CALL_INDIRECT`, `YIELD`, `SWITCH`

## 9.5 Output Instructions

**Purpose:** Control actuators and outputs (LED, buzzer, display).

**Dependencies:** RobotAPI Dispatcher.

**Examples:**
- `SET_3C_LED`
- `SET_LIGHT_SENSOR_LED`
- `SET_MP3_PLAY`
- `SET_SERVO`
- `SET_MOTOR`
- `SET_MOTOR_SERVO`
- `SET_MOTOR_STRAIGHT_ANGLE`

**Future Extensions:**
- `SET_DISPLAY`, `SET_BUZZER_TONE`

## 9.6 Variable Instructions

**Purpose:** Manage variables.

**Dependencies:** Variable Table.

**Examples:**
- `LOAD_CONST`
- `LOAD`
- `STORE`

## 9.7 Function Instructions

**Purpose:** Call and return from functions.

**Dependencies:** Call Stack.

**Examples:**
- `CALL`
- `RETURN`

**Future Extensions:**
- `CALL_INDIRECT`, `GET_RETURN_VALUE`

## 9.8 System Instructions

**Purpose:** Interact with the system (time, version, diagnostics).

**Dependencies:** Runtime Services.

**Examples:**
- `WAIT`
- `END`

**Future Extensions:**
- `GET_VERSION`, `GET_RUNTIME_STATS`

---

# Chapter 10 – Opcode Specification

## 10.1 Opcode Table

| Opcode | Category | Operands | Stack Effect | RobotAPI | Description |
|--------|----------|----------|--------------|----------|-------------|
| `LoadConst` | Core | 2 (varId, constIndex) | — | No | Load constant into variable |
| `CompareEQ` | Control | 0 | left, right → bool | No | Compare equal |
| `CompareNE` | Control | 0 | left, right → bool | No | Compare not equal |
| `CompareLT` | Control | 0 | left, right → bool | No | Compare less than |
| `CompareLE` | Control | 0 | left, right → bool | No | Compare less or equal |
| `CompareGT` | Control | 0 | left, right → bool | No | Compare greater than |
| `CompareGE` | Control | 0 | left, right → bool | No | Compare greater or equal |
| `Jump` | Control | 1 (target) | — | No | Unconditional jump |
| `JumpIfFalse` | Control | 2 (cond, target) | cond → — | No | Jump if condition false |
| `JumpIfTrue` | Control | 2 (cond, target) | cond → — | No | Jump if condition true |
| `Add` | Core | 0 | left, right → sum | No | Arithmetic addition |
| `Sub` | Core | 0 | left, right → diff | No | Subtraction |
| `Mul` | Core | 0 | left, right → product | No | Multiplication |
| `Div` | Core | 0 | left, right → quotient | No | Integer division |
| `Mod` | Core | 0 | left, right → remainder | No | Modulo |
| `Pow` | Core | 0 | left, right → power | No | Power (integer exponent) |
| `Neg` | Core | 0 | value → -value | No | Negation |
| `Call` | Function | 1 (funcId) | — | No | Call function |
| `Return` | Function | 0 | — | No | Return from function |
| `Store` | Variable | 2 (srcVar, dstVar) | — | No | Store variable |
| `Nop` | Core | 0 | — | No | No operation |
| `Forward` | Motion | 1 (speed) | — | Yes | Move forward |
| `Backward` | Motion | 1 (speed) | — | Yes | Move backward |
| `TurnLeft` | Motion | 1 (speed) | — | Yes | Turn left |
| `TurnRight` | Motion | 1 (speed) | — | Yes | Turn right |
| `Stop` | Motion | 0 | — | Yes | Stop motion |
| `Wait` | System | 1 (ms) | — | No | Wait milliseconds (non-blocking) |
| `SetMotorSpeed` | Motion | 2 (left, right) | — | Yes | Set motor speeds |
| `MoveInitialize` | Motion | 3 (left, right, reverse) | — | Yes | Configure motors |
| `MoveRunAngle` | Motion | 3 (dir, speed, angle) | — | Yes | Move for angle |
| `ReadUltrasonic` | Sensor | 1 (port) | port → distance | Yes | Read ultrasonic |
| `ReadTouch` | Sensor | 1 (port) | port → state | Yes | Read touch |
| `ReadLight` | Sensor | 1 (port) | port → value | Yes | Read light |
| `ReadColor` | Sensor | 0 | → color | Yes | Read color |
| `ReadLine` | Sensor | 2 (port, channel) | port, channel → value | Yes | Read line sensor |
| `GetTraceValue` | Sensor | 2 (port, channel) | port, channel → value | Yes | Get trace value |
| `GetTraceState` | Sensor | 2 (port, channel) | port, channel → bool | Yes | Get trace state |
| `GetTraceRaw` | Sensor | 1 (port) | port → mask | Yes | Get raw bitmask |
| `GetLightSensorData` | Sensor | 1 (port) | port → value | Yes | Get light sensor data |
| `Set3CLed` | Output | 2 (port, state) | — | Yes | Set 3-color LED |
| `SetLightSensorLed` | Output | 2 (port, state) | — | Yes | Set sensor LED |
| `SetServo` | Output | 2 (port, angle) | — | Yes | Set servo |
| `SetSeeringEngine` | Output | 2 (port, angle) | — | Yes | Set steering |
| `SetSeeringEngineTime` | Output | 3 (port, angle, ms) | — | Yes | Set steering with timeout |
| `SetMotor` | Output | 2 (port, speed) | — | Yes | Set DC motor |
| `SetMotorServo` | Output | 3 (port, speed, angle) | — | Yes | Set motor+servo |
| `SetMotorStraightAngle` | Output | 4 (left, right, speed, angle) | — | Yes | Set motor straight angle |
| `LineBasis` | Line | 1 (speed) | — | Yes | Basic line following |
| `LineFollow` | Line | 1 (speed) | — | Yes | Line follow until lost |
| `LineStop` | Line | 0 | — | Yes | Stop line following |
| `LineMillisecond` | Line | 2 (speed, ms) | — | Yes | Line follow for time |
| `LineIntersectionStop` | Line | 2 (speed, type) | — | Yes | Stop at intersection |
| `LineTurnEncounterLine` | Line | 3 (speed, angle, dir) | — | Yes | Turn until line |
| `LineForBmp` | Line | 2 (speed, degree) | — | Yes | Line follow bitmap |
| `LineSetInitialize` | Line | 3 (port, color, chassis) | — | Yes | Initialize line sensor |
| `SetMp3Play` | Output | 1 (index) | — | Yes | Play buzzer/MP3 |
| `SetLizard` | Output | 1 (state) | — | Yes | Set lizard output |
| `UpdateVar` | GUI | 2 (name, value) | — | No | GUI variable update (NOP) |
| `DisplayVariable` | GUI | 1 (name) | — | No | GUI display (NOP) |

## 10.2 Reserved Opcodes

The following opcode ranges are reserved for future use:

| Range | Purpose |
|-------|---------|
| 65–127 | Extended core instructions |
| 128–255 | Extended motion |
| 256–511 | Extended sensor |
| 512–1023 | Extended control |
| 1024–2047 | Extended output |
| 2048–4095 | Reserved for custom plugins |

## 10.3 Opcode Semantics

Detailed semantics for each opcode are provided in the following subsections.

---

# Chapter 11 – Stack Semantics

## 11.1 Operand Stack

The Operand Stack is a LIFO stack of RuntimeValues. It grows and shrinks during execution.

### 11.1.1 Stack Operations

| Operation | Effect |
|-----------|--------|
| `push(value)` | Adds `value` to the top. |
| `pop()` | Removes and returns the top value. |
| `peek()` | Returns the top value without removal. |
| `clear()` | Empties the stack. |
| `size()` | Returns the number of elements. |

### 11.1.2 Stack Effect Notation

In the Opcode table, "Stack Effect" is denoted as:

- `a, b → c`: pops `a` and `b`, pushes `c`.
- `a → b`: pops `a`, pushes `b`.
- `→ c`: pushes `c` without popping.
- `—`: no stack change.

### 11.1.3 Stack Overflow/Underflow

- **Overflow**: The stack has a maximum capacity (implementation-defined, at least 256 entries). Pushing beyond capacity causes an error.
- **Underflow**: Popping from an empty stack causes an error.

### 11.1.4 Stack Examples
LOAD_CONST 42
LOAD_CONST 73
ADD

text

Stack evolution:
[] (initial)
[42] after LOAD_CONST
[42, 73] after second LOAD_CONST
[115] after ADD

text

---

## 11.2 Call Stack

The Call Stack stores activation frames for function calls.

### 11.2.1 Frame Structure

Each frame contains:

| Field | Description |
|-------|-------------|
| Function ID | Identifier of the called function. |
| Return Address | PC to return to after function completion. |
| Local Variables | VariableTable for the function's local scope. |
| Frame Pointer | (Optional) Base pointer for stack access. |

### 11.2.2 Frame Operations

- `CALL`: pushes a new frame and jumps to the function entry.
- `RETURN`: pops the current frame and restores PC.

### 11.2.3 Call Stack Depth

The Call Stack has a maximum depth (implementation-defined, at least 16). Exceeding the depth causes a stack overflow error.

---

# Chapter 12 – Execution Semantics

## 12.1 ExecutionResult

Every Instruction returns an `ExecutionResult`, which contains:

| Field | Type | Description |
|-------|------|-------------|
| `status` | `ExecutionStatus` | `Success`, `Failure`, `Pending`, `Cancelled`, `Error` |
| `errorCode` | `uint32_t` | Numeric error code (0 for success) |
| `diagnosticMessage` | `string` | Human-readable diagnostic (optional) |
| `programCounter` | `uint32_t` | PC after execution |
| `layer` | `ExecutionLayer` | Which layer produced the result |
| `opcodeId` | `uint32_t` | Opcode executed |
| `executionTime` | `uint64_t` | Time in microseconds (optional) |

## 12.2 Instruction Validation

Before executing an Instruction, the VM SHALL validate:

1. **Opcode is known** – Must be in the Opcode table.
2. **Operand count matches** – The Instruction provides the correct number of operands.
3. **Operand types are valid** – Immediate operands are within allowed ranges.
4. **Stack depth is sufficient** – There are enough values on the Operand Stack.

If validation fails, the VM SHALL return an `ExecutionResult` with `status = Failure` and an appropriate error code, and transition to the `Error` state.

## 12.3 Runtime Errors

Errors that can occur during execution:

| Error | Description |
|-------|-------------|
| Invalid Opcode | Opcode not recognized. |
| Program Overflow | PC out of bounds. |
| Invalid Jump Target | Jump target is invalid. |
| Call Stack Overflow | Too many nested calls. |
| Return Without Call | RETURN executed with empty call stack. |
| Division by Zero | Division or modulo by zero. |
| Stack Overflow | Operand Stack capacity exceeded. |
| Stack Underflow | Pop from empty Operand Stack. |
| Variable Not Found | Variable ID does not exist. |
| RobotAPI Error | RobotAPI request failed. |

## 12.4 Error Propagation

- Errors are captured in `ExecutionResult`.
- The VM SHALL transition to the `Error` state.
- Execution SHALL stop immediately.
- The Program Loader and upper layers SHALL receive the error.

## 12.5 Program Termination

The VM terminates when:

- The `END` Instruction is executed.
- PC reaches the end of the Instruction Stream.
- A fatal error occurs.
- An external request to stop is received.

---

# Chapter 13 – RobotAPI Mapping

## 13.1 Boundary

The RobotAPI is the **platform boundary** between the VM and the hardware.

- The VM SHALL NOT call RobotAPI directly.
- The VM SHALL issue `RobotApiRequest` objects.
- The `RobotApiDispatcher` SHALL route these to the appropriate RobotAPI methods.

## 13.2 Request/Response
Instruction Handler
│
▼
RobotApiRequest (contains ApiId, parameters)
│
▼
RobotApiDispatcher
│
▼
RobotAPI method
│
▼
RobotApiResponse (contains return value, status)
│
▼
Instruction Handler
│
▼
RuntimeValue pushed onto Operand Stack

text

## 13.3 Motion Mapping

| Instruction | ApiId | Parameters | Returns |
|-------------|-------|------------|---------|
| `Forward` | `FORWARD` | speed | void |
| `Backward` | `BACKWARD` | speed | void |
| `TurnLeft` | `TURN_LEFT` | speed | void |
| `TurnRight` | `TURN_RIGHT` | speed | void |
| `Stop` | `STOP` | none | void |
| `SetMotorSpeed` | `SET_SPEED` | left, right | void |
| `MoveInitialize` | `MOVE_INITIALIZE` | left, right, reverse | void |
| `MoveRunAngle` | `MOVE_RUN_ANGLE` | direction, speed, angle | void |

## 13.4 Sensor Mapping

| Instruction | ApiId | Parameters | Returns |
|-------------|-------|------------|---------|
| `ReadUltrasonic` | `READ_ULTRASONIC` | port | int (distance) |
| `ReadTouch` | `READ_TOUCH` | port | bool |
| `ReadLight` | `READ_LIGHT` | port | int (raw) |
| `ReadColor` | `READ_COLOR` | none | int |
| `ReadLine` | `READ_LINE` | port, channel | int (0/1) |
| `GetTraceValue` | `GET_TRACE_VALUE` | port, channel | int |
| `GetTraceState` | `GET_TRACE_STATE` | port, channel | bool |
| `GetTraceRaw` | `GET_TRACE_RAW` | port | int (mask) |
| `GetLightSensorData` | `GET_LIGHT_SENSOR_DATA` | port | int |

## 13.5 Output Mapping

| Instruction | ApiId | Parameters | Returns |
|-------------|-------|------------|---------|
| `Set3CLed` | `SET_3C_LED` | port, state | void |
| `SetLightSensorLed` | `SET_LIGHT_SENSOR_LED` | port, state | void |
| `SetServo` | `SET_SERVO` | port, angle | void |
| `SetSeeringEngine` | `SET_SEERING_ENGINE` | port, angle | void |
| `SetSeeringEngineTime` | `SET_SEERING_ENGINE_TIME` | port, angle, ms | void |
| `SetMotor` | `SET_MOTOR` | port, speed | void |
| `SetMotorServo` | `SET_MOTOR_SERVO` | port, speed, angle | void |
| `SetMotorStraightAngle` | `SET_MOTOR_STRAIGHT_ANGLE` | left, right, speed, angle | void |
| `SetMp3Play` | `SET_MP3_PLAY` | index | void |
| `SetLizard` | `SET_LIZARD` | state | void |

## 13.6 Compiler SHALL NOT Know RobotAPI

The Compiler SHALL NOT:

- Include any RobotAPI definitions.
- Call RobotAPI directly.
- Generate RobotAPI-specific code.
- Rely on RobotAPI implementation details.

The Compiler only generates bytecode; RobotAPI binding is a runtime concern.

---

# Chapter 14 – Versioning

## 14.1 ISA Version

The ISA version is encoded in the Program Header.

- **Major**: Incremented for breaking changes.
- **Minor**: Incremented for new features without breaking compatibility.
- **Patch**: Incremented for bug fixes and clarifications.

## 14.2 Backward Compatibility

- New versions SHALL support all previous opcodes.
- Deprecated opcodes SHALL remain available.
- New RuntimeValue types SHALL NOT remove existing types.
- The VM SHALL reject programs with an unsupported major version.

## 14.3 Forward Compatibility

- Reserved opcodes SHALL NOT be used by the VM.
- Programs using reserved opcodes SHALL be rejected.
- The Constant Pool MAY contain additional metadata that is ignored by older VMs.

## 14.4 Extension Points

| Extension Point | Location | Purpose |
|-----------------|----------|---------|
| Reserved Opcode Range | 65–4095 | Future instructions |
| Reserved RuntimeValue Tags | 0x06–0xFF | Future data types |
| Flags Field | Instruction header | Conditional execution, hints |
| Metadata Section | Program header | Debug info, profiling |

---

# Chapter 15 – Examples

## 15.1 Simple Move

**Source:**

```python
forward(80)
stop()
Bytecode (mnemonic):

text
LOAD_CONST v0, 80
FORWARD v0
STOP
Execution:

PC	Instruction	Stack Before	Stack After	RobotAPI
0	LOAD_CONST	[]	[]	No
1	FORWARD	[]	[]	Forward(80)
2	STOP	[]	[]	Stop()
15.2 Conditional Movement
Source:

python
if distance < 20:
    backward(50)
else:
    forward(50)
Bytecode:

text
READ_ULTRASONIC v0
LOAD_CONST v1, 20
COMPARE_LT v0, v1 → v2
JUMP_IF_FALSE v2, label_else
LOAD_CONST v3, 50
BACKWARD v3
JUMP label_end
label_else:
LOAD_CONST v4, 50
FORWARD v4
label_end:
STOP
Execution:

Read ultrasonic → pushes distance.

Compare with 20 → pushes boolean.

If false, jump to else block.

Otherwise execute backward.

Jump to end.

15.3 While Loop
Source:

python
while speed > 0:
    forward(50)
    speed = speed - 10
Bytecode:

text
label_loop:
LOAD_CONST v0, speed
LOAD_CONST v1, 0
COMPARE_GT v0, v1 → v2
JUMP_IF_FALSE v2, label_end
LOAD_CONST v3, 50
FORWARD v3
LOAD_CONST v4, 10
SUB v0, v4 → v0
STORE v0, speed
JUMP label_loop
label_end:
15.4 Sensor-Based Obstacle Avoidance
Source:

python
while True:
    dist = read_ultrasonic()
    if dist < 20:
        turn_left(50)
        wait(500)
    else:
        forward(50)
Bytecode:

text
label_loop:
READ_ULTRASONIC v0
LOAD_CONST v1, 20
COMPARE_LT v0, v1 → v2
JUMP_IF_FALSE v2, label_forward
LOAD_CONST v3, 50
TURN_LEFT v3
LOAD_CONST v4, 500
WAIT v4
JUMP label_loop
label_forward:
LOAD_CONST v5, 50
FORWARD v5
JUMP label_loop
Appendix A – Terminology
Term	Definition
ABI	Application Binary Interface.
Bytecode	Binary representation of a Program.
Category	Grouping of Instructions by purpose.
Constant Pool	Deduplicated constants.
Dispatcher	Maps Opcode to Handler.
Execution Context	Runtime state of the VM.
Handler	Code that executes an Instruction.
HAL	Hardware Abstraction Layer.
ISA	Instruction Set Architecture.
Operand	Parameter to an Instruction.
Opcode	Numeric identifier for an Instruction.
Program Counter	Index of next Instruction.
RobotAPI	Platform boundary.
RuntimeValue	Type-safe container for data.
Stack	LIFO data structure.
Variable Table	Storage for program variables.
VM	Virtual Machine.
Appendix B – Opcode Summary
Opcode	ID
LoadConst	1
CompareEQ	8
CompareNE	9
CompareLT	10
CompareLE	11
CompareGT	12
CompareGE	13
Jump	14
JumpIfFalse	15
JumpIfTrue	16
Label	17
Add	20
Sub	21
Mul	22
Div	23
Mod	24
Pow	25
Neg	26
Call	27
Return	28
Store	29
Nop	64
Forward	2
Backward	3
TurnLeft	4
TurnRight	5
Stop	6
Wait	7
SetMotorSpeed	35
MoveInitialize	52
MoveRunAngle	53
ReadUltrasonic	30
ReadTouch	31
ReadLight	32
ReadColor	33
ReadLine	34
GetTraceValue	42
GetTraceState	43
GetTraceRaw	44
GetLightSensorData	54
Set3CLed	37
SetLightSensorLed	38
SetServo	36
SetSeeringEngine	55
SetSeeringEngineTime	56
SetMotor	57
SetMotorServo	58
SetMotorStraightAngle	39
LineBasis	47
LineFollow	48
LineStop	49
LineMillisecond	59
LineIntersectionStop	40
LineTurnEncounterLine	50
LineForBmp	51
LineSetInitialize	60
SetMp3Play	41
SetLizard	61
UpdateVar	62
DisplayVariable	63
Appendix C – RuntimeValue Summary
Type	Tag	Description
Integer	0x01	32-bit signed integer
Float	0x02	32-bit IEEE 754 float
Boolean	0x03	true (1) or false (0)
String	0x04	UTF-8 string
Null	0x05	null value
(Reserved)	0x06–0xFF	Future types
Appendix D – Stack Effect Summary
Instruction	Stack Before	Stack After
LoadConst	[]	[]
CompareEQ	left, right	bool
CompareNE	left, right	bool
CompareLT	left, right	bool
CompareLE	left, right	bool
CompareGT	left, right	bool
CompareGE	left, right	bool
Add	left, right	sum
Sub	left, right	diff
Mul	left, right	product
Div	left, right	quotient
Mod	left, right	remainder
Pow	left, right	power
Neg	value	-value
Jump	—	—
JumpIfFalse	cond, target	—
JumpIfTrue	cond, target	—
Call	—	—
Return	—	—
Store	—	—
Nop	—	—
Forward	—	—
Backward	—	—
TurnLeft	—	—
TurnRight	—	—
Stop	—	—
Wait	—	—
SetMotorSpeed	—	—
MoveInitialize	—	—
MoveRunAngle	—	—
ReadUltrasonic	port	distance
ReadTouch	port	state
ReadLight	port	value
ReadColor	—	color
ReadLine	port, channel	value
GetTraceValue	port, channel	value
GetTraceState	port, channel	bool
GetTraceRaw	port	mask
GetLightSensorData	port	value
Set3CLed	—	—
SetLightSensorLed	—	—
SetServo	—	—
SetSeeringEngine	—	—
SetSeeringEngineTime	—	—
SetMotor	—	—
SetMotorServo	—	—
SetMotorStraightAngle	—	—
LineBasis	—	—
LineFollow	—	—
LineStop	—	—
LineMillisecond	—	—
LineIntersectionStop	—	—
LineTurnEncounterLine	—	—
LineForBmp	—	—
LineSetInitialize	—	—
SetMp3Play	—	—
SetLizard	—	—
UpdateVar	—	—
DisplayVariable	—	—
Appendix E – Future Reserved ISA
Range	Purpose
Opcodes 65–127	Extended core (breakpoint, debug)
Opcodes 128–255	Extended motion (velocity control, path planning)
Opcodes 256–511	Extended sensor (IMU, GPS, camera)
Opcodes 512–1023	Extended control (switch, coroutine)
Opcodes 1024–2047	Extended output (display, speaker)
RuntimeValue tags 0x06–0x0F	Composite types (array, struct)
RuntimeValue tags 0x10–0x1F	Advanced numeric (64-bit, complex)