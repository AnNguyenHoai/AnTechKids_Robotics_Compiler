# RoboSim RC1 Runtime Gap Analysis

**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Draft for Review  

---

## Overview

This document analyzes the runtime requirements of the RC1 acceptance program and identifies gaps between current Robot Platform capabilities and what is needed.

---

## RC1 Program Structure

```python
import rcu
import _thread

def task1():
  while True:
    if (rcu.GetLightSensorData(1) == 1):
      rcu.SetMoveSpeed(-50, -50)
      rcu.line_intersection_stop(70, 17)
    else:
      rcu.SetMoveRunSecond("turnright", 50, 0.5)
      rcu.SetMoveRunSecond("forward", 50, 5)
      if (rcu.GetTraceV2I2CState(1, 1)):
        rcu.line_turn_encounterline(70, 20, 1)
      if (rcu.GetTraceV2I2C(1, 1) == 50):
        rcu.line_basis(70)
      if (rcu.GetTraceV2I2CChxState(1, 1)):
        rcu.line_set_initialize(1, "black", "wheeledchassis")
        rcu.line_intersection_stop(70, 17)
        rcu.line_for_bmp(70, 360)

def task2():
  while True:
    if (rcu.GetLightSensorData(1)):
      rcu.SetMoveSpeed(50, 50)
    if (rcu.GetLightSensor(1) == 50):
      rcu.SetMoveRunAngle("forward", 50, 50)

_thread.start_new_thread(task1, ())
_thread.start_new_thread(task2, ())

while 1:
  pass
Runtime Requirements
1. Multiple Execution Contexts
Two tasks (task1 and task2) run concurrently.

Each task has its own:

Program counter

Local variables (none here)

Execution state (running, blocked)

Current State:

The compiler inlines the function bodies of task1 and task2 sequentially. Only one instruction stream exists.

No multiple contexts.

Gap:

Need support for multiple threads in the VM.

Solution:

Implement a cooperative scheduler in the VM.

Each _thread.start_new_thread registers a function.

VM round‑robins between threads.

Wait opcode yields to other threads.

2. Infinite Loops
Both tasks contain while True.

These loops should run forever.

Current State:

Compiler generates infinite loops using Jump to loop start.

VM executes until program end (which never occurs if loop is infinite).

Gap:

With multiple threads, infinite loops should not block other threads.

If one thread is in a loop and never yields, others starve.

Solution:

Insert cooperative yield points: after each instruction, or specifically after Wait and sensor reads.

In round‑robin, each thread executes a fixed number of instructions before switching.

3. Blocking API Calls
rcu.SetMoveRunSecond is blocking (waits for seconds).

line_intersection_stop, line_turn_encounterline, line_basis are likely blocking.

Current State:

Wait opcode blocks the entire VM (single thread).

No mechanism to switch to another thread during blocking.

Gap:

Blocking should only block the calling thread.

Solution:

When a thread executes a blocking call (e.g., Wait), mark it as BLOCKED.

Scheduler switches to next READY thread.

Timer interrupt or periodic check unblocks the thread after duration.

4. Shared State
No globals used in tasks, but both tasks may call SetMoveSpeed which affects shared motors.

Current State:

Motors are global hardware state.

Gap:

Race conditions: both tasks may write conflicting motor speeds.

Solution:

No locking mechanism yet. For RC1, accept that last write wins.

Future: add mutex for critical sections.

5. Sensor Reading During Concurrency
Both tasks read sensors.

Sensors are polled; no conflict.

Current State:

Sensor reading is instantaneous.

Gap:

None.

VM Architecture Gaps
1. No Thread Abstraction
VMContext currently holds a single program counter, variables, etc.

Need an array of contexts.

Proposed Model:

cpp
struct ThreadContext {
    uint16_t pc;
    int16_t variables[MAX_VARIABLES];
    uint8_t state; // READY, RUNNING, BLOCKED, FINISHED
    uint32_t wakeupTime; // for BLOCKED state
};

class VM {
    ThreadContext threads[MAX_THREADS];
    uint8_t currentThread;
    Program* program; // shared program (or per‑thread)
};
2. No Scheduling
VM::Step() currently executes one instruction of the only thread.

Need to execute one instruction of current thread, then switch.

Proposed Scheduling:

cpp
void VM::Step() {
    // Check if current thread is BLOCKED and wakeup time reached
    if (threads[currentThread].state == BLOCKED && millis() >= threads[currentThread].wakeupTime) {
        threads[currentThread].state = READY;
    }
    // Find next READY thread
    for (int i = 0; i < MAX_THREADS; i++) {
        currentThread = (currentThread + 1) % MAX_THREADS;
        if (threads[currentThread].state == READY) {
            break;
        }
    }
    // Execute one instruction
    ExecuteInstruction(program->instructions[threads[currentThread].pc]);
    // After instruction, if it was blocking, mark BLOCKED and set wakeup time
}
3. Wait Yielding
When Wait is executed, the current thread should be BLOCKED for ms milliseconds.

Scheduler then switches to another thread.

Implementation:

Handler for Wait calls RobotAPI::Wait(ms)? No, that would block the whole CPU.

Instead, Wait sets thread.wakeupTime = millis() + ms and thread.state = BLOCKED.

4. Compiler Support for Threads
Currently _thread.start_new_thread is transformed into a function call (inlined).

Need to change:

Adapter: keep as function call? No, compiler must know it's a thread.

Compiler: when encountering _thread.start_new_thread(func, ()), emit ThreadStart opcode with function ID.

VM: on ThreadStart, create a new context with PC = entry of function.

Summary of Gaps
Gap	Severity	Solution
No multiple contexts	Critical	Implement ThreadContext array in VM
No scheduling	Critical	Implement round‑robin scheduler in Step()
Blocking blocks all threads	Critical	Make Wait thread‑local with wakeup timer
Inlining of _thread.start_new_thread	High	Change compiler to emit ThreadStart opcode
Shared motor state	Medium	Accept for RC1; later add mutex
Effort Estimate
VM threading: ~2 days

Compiler ThreadStart: ~1 day

Wait yielding: ~0.5 day

Testing & debugging: ~1 day

Total: ~4.5 days.

Alternative Approach (Quick & Dirty)
Instead of full threading:

Keep inlining but place both task bodies sequentially.

Let task1 run forever, never reaching task2.

This will not run the RC1 program correctly.