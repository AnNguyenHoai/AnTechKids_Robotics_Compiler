#!/usr/bin/env python3
"""VM responsiveness compatibility + production loop integration gate.

This deterministic host gate freezes legacy Step()/dispatch semantics and checks
that production firmware schedules bounded RunSlice work without starving the
platform control plane. It intentionally does not claim ESP32 wall-clock timing;
physical evidence remains the qualification boundary.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "vm_responsiveness" / "fixtures" / "step_baseline.json"
VM_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"
VM_RUN_SLICE_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRunSlice.cpp"
VM_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.h"
TELEMETRY_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRuntimeTelemetry.cpp"
CTX_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMContext.h"
OPCODE_H = ROOT / "robot-platform" / "main" / "include" / "generated" / "opcode.h"
FIRMWARE_MAIN = ROOT / "robot-platform" / "main" / "main.ino"
C2 = ROOT / "docs" / "C2_VM_DISPATCH_CONTRACT.md"
MATRIX = ROOT / "docs" / "VM_RESPONSIVENESS_COMPATIBILITY_MATRIX.md"
AUDIT = ROOT / "docs" / "VM_RUNTIME_BLOCKING_AUDIT.md"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def opcode_map(text: str) -> dict[str, int]:
    return {
        name: int(value)
        for name, value in re.findall(r"^\s*(\w+)\s*=\s*(\d+)\s*,?", text, re.MULTILINE)
    }


def extract_constant(source: str, name: str) -> int:
    match = re.search(rf"{re.escape(name)}\s*=\s*(\d+)", source)
    if not match:
        raise AssertionError(f"missing firmware constant {name}")
    return int(match.group(1))


def simulate_bounded_firmware_loop(total_work: int, budget: int, stop_at_cycle: int | None = None) -> tuple[int, int, int]:
    """Tiny scheduler model for the work-ceiling integration invariant."""
    remaining = total_work
    cycles = 0
    platform_service_ticks = 0
    vm_work = 0
    running = True

    while running and remaining > 0:
        cycles += 1
        platform_service_ticks += 1
        if stop_at_cycle is not None and cycles == stop_at_cycle:
            running = False
            continue

        consumed = min(budget, remaining)
        remaining -= consumed
        vm_work += consumed

    return cycles, platform_service_ticks, vm_work


def simulate_dual_budget(work_durations_us: list[int], max_work: int, max_us: int) -> int:
    """Model the between-Step wall-clock guard used by RunSlice."""
    elapsed = 0
    consumed = 0
    for duration in work_durations_us:
        if consumed >= max_work:
            break
        elapsed += duration
        consumed += 1
        if max_us and elapsed >= max_us:
            break
    return consumed


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    vm = VM_CPP.read_text(encoding="utf-8")
    vm_slice = VM_RUN_SLICE_CPP.read_text(encoding="utf-8")
    vm_h = VM_H.read_text(encoding="utf-8")
    telemetry = TELEMETRY_CPP.read_text(encoding="utf-8")
    ctx = CTX_H.read_text(encoding="utf-8")
    opcodes = opcode_map(OPCODE_H.read_text(encoding="utf-8"))
    firmware = FIRMWARE_MAIN.read_text(encoding="utf-8")
    matrix = MATRIX.read_text(encoding="utf-8")
    c2 = C2.read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")
    work_budget = extract_constant(firmware, "VM_WORK_UNITS_PER_FIRMWARE_CYCLE")
    time_budget_us = extract_constant(firmware, "VM_MAX_SLICE_DURATION_US")

    check("fixture schema is version 1", fixture.get("schema_version") == 1)
    check("baseline is pinned to post-#303 main", fixture.get("baseline_commit") == "0b2d5c6cfdf7c807b374e2bc745405eb5119e8da")
    check("compatibility generation remains 1", fixture.get("compatibility_generation") == 1)
    guard = fixture.get("guard", {})
    check("opcode numbering is frozen", guard.get("opcode_numbering") == "unchanged")
    check("bytecode encoding is frozen", guard.get("bytecode_encoding") == "unchanged")
    check("Step semantics are frozen", guard.get("step_semantics") == "unchanged")

    cases = fixture.get("fixtures", [])
    check("representative baseline fixture set exists", len(cases) >= 8)
    for case in cases:
        check(f"fixture {case['id']} has Step contract", bool(case.get("step_contract")))
        for insn in case.get("program", []):
            check(
                f"{case['id']} opcode {insn['opcode']} number matches canonical header",
                opcodes.get(insn["opcode"]) == insn["opcode_value"],
            )

    check("VM exposes legacy Step", "void Step();" in vm_h)
    step_start = vm.index("void VM::Step()")
    step_end = vm.index("bool VM::ContinuePendingLineOperation()", step_start)
    step_body = vm[step_start:step_end]
    check("Step dispatches current instruction exactly once", step_body.count("ExecuteInstruction(instruction);") == 1)
    check("Step itself has no unbounded instruction loop", "while (" not in step_body and "for (" not in step_body)

    wait_start = vm.index("case Opcode::Wait:")
    wait_end = vm.index("case Opcode::CompareEQ:", wait_start)
    wait = vm[wait_start:wait_end]
    check("Wait initializes pending state", "VMPendingOperation::Wait" in wait and "mPendingDeadlineMs" in wait)
    check("Wait does not use blocking delay", "delay(" not in wait)
    check("Wait advances PC on immediate/non-positive or completion paths", wait.count("mProgramCounter++") == 2)

    for opcode, starter in {
        "LineIntersectionStop": "StartIntersectionStop",
        "LineMillisecond": "StartMillisecond",
        "LineTurnEncounterLine": "StartTurnEncounterLine",
        "LineForBmp": "StartBmp",
    }.items():
        start = vm.index(f"case Opcode::{opcode}:")
        next_case = vm.find("case Opcode::", start + 10)
        block = vm[start: next_case if next_case != -1 else len(vm)]
        check(f"{opcode} resumes pending line operation first", "ContinuePendingLineOperation()" in block)
        check(f"{opcode} starts cooperative service", starter in block)
        check(f"{opcode} records Line pending state", "VMPendingOperation::Line" in block)

    check("VMContext has explicit pending operation state", "mPendingOperation" in ctx and "mPendingDeadlineMs" in ctx)
    cancel_start = vm.index("void VM::CancelPendingOperation")
    cancel_end = vm.index("void VM::Reset()", cancel_start)
    cancel_body = vm[cancel_start:cancel_end]
    check("centralized cleanup cancels cooperative line state", "CooperativeLineOperation::Cancel(stopLineMotors);" in cancel_body)
    check("centralized cleanup finalizes pending MP3", "RobotAPI::EndMp3PlayCooperative();" in cancel_body)
    check("centralized cleanup clears pending ownership", "mContext.ClearPendingOperation();" in cancel_body)
    reset_body = vm[vm.index("void VM::Reset()"):vm.index("bool VM::LoadProgram")]
    check("Reset uses centralized pending cleanup", "CancelPendingOperation(true);" in reset_body)
    check("normal program-end uses centralized pending cleanup", "CancelPendingOperation(true);" in step_body)
    check("fault cleanup uses centralized pending cleanup", "Stop on a real VM error" in step_body and step_body.count("CancelPendingOperation(true);") >= 2)

    check("RunSlice budget exposes optional wall-clock ceiling", "uint32_t maxDurationUs = 0;" in vm_h)
    check("time-budget stop reason is appended", "TimeBudgetExhausted" in vm_h)
    check("RunSlice enforces wall-clock ceiling between Step calls",
          "budget.maxDurationUs != 0" in vm_slice and "VMRunSliceStopReason::TimeBudgetExhausted" in vm_slice)

    loop = firmware[firmware.index("void loop()") :]
    check("production loop uses bounded RunSlice", "vm.RunSlice(budget);" in loop)
    check("production loop no longer invokes VM Step directly", "vm.Step();" not in loop)
    check("firmware reactive work ceiling covers representative 22-unit loop", work_budget >= 22)
    check("firmware keeps a finite wall-clock slice ceiling", 0 < time_budget_us <= 2000)
    check("production budget passes both ceilings", "VM_MAX_SLICE_DURATION_US" in loop[loop.index("VMRunSliceBudget budget"):loop.index("vm.RunSlice(budget);")])

    begin = loop.index("LineSensorSnapshot::BeginCycle();")
    sensor = loop.index("SensorManager::instance().updateAll();")
    motion = loop.index("RobotAPI::updateMotion();")
    vm_call = loop.index("vm.RunSlice(budget);")
    end_snapshot = loop.index("LineSensorSnapshot::EndCycle();")
    serial = loop.index("SerialCommandHandler::handle();")
    network = loop.index("RobotNetworkService::update(ROBOT_NETWORK_SERVICE_BUDGET_US);")
    check("fresh line sample precedes VM decision", begin < sensor < motion < vm_call)
    check("serial background service follows VM control phase", vm_call < end_snapshot < serial)
    check("network background service follows serial background phase", serial < network)
    check("active OTA gate runs before line sampling", loop.index("RobotNetworkService::isUpdateInProgress()") < begin)
    check("active OTA retains service path after actuator stop",
          loop.index("RobotAPI::Stop();") < loop.index("RobotNetworkService::update(0);") < begin)
    check("loop diagnostics records after background service",
          loop.rindex("DiagnosticsManager::instance().recordLoopTime(end - start);") > network)
    check("VM completion does not enter nested firmware halt loop", "while (1)" not in loop)

    run_slice_block = loop[loop.index("if (runVmSlice)"):loop.index("if (vm.IsRunning())")]
    check("hot VM path records telemetry in RAM", "VMRuntimeTelemetry::RecordSlice(sliceResult);" in run_slice_block)
    check("hot VM path does not print telemetry", "PrintLatestJson" not in run_slice_block and "PrintBufferedJson" not in run_slice_block)
    terminal_block = loop[loop.index("else if (!g_vmTerminalReported)"):]
    check("terminal path stops actuator before telemetry dump",
          terminal_block.index("RobotAPI::Stop();") < terminal_block.index("VMRuntimeTelemetry::PrintBufferedJson();"))
    check("telemetry implementation uses RAM ring buffer", "g_sliceBuffer" in telemetry and "kSliceBufferCapacity" in telemetry)

    reactive_work = [50] * 22
    check("representative reactive chain fits one slice under work ceiling",
          simulate_dual_budget(reactive_work, work_budget, time_budget_us) == 22)
    check("time ceiling still bounds a slow burst",
          simulate_dual_budget([500] * work_budget, work_budget, time_budget_us) == 4)

    long_cycles, long_services, long_work = simulate_bounded_firmware_loop(100, work_budget)
    expected_cycles = (100 + work_budget - 1) // work_budget
    check("long program yields across repeated firmware cycles", long_cycles == expected_cycles and long_work == 100)
    check("platform service progresses once per long-program cycle", long_services == long_cycles and long_services > 1)

    stop_cycles, stop_services, stop_work = simulate_bounded_firmware_loop(100, work_budget, stop_at_cycle=3)
    check("stop is observed at bounded service point", stop_cycles == 3 and stop_services == 3)
    check("stop prevents additional VM work in observed cycle", stop_work == min(100, work_budget * 2))

    check("C2 contract records original blocking reference", "blocking" in c2.lower() and "LineMillisecond" in c2)
    check("runtime audit records cooperative current baseline", "LineMillisecond" in audit and "COOPERATIVE" in audit)
    check(
        "compatibility matrix protects Step semantics",
        re.search(r"\|\s*`Step\(\)`(?:\s+logical)?\s+semantics\s*\|\s*unchanged\s*\|", matrix) is not None,
    )
    check(
        "compatibility matrix classifies RunSlice as compatible extension",
        "`RunSlice(...)`" in matrix
        and "existing `Step()`" in matrix
        and "Compatible extension" in matrix,
    )
    check("compatibility matrix requires H35 for opcode changes", "opcode number changes" in matrix)

    print("VM responsiveness compatibility + dual-budget firmware integration: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
