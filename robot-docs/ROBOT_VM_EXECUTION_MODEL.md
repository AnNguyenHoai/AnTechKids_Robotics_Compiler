**Robot Virtual Machine Execution Model**

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
2. Virtual Machine Overview
3. Runtime Components
4. VM Lifecycle
5. Execution Loop
6. Program Counter
7. Execution Context
8. Instruction Dispatch
9. Instruction Execution
10. ExecutionResult
11. Runtime Errors
12. RobotAPI Interaction
13. Timing Model
14. Diagnostics
15. Future Extensions
Appendix: Execution Timeline, State Diagram, Program Counter Examples, Execution Examples, Instruction Trace Examples

---

# Chapter 1 – Introduction

## 1.1 Purpose

This document defines the **Execution Model** of the Robot Virtual Machine. It specifies **how** the VM executes Robot Programs, complements the **Robot VM ISA** specification, and defines the runtime behavior of the platform.

The execution model covers:
- The runtime lifecycle of a Program
- The instruction execution loop
- The management of execution state
- Interaction with RobotAPI
- Error handling and diagnostics
- Extension points for future features

This document is the **official specification** for all Runtime implementations.

## 1.2 Scope

This specification covers:
- The VM lifecycle from creation to destruction
- The fetch–decode–dispatch–execute loop
- Program Counter semantics and update rules
- Execution Context layout and semantics
- Instruction dispatching and validation
- ExecutionResult and error propagation
- RobotAPI interaction model
- Timing and scheduling semantics
- Diagnostics and profiling support

It does **not** cover:
- The instruction set or opcode semantics (covered by `ROBOT_VM_ISA.md`)
- Compiler internals
- HAL or hardware implementation
- Performance optimization techniques

## 1.3 Relationship with ISA

| Aspect | ISA (`ROBOT_VM_ISA.md`) | Execution Model (this document) |
|--------|--------------------------|----------------------------------|
| **Focus** | *What* an instruction does | *How* the VM executes instructions |
| **Scope** | Opcodes, operands, stack effects | Lifecycle, loop, state management |
| **Stability** | Stable; defines the contract | Stable; defines the runtime behavior |
| **Audience** | Compiler, debugger, tooling | Runtime implementers, debugger, profiler |

## 1.4 Relationship with Compiler

The compiler SHALL produce bytecode that conforms to the ISA specification. The compiler SHALL NOT assume any particular execution model behavior beyond what is specified in this document.

## 1.5 Relationship with RobotAPI

The VM interacts with RobotAPI through a well-defined boundary. The execution model specifies how requests are dispatched, how responses are handled, and how errors propagate.

---

# Chapter 2 – Virtual Machine Overview

## 2.1 Responsibilities

The Robot Virtual Machine SHALL be responsible for:

| Responsibility | Description |
|----------------|-------------|
| **Program Execution** | Fetch, decode, and execute Instructions from a loaded Program. |
| **Execution State** | Maintain Program Counter, Operand Stack, Call Stack, Variable Table, and execution flags. |
| **Instruction Dispatch** | Map Opcodes to their corresponding Handlers. |
| **Control Flow** | Manage jumps, branches, calls, and returns. |
| **RobotAPI Interaction** | Dispatch RobotAPI requests and handle responses. |
| **Error Handling** | Detect, report, and recover from runtime errors. |
| **Termination** | Stop execution when appropriate (end of program, error, or external request). |

## 2.2 Execution State

The VM's execution state SHALL include:

- **Program Counter (PC)**: The index of the next instruction to execute.
- **Operand Stack**: A LIFO stack for temporary values.
- **Call Stack**: A LIFO stack of activation frames.
- **Variable Table**: A mapping from variable IDs to RuntimeValues.
- **Execution Flags**: Boolean flags indicating running, paused, waiting, completed, error, etc.
- **Current Instruction**: The instruction being executed (optional, for debugging).

## 2.3 Program Counter

The Program Counter SHALL be a 32-bit unsigned integer that indexes the Instruction Stream. It SHALL be initialized to the Program's entry point and updated according to the rules in Chapter 6.

## 2.4 Termination

The VM SHALL terminate execution when:
- The Program executes an `END` instruction.
- The PC reaches the end of the Instruction Stream.
- A fatal error occurs.
- An external request (e.g., `stop()`) is received.

Upon termination, the VM SHALL transition to the `Completed` or `Error` state and SHALL NOT execute further instructions until reloaded.

---

# Chapter 3 – Runtime Components

## 3.1 Component Diagram
┌─────────────────────┐
│ Program │ (Immutable bytecode)
└──────────┬──────────┘
│
▼
┌─────────────────────┐
│ Program Loader │ (Deserialize → Runtime Program)
└──────────┬──────────┘
│
▼
┌─────────────────────┐
│ Execution Engine │ (Orchestrates VM execution)
└──────────┬──────────┘
│
┌──────────┴──────────┐
│ │
▼ ▼
┌─────────────────┐ ┌──────────────────┐
│ Virtual Machine │ │ Dispatcher │
└─────────────────┘ └──────────────────┘
│ │
▼ ▼
┌─────────────────────┐ ┌──────────────────┐
│ Execution Context │ │Instruction Handler│
└─────────────────────┘ └──────────────────┘
│ │
└──────────┬──────────┘
▼
┌─────────────────────┐
│ RobotAPI Dispatcher │
└─────────────────────┘
│
▼
┌─────────────────────┐
│ RobotAPI │
└─────────────────────┘

text

## 3.2 Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Program** | Immutable container for bytecode, constants, and metadata. |
| **Program Loader** | Validates and deserializes bytecode into a Runtime Program. |
| **Execution Engine** | Orchestrates the VM execution lifecycle; creates and manages the VM instance. |
| **Virtual Machine** | Implements the fetch–decode–dispatch–execute loop; owns the Execution Context. |
| **Dispatcher** | Maps Opcodes to Instruction Handlers; validates opcode existence. |
| **Instruction Handler** | Executes a single instruction, updates VM state, and issues RobotAPI requests. |
| **Execution Context** | Holds the runtime state (PC, stacks, variables, flags). |
| **RobotAPI Dispatcher** | Routes RobotApiRequests to the appropriate RobotAPI method. |
| **ExecutionResult** | Encapsulates the outcome of an instruction or execution step. |

## 3.3 Component Ownership

| Component | Owned By |
|-----------|----------|
| Program | Program Loader / Execution Engine |
| Runtime Program | Execution Engine |
| Virtual Machine | Execution Engine |
| Execution Context | Virtual Machine |
| Dispatcher | Virtual Machine |
| RobotAPI Dispatcher | Virtual Machine / Execution Engine |

---

# Chapter 4 – VM Lifecycle

## 4.1 Lifecycle States
┌─────────┐
│ Created │
└────┬────┘
│ initialize()
▼
┌─────────────┐
│ Initialized │
└────┬────────┘
│ loadProgram()
▼
┌─────────────┐
│ Program │
│ Loaded │
└────┬────────┘
│ prepare()
▼
┌─────────┐
│ Ready │
└────┬────┘
│ start()
▼
┌─────────┐ pause() ┌─────────┐
│ Running │ ─────────────────▶│ Paused │
└────┬────┘ resume() └────┬────┘
│ │
│ end/error/stop │ end/error/stop
▼ ▼
┌─────────────┐ ┌─────────────┐
│ Completed │ │ Stopped │
│ or Error │ │ │
└─────────────┘ └─────────────┘
│ │
└──────────┬───────────────────┘
▼
┌────────────┐
│ Destroyed │
└────────────┘

text

## 4.2 State Descriptions

| State | Description | Allowed Transitions |
|-------|-------------|---------------------|
| **Created** | VM instance created; no resources allocated. | → Initialized |
| **Initialized** | VM resources allocated; no Program loaded. | → Program Loaded |
| **Program Loaded** | Program is loaded and validated. | → Ready |
| **Ready** | Program is prepared; entry point set; execution can begin. | → Running |
| **Running** | VM is executing instructions. | → Paused, Completed, Stopped, Error |
| **Paused** | Execution temporarily suspended. | → Running, Stopped, Error |
| **Completed** | Program finished normally. | → Destroyed |
| **Stopped** | Execution stopped externally. | → Destroyed |
| **Error** | Execution stopped due to a fatal error. | → Destroyed |
| **Destroyed** | VM resources released; instance is dead. | (none) |

## 4.3 State Entry/Exit Actions

| Transition | Action |
|------------|--------|
| Created → Initialized | Allocate Execution Context, initialize stacks and tables. |
| Initialized → Program Loaded | Load Program; validate bytecode; build function table. |
| Program Loaded → Ready | Set entry point; initialize PC; validate entry point. |
| Ready → Running | Begin execution loop. |
| Running → Paused | Suspend execution; preserve context. |
| Paused → Running | Resume execution; continue loop. |
| Running → Completed | Finish execution; clean up. |
| Running → Stopped | External stop; clean up. |
| Running → Error | Fatal error; capture error details. |

## 4.4 Error Transitions

Any state MAY transition to `Error` if a fatal error occurs. The VM SHALL capture the error and provide diagnostics through `ExecutionResult`.

---

# Chapter 5 – Execution Loop

## 5.1 The Official VM Loop
while (state == Running):
instruction = fetch(PC)
if (instruction == null):
state = Completed
break

decoded = decode(instruction)
if (!validate(decoded)):
state = Error
break

handler = dispatcher.lookup(decoded.opcode)
if (handler == null):
state = Error
break

result = handler.execute(decoded, context)
if (!result.success):
state = Error
break

PC = updatePC(decoded, result, PC)
if (PC >= program.size):
state = Completed
break

text

## 5.2 Fetch Stage

**Responsibility:** Read the next Instruction from the Instruction Stream at the current Program Counter.

**Input:** Program Counter (PC)

**Output:** Instruction (or null if PC is out of bounds)

**Validation:** The VM SHALL verify that PC is within the valid range of the Instruction Stream. If not, the VM SHALL transition to `Completed` (normal termination).

## 5.3 Decode Stage

**Responsibility:** Extract the Opcode, Flags, and Operands from the Instruction.

**Input:** Instruction (16-byte fixed size)

**Output:** DecodedInstruction (Opcode, Flags, Operands)

**Validation:** The VM SHALL validate that the Opcode is known and that the operand count matches the expected count for that Opcode.

## 5.4 Dispatch Stage

**Responsibility:** Find the appropriate Instruction Handler for the Opcode.

**Input:** Opcode

**Output:** Handler (or null)

**Validation:** If no handler exists, the VM SHALL return an error and transition to `Error`.

## 5.5 Execute Stage

**Responsibility:** Invoke the Instruction Handler to execute the instruction.

**Input:** DecodedInstruction, ExecutionContext, RobotAPIDispatcher

**Output:** ExecutionResult

**Validation:** The handler SHALL update the ExecutionContext and issue RobotAPI requests as necessary. It SHALL return an ExecutionResult indicating success or failure.

## 5.6 Update PC Stage

**Responsibility:** Advance or modify the Program Counter based on the instruction semantics.

**Rules:**

- For sequential instructions, PC SHALL be incremented by 1.
- For jump instructions, PC SHALL be set to the target address.
- For function calls, PC SHALL be pushed onto the Call Stack and set to the function entry.
- For returns, PC SHALL be restored from the Call Stack.

---

# Chapter 6 – Program Counter

## 6.1 Responsibilities

The Program Counter (PC) SHALL:

- Indicate the index of the next Instruction to execute.
- Be initialized to the Program's entry point.
- Be updated by the VM after each instruction according to the semantics of that instruction.
- Be preserved across pauses and resumes.

## 6.2 Initialization

When a Program is loaded and prepared, the VM SHALL set PC to the Program's entry point. The entry point is defined in the Program Header.

## 6.3 Update Rules

| Instruction Type | PC Update |
|------------------|-----------|
| Sequential | `PC = PC + 1` |
| Unconditional Jump | `PC = target` |
| Conditional Jump (taken) | `PC = target` |
| Conditional Jump (not taken) | `PC = PC + 1` |
| CALL | `PC = function_entry` (return address pushed) |
| RETURN | `PC = return_address` (popped from Call Stack) |
| END | `PC = program_size` (termination) |

## 6.4 Jump Targets

Jump targets SHALL be validated before use:

- The target SHALL be within the range `[0, program_size)`.
- The target SHALL point to a valid Instruction (not padding or metadata).
- If validation fails, the VM SHALL transition to `Error` with an invalid jump target error.

## 6.5 Return Address Management

On `CALL`, the VM SHALL push the current PC + 1 onto the Call Stack as the return address. On `RETURN`, the VM SHALL pop the return address and set PC to it.

## 6.6 Error Conditions

| Condition | Error | Recovery |
|-----------|-------|----------|
| PC out of bounds | Program Overflow | Transition to Completed (if at end) or Error |
| Invalid jump target | Invalid Jump Target | Transition to Error |
| Return without call | Return Without Call | Transition to Error |

---

# Chapter 7 – Execution Context

## 7.1 Structure

The Execution Context SHALL contain:
ExecutionContext {
ProgramCounter: uint32_t
OperandStack: Stack<RuntimeValue>
CallStack: Stack<Frame>
VariableTable: Map<VariableId, RuntimeValue>
Flags: ExecutionFlags
CurrentInstruction: Instruction (optional)
}

text

## 7.2 Operand Stack

The Operand Stack is a LIFO stack of RuntimeValues. It is used for:

- Passing arguments to instructions.
- Storing intermediate results.
- Returning values from expressions and sensor reads.

**Capacity:** At least 256 entries (implementation-defined).

**Operations:** push, pop, peek, clear, size.

**Error Conditions:**
- Stack overflow: push when full → Error.
- Stack underflow: pop when empty → Error.

## 7.3 Call Stack

The Call Stack is a LIFO stack of activation frames. Each frame contains:
Frame {
FunctionId: uint32_t
ReturnAddress: uint32_t
LocalVariables: VariableTable
FramePointer: uint32_t (optional)
}

text

**Capacity:** At least 16 frames (implementation-defined).

**Operations:** push, pop, peek, depth.

**Error Conditions:**
- Stack overflow: call depth exceeds capacity → Error.
- Return without call: pop on empty stack → Error.

## 7.4 Variable Table

The Variable Table maps variable IDs (32-bit) to RuntimeValues. It is used for:

- Global variables (accessible across functions).
- Local variables (scope-limited to a function).

**Operations:** get, set, exists, define, remove.

**Error Conditions:**
- Variable not found: get/set on non-existent variable → Error.

## 7.5 Execution Flags

The Execution Flags SHALL include:

| Flag | Description |
|------|-------------|
| Running | VM is actively executing instructions. |
| Paused | Execution is suspended. |
| Waiting | VM is waiting for a condition (e.g., sensor read). |
| Completed | Program finished normally. |
| Error | Fatal error occurred. |
| Interrupted | (Reserved) External interrupt. |
| Breakpoint | (Reserved) Breakpoint hit. |

**Operations:** set, clear, query.

---

# Chapter 8 – Instruction Dispatch

## 8.1 Instruction Registry

The Instruction Registry SHALL contain metadata for all supported opcodes:

| Field | Description |
|-------|-------------|
| Opcode | Numeric identifier. |
| Name | Mnemonic name. |
| Category | Instruction category. |
| Operand Count | Number of operands expected. |
| Semantic | Native, Rewrite, NOP, Stub, Approximation, Dummy, Deprecated. |
| Handler Function | Pointer to the execution handler. |
| Version | Introduced version. |
| Deprecated | Boolean indicating if the instruction is deprecated. |

## 8.2 Dispatcher

The Dispatcher SHALL:

1. Receive an Opcode from the Decode stage.
2. Validate the Opcode (exists in the registry).
3. Retrieve the Handler Function for the Opcode.
4. Invoke the Handler with the ExecutionContext and RobotAPIDispatcher.
5. Return an ExecutionResult.

## 8.3 Handler Lookup
Handler = Registry.lookup(Opcode)
if (Handler == null):
return ExecutionResult.Error("Unknown opcode: " + opcode)

text

## 8.4 Unknown Opcode Handling

If an Opcode is not recognized, the VM SHALL:

- Return an ExecutionResult with status `Error`.
- Set the error code to `UNKNOWN_OPCODE`.
- Transition the VM to the `Error` state.
- Terminate execution.

## 8.5 Validation

Before invoking the Handler, the Dispatcher SHALL validate:

- The Opcode is known.
- The operand count matches the expected count.
- The operands are of the correct type (if type information is available).

---

# Chapter 9 – Instruction Execution

## 9.1 General Lifecycle

Each Instruction SHALL be executed in the following stages:
Before Execute
│
▼
Validate operands and stack
│
▼
Execute Instruction
│
▼
Update ExecutionContext (PC, stacks, variables)
│
▼
Issue RobotAPI request (if needed)
│
▼
Process response (if any)
│
▼
Return ExecutionResult

text

## 9.2 Validation

Validation SHALL ensure:

- Sufficient operands are present on the Operand Stack.
- Operands are of the correct type.
- Immediate operands are within valid ranges.
- Jump targets are valid.
- Variable IDs exist.

If validation fails, the instruction SHALL NOT execute, and the VM SHALL transition to `Error`.

## 9.3 Execution

The Handler SHALL:

1. Pop operands from the Operand Stack as needed.
2. Perform the operation (arithmetic, control flow, sensor read, etc.).
3. Push results onto the Operand Stack.
4. Update the Program Counter according to the instruction semantics.
5. Issue RobotAPI requests if the instruction requires hardware interaction.
6. Handle RobotAPI responses and push results onto the stack.

## 9.4 State Update

After execution, the VM SHALL:

- Update PC (unless the instruction already did so).
- Update the Operand Stack.
- Update the Variable Table (for `STORE`).
- Update the Call Stack (for `CALL` and `RETURN`).
- Update Execution Flags (for `WAIT`, `END`, etc.).

## 9.5 ExecutionResult

Every instruction SHALL return an ExecutionResult. The VM SHALL check the result and:

- If success: continue to the next instruction.
- If warning: log the warning and continue.
- If error: transition to `Error` and stop.

---

# Chapter 10 – ExecutionResult

## 10.1 Structure
ExecutionResult {
Status: ExecutionStatus
ErrorCode: uint32_t
Message: string (optional)
PC: uint32_t
Layer: ExecutionLayer
OpcodeId: uint32_t
ExecutionTime: uint64_t (optional)
Context: any (optional, for debugging)
}

text

## 10.2 Status Values

| Status | Description |
|--------|-------------|
| Success | Execution completed normally. |
| Failure | Execution failed but may be recoverable. |
| Pending | Execution is waiting for an asynchronous operation. |
| Cancelled | Execution was cancelled externally. |
| Error | Fatal error; execution cannot continue. |

## 10.3 Error Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Unknown Opcode |
| 2 | Invalid Operand |
| 3 | Stack Underflow |
| 4 | Stack Overflow |
| 5 | Invalid Program Counter |
| 6 | Invalid Jump Target |
| 7 | Return Without Call |
| 8 | Call Stack Overflow |
| 9 | Variable Not Found |
| 10 | Division by Zero |
| 11 | RobotAPI Error |
| 12 | Insufficient Operands |
| 13 | Type Mismatch |

## 10.4 Propagation

- Errors SHALL be propagated upward to the Execution Engine.
- The VM SHALL transition to `Error` upon any fatal error.
- The Execution Engine SHALL handle the error (e.g., log, stop, reset).

## 10.5 Termination

Upon receiving a fatal error, the VM SHALL:

1. Set state to `Error`.
2. Stop the execution loop.
3. Capture the error details in ExecutionResult.
4. Return the ExecutionResult to the caller.

---

# Chapter 11 – Runtime Errors

## 11.1 Error Categories

| Category | Description | Recoverable |
|----------|-------------|-------------|
| Validation Error | Invalid program or instruction format | No |
| Stack Error | Stack overflow/underflow | No |
| Control Flow Error | Invalid jump, return without call | No |
| Variable Error | Variable not found | No |
| Arithmetic Error | Division by zero, type mismatch | No |
| RobotAPI Error | Hardware request failed | Maybe (depends on API) |
| System Error | Internal VM error | No |

## 11.2 Recovery Strategy

| Error Type | Strategy |
|------------|----------|
| Validation Error | Stop execution; return error. |
| Stack Error | Stop execution; return error. |
| Control Flow Error | Stop execution; return error. |
| Variable Error | Stop execution; return error. |
| Arithmetic Error | Stop execution; return error. |
| RobotAPI Error | Stop execution; or allow continuation if API permits. |
| System Error | Stop execution; return error. |

## 11.3 Error Logging

The VM SHALL log all errors (implementation-defined logging) for diagnostics. The log SHALL include:
- Error code
- Message
- PC
- Opcode (if known)
- Timestamp

---

# Chapter 12 – RobotAPI Interaction

## 12.1 Execution Model
Instruction Handler
│
▼
RobotApiRequest (ApiId, parameters)
│
▼
RobotApiDispatcher
│
▼
RobotAPI method
│
▼
RobotApiResponse (return value, status)
│
▼
Instruction Handler
│
▼
RuntimeValue pushed onto Operand Stack

text

## 12.2 Request Types

| Type | Description | Example |
|------|-------------|---------|
| Command | Action without return value | Forward, Stop, SetLED |
| Query | Request data with return value | ReadUltrasonic, ReadLine |

## 12.3 Synchronous Execution

All RobotAPI requests SHALL be synchronous. The VM SHALL wait for the response before continuing execution.

## 12.4 Error Handling

If RobotAPI returns an error, the VM SHALL:
- Return an ExecutionResult with `Error` status.
- Set the error code to `ROBOTAPI_ERROR`.
- Transition to `Error` state.

## 12.5 Compiler SHALL NOT Know RobotAPI

The Compiler SHALL NOT include or call RobotAPI directly. All RobotAPI interaction is the responsibility of the Runtime and Instruction Handlers.

---

# Chapter 13 – Timing Model

## 13.1 Execution Step

Each instruction execution is an atomic step. The VM SHALL execute one instruction per `step()` call.

## 13.2 Continuous Run

The VM SHALL execute a sequence of instructions in a loop until:

- The Program ends.
- An error occurs.
- An external stop is requested.

## 13.3 Wait Instruction

The `WAIT` instruction SHALL:

- Set the `Waiting` flag.
- Suspend execution for the specified time.
- Resume execution after the time elapses.

**Implementation:** The VM SHALL NOT block the MCU. It SHALL use a timer mechanism (provided by Runtime Services) to resume after the delay.

## 13.4 Blocking vs Non-Blocking

- Instructions that interact with hardware (motion, sensors) are **blocking** in the sense that they wait for the RobotAPI response.
- The VM SHALL NOT block on `WAIT`; it SHALL yield to a scheduler if one exists.

## 13.5 Future Scheduler

The current execution model is single-threaded. Future versions SHALL support cooperative multitasking and scheduling through a dedicated scheduler.

---

# Chapter 14 – Diagnostics

## 14.1 Execution Statistics

The VM SHALL maintain the following statistics:

| Statistic | Description |
|-----------|-------------|
| Instruction Count | Total instructions executed. |
| Runtime (ms) | Total execution time in milliseconds. |
| Error Count | Number of errors encountered. |
| RobotAPI Request Count | Number of RobotAPI requests dispatched. |

## 14.2 Tracing

The VM MAY support instruction tracing:

- Log each instruction before execution.
- Include PC, Opcode, and operands.
- Enable/disable tracing via a configuration flag.

## 14.3 Profiler

Future versions SHALL support a profiler that collects:

- Instruction frequency.
- Execution time per instruction.
- RobotAPI call distribution.

## 14.4 Debugger

Future versions SHALL support a debugger with:

- Breakpoints.
- Watchpoints.
- Single-stepping.
- State inspection.

---

# Chapter 15 – Future Extensions

## 15.1 Debugger

- Breakpoints: Stop execution at a specific address.
- Watchpoints: Stop execution when a variable changes.
- Single-step: Execute one instruction at a time.
- State inspection: Read/write ExecutionContext.

## 15.2 Profiler

- Instruction counting.
- Timing analysis.
- RobotAPI call tracing.

## 15.3 Coroutines and Multitasking

- Cooperative multitasking with multiple ExecutionContexts.
- Yield instruction to switch tasks.
- Scheduler for task management.

## 15.4 Event Loop

- Asynchronous events (sensor interrupts, timers).
- Event queue and dispatcher.
- Pause/resume on events.

## 15.5 Garbage Collection (Reserved)

- Automatic memory management for RuntimeValues (if heap-allocated).
- Reference counting or mark-and-sweep (future).

---

# Appendix – Execution Timeline

## A.1 Simple Program Timeline
Time 0: VM Created
Time 1: Program Loaded
Time 2: VM Initialized
Time 3: VM Ready
Time 4: VM Running
Time 5: Instruction Fetch (PC=0)
Time 6: Instruction Decode (LOAD_CONST)
Time 7: Instruction Execute
Time 8: PC=1
...
Time N: PC=program_size-1
Time N+1: END instruction executed
Time N+2: VM Completed

text

## A.2 Execution Timeline Diagram
Created ──► Initialized ──► Loaded ──► Ready ──► Running ──► Completed
│
▼
Paused ──► Running
│
▼
Error

text

---

# Appendix B – Runtime State Diagram
┌─────────────────────────────────────────────────────────────────┐
│ VM State Machine │
├─────────────────────────────────────────────────────────────────┤
│ │
│ ┌─────────┐ initialize ┌─────────────┐ │
│ │ Created │ ────────────────▶ │ Initialized │ │
│ └─────────┘ └──────┬──────┘ │
│ │ loadProgram │
│ ▼ │
│ ┌─────────────────┐ │
│ │ Program Loaded │ │
│ └────────┬────────┘ │
│ │ prepare │
│ ▼ │
│ ┌─────────────┐ │
│ │ Ready │ │
│ └──────┬──────┘ │
│ │ start │
│ ▼ │
│ ┌─────────┐ pause ┌─────────────┐ │
│ │ Paused │ ◀──────────── │ Running │ │
│ └─────────┘ resume └──────┬──────┘ │
│ │ │
│ │ end/error/stop │
│ ▼ │
│ ┌─────────────────┐ │
│ │ Completed/ │ │
│ │ Stopped/Error │ │
│ └─────────────────┘ │
│ │ │
│ │ destroy │
│ ▼ │
│ ┌─────────────┐ │
│ │ Destroyed │ │
│ └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘

text

---

# Appendix C – Program Counter Examples

## C.1 Sequential Execution
PC = 0
Instruction 0: LOAD_CONST
Execute → PC = 1

PC = 1
Instruction 1: FORWARD
Execute → PC = 2

PC = 2
Instruction 2: STOP
Execute → PC = 3

PC = 3 = program_size → terminate

text

## C.2 Jump Execution
PC = 0
Instruction 0: LOAD_CONST
Execute → PC = 1

PC = 1
Instruction 1: JUMP 5
Execute → PC = 5

PC = 5
Instruction 5: FORWARD
Execute → PC = 6

text

## C.3 Conditional Jump
PC = 0
Instruction 0: COMPARE
Execute → PC = 1

PC = 1
Instruction 1: JUMP_IF_FALSE 5, condition=false
Execute → condition true? false → PC = 2

PC = 2
Instruction 2: FORWARD
Execute → PC = 3

text

## C.4 Function Call
PC = 0
Instruction 0: CALL 10
Execute → push return address (1) → PC = 10

PC = 10
Instruction 10: FORWARD
Execute → PC = 11

PC = 11
Instruction 11: RETURN
Execute → pop return address → PC = 1

PC = 1
Instruction 1: STOP
Execute → PC = 2

text

---

# Appendix D – Execution Examples

## D.1 Simple Move Program
Program:
0: LOAD_CONST 50 → v0
1: FORWARD v0
2: STOP
3: END

Execution:
PC=0: LOAD_CONST → v0=50, PC=1
PC=1: FORWARD → RobotAPI.Forward(50), PC=2
PC=2: STOP → RobotAPI.Stop(), PC=3
PC=3: END → state=Completed

text

## D.2 Conditional Program
Program:
0: READ_ULTRASONIC → v0
1: LOAD_CONST 20 → v1
2: COMPARE_LT v0, v1 → v2
3: JUMP_IF_FALSE v2, 6
4: FORWARD 50
5: JUMP 7
6: BACKWARD 50
7: STOP

Execution (distance=15):
PC=0: READ_ULTRASONIC → v0=15, PC=1
PC=1: LOAD_CONST → v1=20, PC=2
PC=2: COMPARE_LT → v2=true, PC=3
PC=3: JUMP_IF_FALSE → condition true? false, PC=4
PC=4: FORWARD → RobotAPI.Forward(50), PC=5
PC=5: JUMP → PC=7
PC=7: STOP → RobotAPI.Stop(), PC=8
PC=8: END → state=Completed

text

---

# Appendix E – Instruction Trace Examples

## E.1 Trace Format
[PC=0x0000] LOAD_CONST v0, 80
[PC=0x0001] FORWARD v0
[PC=0x0002] STOP

text

## E.2 Full Trace
[Time=0] VM Ready
[Time=1] PC=0x0000 | LOAD_CONST v0, 80
[Time=2] PC=0x0001 | FORWARD v0 → RobotAPI.Forward(80)
[Time=3] PC=0x0002 | STOP → RobotAPI.Stop()
[Time=4] VM Completed