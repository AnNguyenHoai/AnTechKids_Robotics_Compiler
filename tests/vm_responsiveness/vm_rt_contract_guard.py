#!/usr/bin/env python3
"""Reusable source-contract guard for VM responsiveness CI.

The guard is intentionally deterministic and host-only. It checks the scheduler,
pending-operation, bounded indivisible work, deadline ownership, line-snapshot
and compatibility boundaries that must fail closed when a regression is introduced.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Sources:
    vm_h: str
    vm_cpp: str
    vm_context_h: str
    run_slice_cpp: str
    snapshot_cpp: str
    tcrt_h: str
    tcrt_cpp: str
    canonical_isa: str
    firmware_opcode_h: str


def load_sources(root: Path = ROOT) -> Sources:
    def read(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")

    return Sources(
        vm_h=read("robot-platform/main/src/Services/VM/VM.h"),
        vm_cpp=read("robot-platform/main/src/Services/VM/VM.cpp"),
        vm_context_h=read("robot-platform/main/src/Services/VM/VMContext.h"),
        run_slice_cpp=read("robot-platform/main/src/Services/VM/VMRunSlice.cpp"),
        snapshot_cpp=read("robot-platform/main/src/Sensor/LineSensorSnapshot.cpp"),
        tcrt_h=read("robot-platform/main/src/Sensor/TCRT5000.h"),
        tcrt_cpp=read("robot-platform/main/src/Sensor/TCRT5000.cpp"),
        canonical_isa=read("packages/robot-isa/canonical_isa.json"),
        firmware_opcode_h=read("robot-platform/main/include/generated/opcode.h"),
    )


def validate(s: Sources) -> list[str]:
    errors: list[str] = []

    # #383 keeps maxWorkUnits as the soft scheduling boundary, then permits a
    # small fixed amount of generic control-flow headroom. The extension itself
    # must remain strictly bounded; wall-clock/pending/fault/stop boundaries are
    # validated separately by the VM-RT source gates.
    loop_marker = "while (static_cast<uint32_t>(workUnits) < extendedWorkLimit)"
    if loop_marker not in s.run_slice_cpp:
        errors.append("slice scheduler must use bounded extendedWorkLimit loop")
    if "VM_REACTIVE_TRANSACTION_MAX_EXTRA_WORK_UNITS = 8" not in s.run_slice_cpp:
        errors.append("reactive transaction extension must remain fixed at 8 work units")
    if "static_cast<uint32_t>(budget.maxWorkUnits) +" not in s.run_slice_cpp or \
       "static_cast<uint32_t>(VM_REACTIVE_TRANSACTION_MAX_EXTRA_WORK_UNITS)" not in s.run_slice_cpp:
        errors.append("extended work limit must equal soft budget plus fixed transaction headroom")
    if "while (static_cast<uint32_t>(workUnits) <= extendedWorkLimit)" in s.run_slice_cpp:
        errors.append("slice scheduler permits one extra work unit beyond extended limit")
    if "if (workUnits >= budget.maxWorkUnits)" not in s.run_slice_cpp:
        errors.append("soft maxWorkUnits boundary must remain explicit")
    if "isTakenBackEdge(mProgram, mContext, executedPc)" not in s.run_slice_cpp:
        errors.append("soft-budget continuation must terminate at generic taken back-edge when available")

    if s.run_slice_cpp.count("Step();") != 1:
        errors.append("RunSlice must contain exactly one Step call site")
    if "ExecuteInstruction(" in s.run_slice_cpp:
        errors.append("RunSlice must not bypass legacy Step dispatch")

    step_start = s.vm_cpp.find("void VM::Step()")
    step_end = s.vm_cpp.find("bool VM::ContinuePendingLineOperation()", step_start)
    if step_start < 0 or step_end < 0:
        errors.append("legacy Step boundaries unavailable")
    else:
        step_body = s.vm_cpp[step_start:step_end]
        if step_body.count("ExecuteInstruction(instruction);") != 1:
            errors.append("legacy Step dispatch count changed")
        if "while (" in step_body or "for (" in step_body:
            errors.append("legacy Step became scheduler/unbounded loop")

    wait_start = s.vm_cpp.find("case Opcode::Wait:")
    wait_end = s.vm_cpp.find("case Opcode::CompareEQ:", wait_start)
    if wait_start < 0 or wait_end < 0:
        errors.append("Wait opcode boundaries unavailable")
    else:
        wait_body = s.vm_cpp[wait_start:wait_end]
        if "RobotAPI::Wait" in wait_body or "delay(" in wait_body:
            errors.append("Wait opcode regressed to blocking implementation")
        if "VMPendingOperation::Wait" not in wait_body:
            errors.append("Wait no longer uses cooperative pending state")
        if wait_body.count("mContext.mProgramCounter++;") != 2:
            errors.append("Wait PC advance contract changed or double-advanced")
        completion = wait_body.find("mContext.ClearPendingOperation();")
        if completion < 0 or wait_body.find("mContext.mProgramCounter++;", completion) < 0:
            errors.append("Wait completion must clear pending state before PC advance")

    deadline_start = s.vm_context_h.find("bool IsPendingDeadlineReached")
    deadline_end = s.vm_context_h.find("public:", deadline_start)
    if deadline_start < 0 or deadline_end < 0:
        errors.append("pending deadline helper boundaries unavailable")
    else:
        deadline_body = s.vm_context_h[deadline_start:deadline_end]
        if "mPendingOperation.IsPending()" not in deadline_body:
            errors.append("deadline helper must require live pending state")
        if "mPendingOperation.IsOwnedBy(mProgramCounter)" not in deadline_body:
            errors.append("deadline helper must enforce current-PC ownership")
        if "VMPendingOperation::Wait" not in deadline_body:
            errors.append("deadline helper must support Wait")
        if "VMPendingOperation::Mp3Play" not in deadline_body:
            errors.append("deadline helper must support Mp3Play")
        if "static_cast<int32_t>(nowMs - mPendingDeadlineMs) >= 0" not in deadline_body:
            errors.append("deadline helper must keep wrap-safe signed subtraction")

    mp3_start = s.vm_cpp.find("case Opcode::SetMp3Play:")
    mp3_end = s.vm_cpp.find("case Opcode::GetTraceValue:", mp3_start)
    if mp3_start < 0 or mp3_end < 0:
        errors.append("SetMp3Play opcode boundaries unavailable")
    else:
        mp3_body = s.vm_cpp[mp3_start:mp3_end]
        if "VMPendingOperation::Mp3Play" not in mp3_body:
            errors.append("Mp3Play must use cooperative pending state")
        if "mContext.IsPendingDeadlineReached(millis())" not in mp3_body:
            errors.append("Mp3Play must complete through shared deadline helper")
        if "RobotAPI::EndMp3PlayCooperative();" not in mp3_body:
            errors.append("Mp3Play completion must finalize cooperative output")
        completion = mp3_body.find("RobotAPI::EndMp3PlayCooperative();")
        clear = mp3_body.find("mContext.ClearPendingOperation();", completion)
        advance = mp3_body.find("mContext.mProgramCounter++;", clear)
        if completion < 0 or clear < 0 or advance < 0:
            errors.append("Mp3Play completion must finalize, clear pending, then advance PC")

    pow_start = s.vm_cpp.find("case Opcode::Pow:")
    pow_end = s.vm_cpp.find("case Opcode::Neg:", pow_start)
    if pow_start < 0 or pow_end < 0:
        errors.append("Pow opcode boundaries unavailable")
    else:
        pow_body = s.vm_cpp[pow_start:pow_end]
        if "VMPendingOperation::Pow" not in pow_body:
            errors.append("Pow must use cooperative pending state")
        if "POW_MULTIPLIES_PER_STEP" not in s.vm_cpp:
            errors.append("Pow must define a fixed per-Step multiplication budget")
        if "multiplies < POW_MULTIPLIES_PER_STEP" not in pow_body:
            errors.append("Pow work must be bounded by POW_MULTIPLIES_PER_STEP")
        if "for (int16_t i = 0; i < exp; ++i)" in pow_body:
            errors.append("Pow regressed to exponent-sized indivisible loop")
        if "mPendingPowRemaining" not in pow_body or "mPendingPowResult" not in pow_body:
            errors.append("Pow cooperative progress state is missing")
        if pow_body.count("mContext.mProgramCounter++;") != 2:
            errors.append("Pow PC advance contract changed or double-advanced")
        completion = pow_body.find("mContext.ClearPendingOperation();")
        if completion < 0 or pow_body.find("mContext.mProgramCounter++;", completion) < 0:
            errors.append("Pow completion must clear pending state before PC advance")

    if "if (g_sampledThisCycle)" not in s.snapshot_cpp:
        errors.append("same-cycle line snapshot reuse guard removed")

    fixed_start = s.snapshot_cpp.find("void sampleFixedRateOnce()")
    fixed_end = s.snapshot_cpp.find("void fixedRateTask", fixed_start)
    ensure_start = s.snapshot_cpp.find("bool EnsureSample()")
    ensure_end = s.snapshot_cpp.find("void RecordConsumer()", ensure_start)
    if min(fixed_start, fixed_end, ensure_start, ensure_end) < 0:
        errors.append("line snapshot producer/consumer boundaries unavailable")
    else:
        fixed_body = s.snapshot_cpp[fixed_start:fixed_end]
        ensure_body = s.snapshot_cpp[ensure_start:ensure_end]
        if fixed_body.count("ReadHardwareDetectedDirect()") != 3:
            errors.append("fixed-rate producer must perform exactly three read-only physical channel reads")
        if "SampleHardwareDirect();" in fixed_body or "ApplySnapshotReading(" in fixed_body:
            errors.append("fixed-rate producer must not mutate legacy TCRT cached readings")
        if ensure_body.count("SampleHardwareDirect();") != 3:
            errors.append("firmware-owned snapshot must perform exactly three physical channel reads")
        if "g_snapshot.physicalReadCount = 3;" not in ensure_body:
            errors.append("firmware-owned snapshot physical-read evidence drifted")
        if "g_snapshot.physicalReadCount = 0;" not in ensure_body:
            errors.append("fixed-rate consumer must not claim firmware-cycle-owned physical reads")
        for token in (
            "left->ApplySnapshotReading(latest.left ? 1 : 0)",
            "center->ApplySnapshotReading(latest.center ? 1 : 0)",
            "right->ApplySnapshotReading(latest.right ? 1 : 0)",
        ):
            if token not in ensure_body:
                errors.append("fixed-rate consumer must apply one coherent published L/C/R set at legacy boundary")
                break

    if "ReadHardwareDetectedDirect() const" not in s.tcrt_h or "TCRT5000::ReadHardwareDetectedDirect() const" not in s.tcrt_cpp:
        errors.append("TCRT read-only fixed-rate acquisition primitive missing")

    try:
        isa = json.loads(s.canonical_isa)
    except json.JSONDecodeError:
        errors.append("canonical ISA is not valid JSON")
        return errors

    rows = isa.get("rows")
    if not isinstance(rows, list) or not rows:
        errors.append("canonical ISA rows missing")
        return errors

    seen_codes: set[int] = set()
    for row in rows:
        if not isinstance(row, list) or len(row) < 3:
            errors.append("canonical ISA row shape changed")
            continue
        code = row[2]
        if not isinstance(code, int):
            errors.append("canonical ISA opcode must remain integer")
            continue
        if code in seen_codes:
            errors.append(f"duplicate canonical opcode number: {code}")
        seen_codes.add(code)
        name = row[1]
        pattern = rf"\b{re.escape(str(name))}\s*=\s*{code}\s*,"
        if re.search(pattern, s.firmware_opcode_h) is None:
            errors.append(f"firmware opcode drift: {name}={code}")

    return errors


def assert_valid(s: Sources | None = None) -> None:
    errors = validate(s or load_sources())
    if errors:
        raise AssertionError("VM-RT contract violation(s):\n- " + "\n- ".join(errors))


if __name__ == "__main__":
    assert_valid()
    print("VM-RT reusable contract guard: PASS")
