#!/usr/bin/env python3
"""VM responsiveness scheduler/pending-state contract gate.

This is a deterministic host gate for VM-RT C/D. It verifies the C++ scheduler
and generic cooperative-state implementation shape without pretending to
measure ESP32 wall-clock latency. Physical timing belongs to VM-RT H/J.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VM_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.h"
CTX_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMContext.h"
PENDING_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMPendingState.h"
RUN_SLICE_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRunSlice.cpp"
VM_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"
SPEC = ROOT / "docs" / "VM_COOPERATIVE_EXECUTION_SPEC.md"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    header = VM_H.read_text(encoding="utf-8")
    context = CTX_H.read_text(encoding="utf-8")
    pending = PENDING_H.read_text(encoding="utf-8")
    run_slice = RUN_SLICE_CPP.read_text(encoding="utf-8")
    legacy = VM_CPP.read_text(encoding="utf-8")
    spec = SPEC.read_text(encoding="utf-8")

    # Public API/result reasons required by VM_COOPERATIVE_EXECUTION_SPEC.
    for reason in (
        "BudgetExhausted",
        "Yielded",
        "Waiting",
        "Halted",
        "Stopped",
        "Fault",
    ):
        check(f"RunSlice exposes {reason} reason", reason in header)

    check("RunSlice budget has deterministic work-unit bound", "uint16_t maxWorkUnits;" in header)
    check("RunSlice result reports consumed work", "uint16_t workUnits;" in header)
    check("RunSlice result reports start PC", "uint16_t startProgramCounter;" in header)
    check("RunSlice result reports end PC", "uint16_t endProgramCounter;" in header)
    check("VM exposes additive RunSlice API", "VMRunSliceResult RunSlice(const VMRunSliceBudget& budget);" in header)
    check("legacy Step API remains directly exposed", "void Step();" in header)

    # Preserve the frozen #304 Step implementation. RunSlice is deliberately in
    # a separate translation unit so adding the scheduler cannot rewrite Step.
    step_start = legacy.index("void VM::Step()")
    step_end = legacy.index("bool VM::ContinuePendingLineOperation()", step_start)
    step_body = legacy[step_start:step_end]
    check("legacy Step still dispatches exactly once", step_body.count("ExecuteInstruction(instruction);") == 1)
    check("legacy Step still contains no scheduler loop", "while (" not in step_body and "for (" not in step_body)
    check("RunSlice does not call ExecuteInstruction directly", "ExecuteInstruction(" not in run_slice)

    # Hard work-unit boundary: one Step at most per loop iteration and the loop
    # itself is bounded only by maxWorkUnits.
    check("zero budget exits without Step", run_slice.index("budget.maxWorkUnits == 0") < run_slice.index("while (workUnits < budget.maxWorkUnits)"))
    loop = run_slice[run_slice.index("while (workUnits < budget.maxWorkUnits)"):]
    check("slice loop is work-unit bounded", loop.startswith("while (workUnits < budget.maxWorkUnits)"))
    check("slice loop invokes legacy Step once", loop.count("Step();") == 1)
    check("each attempted Step consumes one work unit", "++workUnits;" in loop)
    check("slice does not contain nested unbounded while", loop.count("while (") == 1)

    # Termination ordering and cooperative pending reasons.
    check("pre-existing VM fault returns Fault", run_slice.find("VMRunSliceStopReason::Fault") < run_slice.find("while (workUnits < budget.maxWorkUnits)"))
    check("post-Step VM fault returns Fault", loop.count("VMRunSliceStopReason::Fault") >= 1)
    check("Wait pending returns Waiting", "mPendingOperation == VMPendingOperation::Wait" in loop and "VMRunSliceStopReason::Waiting" in loop)
    check("other pending operation returns Yielded", "mPendingOperation != VMPendingOperation::None" in loop and "VMRunSliceStopReason::Yielded" in loop)
    check("non-running state distinguishes Halted", "VMRunSliceStopReason::Halted" in run_slice)
    check("non-running state distinguishes Stopped", "VMRunSliceStopReason::Stopped" in run_slice)
    check("budget exhaustion is final fallthrough", re.search(r"return makeResult\(VMRunSliceStopReason::BudgetExhausted,[\s\S]*?\n\}\s*$", run_slice) is not None)

    # Legacy Jump/JumpIf* completion stops with error=None without rewriting PC
    # to instructionCount. RunSlice must still report that outcome as Halted.
    check("RunSlice captures executed PC before Step", "const uint16_t executedPc = mContext.mProgramCounter;" in loop)
    check("normal direct jump-to-end maps to Halted", "case Opcode::Jump:" in loop and "executed.p2 == programEnd" in loop)
    check("normal conditional jump-to-end maps to Halted", "case Opcode::JumpIfFalse:" in loop and "case Opcode::JumpIfTrue:" in loop)
    check("RunSlice preserves legacy jump PC rather than rewriting it", "mContext.mProgramCounter = programEnd" not in run_slice)

    # VM-RT D: generic pending state, not opcode-specific ad-hoc state.
    check("generic pending state type exists", "class VMPendingState" in pending)
    check("pending lifecycle is explicit", "enum class VMPendingLifecycle" in pending and "Idle" in pending and "Pending" in pending)
    check("pending state records owner PC", "mOwnerProgramCounter" in pending and "OwnerProgramCounter()" in pending)
    check("pending state records generation", "mGeneration" in pending and "Generation()" in pending)
    check("same operation/owner resumes without new generation", "mOperation == operation" in pending and "mOwnerProgramCounter == ownerProgramCounter" in pending and "return false;" in pending)
    check("new logical pending operation increments generation", "++mGeneration;" in pending)
    check("legacy direct assignment captures live PC", "operator=(VMPendingOperation operation)" in pending and "*mProgramCounter" in pending)
    check("context binds pending owner to program counter", "BindProgramCounter(&mProgramCounter)" in context)
    check("context exposes owner invariant", "PendingOperationOwnedByCurrentPc()" in context)
    check("normal clear returns lifecycle to Idle", "mPendingOperation.Clear();" in context)
    check("hard reset starts a fresh pending epoch", "mPendingOperation.HardReset();" in context)
    check("deadline helper is wrap-safe", "static_cast<int32_t>(nowMs - mPendingDeadlineMs) >= 0" in context)

    # Current Wait/Line dispatch keeps the compatibility behavior while the
    # wrapper captures generic state metadata transparently.
    check("Wait still uses cooperative pending operation", "mPendingOperation = VMPendingOperation::Wait;" in legacy)
    check("Line operations still use shared Line pending kind", legacy.count("mPendingOperation = VMPendingOperation::Line;") >= 4)
    check("pending completion still clears before PC advance", "mContext.ClearPendingOperation();\n        mContext.mProgramCounter++;" in legacy)
    check("stop/reset/fault cleanup still clears pending state", step_body.count("mContext.ClearPendingOperation();") >= 2)

    # #305/#306 must not make a false wall-clock responsiveness claim while
    # known synchronous RobotAPI calls still exist.
    lower_header = header.lower()
    check("API documents cooperative non-preemptive boundary", "not preemption" in lower_header)
    check("API documents remaining synchronous RobotAPI risk", "synchronous robotapi call" in lower_header)
    check("spec keeps wall-clock secondary to deterministic budget", "Wall-clock time alone should not be the only semantic budget" in spec)

    print("VM RunSlice + cooperative pending-state contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
