#!/usr/bin/env python3
"""VM responsiveness compatibility + production loop integration gate.

This deterministic host gate freezes legacy Step()/dispatch semantics and checks
that production firmware schedules bounded RunSlice work without starving the
platform control plane. It intentionally does not claim ESP32 wall-clock timing;
that evidence belongs to VM-RT H/J.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "vm_responsiveness" / "fixtures" / "step_baseline.json"
VM_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"
VM_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.h"
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


def simulate_bounded_firmware_loop(total_work: int, budget: int, stop_at_cycle: int | None = None) -> tuple[int, int, int]:
    """Tiny scheduler model for the VM-RT G integration invariants.

    Platform service advances once before each bounded VM slice. A stop request
    observed at the service point prevents any further VM work that cycle.
    """
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


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    vm = VM_CPP.read_text(encoding="utf-8")
    vm_h = VM_H.read_text(encoding="utf-8")
    ctx = CTX_H.read_text(encoding="utf-8")
    opcodes = opcode_map(OPCODE_H.read_text(encoding="utf-8"))
    firmware = FIRMWARE_MAIN.read_text(encoding="utf-8")
    matrix = MATRIX.read_text(encoding="utf-8")
    c2 = C2.read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")

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

    loop = firmware[firmware.index("void loop()") :]
    check("production loop uses bounded RunSlice", "vm.RunSlice(budget);" in loop)
    check("production loop no longer invokes VM Step directly", "vm.Step();" not in loop)
    check("firmware defines conservative VM work-unit budget", "VM_WORK_UNITS_PER_FIRMWARE_CYCLE = 4" in firmware)
    check("serial service runs before VM slice", loop.index("SerialCommandHandler::handle();") < loop.index("vm.RunSlice(budget);"))
    check("network service runs before VM slice", loop.index("RobotNetworkService::update();") < loop.index("vm.RunSlice(budget);"))
    check("OTA gate runs before VM slice", loop.index("RobotNetworkService::isUpdateInProgress()") < loop.index("vm.RunSlice(budget);"))
    check("platform sensors refresh before VM slice", loop.index("SensorManager::instance().updateAll();") < loop.index("vm.RunSlice(budget);"))
    check("motion/output service runs before VM slice", loop.index("RobotAPI::updateMotion();") < loop.index("vm.RunSlice(budget);"))
    check("loop diagnostics records after VM scheduling", loop.rindex("DiagnosticsManager::instance().recordLoopTime(elapsed);") > loop.index("vm.RunSlice(budget);"))
    check("VM completion does not enter nested firmware halt loop", "while (1)" not in loop)
    check("VM fault stops robot outputs", "RobotAPI::Stop();" in loop[loop.index("if (err != 0)") : loop.index("} else {", loop.index("if (err != 0)"))])

    long_cycles, long_services, long_work = simulate_bounded_firmware_loop(100, 4)
    check("long program yields across repeated firmware cycles", long_cycles == 25 and long_work == 100)
    check("platform service progresses once per long-program cycle", long_services == long_cycles and long_services > 1)

    stop_cycles, stop_services, stop_work = simulate_bounded_firmware_loop(100, 4, stop_at_cycle=3)
    check("stop is observed at bounded pre-slice service point", stop_cycles == 3 and stop_services == 3)
    check("stop prevents additional VM work in observed cycle", stop_work == 8)

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

    print("VM responsiveness compatibility + firmware main-loop integration: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
