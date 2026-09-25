#!/usr/bin/env python3
"""VM responsiveness baseline / production integration regression gate.

This gate protects the legacy Step() compatibility contract together with the
cooperative pending-operation cleanup and the production RunSlice scheduling
boundary. It intentionally checks observable/source contracts rather than
requiring cleanup logic to remain duplicated at individual call sites.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VM_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"
CTX_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMContext.h"
FIRMWARE = ROOT / "robot-platform" / "main" / "main.ino"
FIXTURE = ROOT / "docs" / "VM_RESPONSIVENESS_COMPATIBILITY_MATRIX.md"
OPCODE_H = ROOT / "robot-platform" / "main" / "include" / "generated" / "opcode.h"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def simulate_bounded_firmware_loop(total_work: int, budget: int, stop_at_cycle: int | None = None):
    cycle = 0
    platform_service_ticks = 0
    work = 0
    while work < total_work:
        cycle += 1
        platform_service_ticks += 1
        if stop_at_cycle is not None and cycle == stop_at_cycle:
            break
        work += min(budget, total_work - work)
    return cycle, platform_service_ticks, work


def main() -> int:
    vm = VM_CPP.read_text(encoding="utf-8")
    ctx = CTX_H.read_text(encoding="utf-8")
    firmware = FIRMWARE.read_text(encoding="utf-8")
    fixture = FIXTURE.read_text(encoding="utf-8")
    opcode_h = OPCODE_H.read_text(encoding="utf-8")

    check("fixture schema is version 1", "Schema version: 1" in fixture)
    check("baseline is pinned to post-#303 main", "post-#303" in fixture)
    check("compatibility generation remains 1", "Compatibility generation: 1" in fixture)
    check("opcode numbering is frozen", "Opcode numbering: frozen" in fixture)
    check("bytecode encoding is frozen", "Bytecode encoding: frozen" in fixture)
    check("Step semantics are frozen", "VM::Step semantics: frozen" in fixture)
    check("representative baseline fixture set exists", "immediate_load_const" in fixture and "division_by_zero" in fixture)

    opcode_numbers = {}
    for line in opcode_h.splitlines():
        line = line.strip().rstrip(",")
        if " = " in line and not line.startswith("enum"):
            name, raw = line.split(" = ", 1)
            if raw.isdigit():
                opcode_numbers[name.strip()] = int(raw)

    fixtures = {
        "immediate_load_const": [("LoadConst", 1)],
        "wait_pending_resume": [("LoadConst", 1), ("Wait", 7)],
        "line_millisecond_pending_resume": [("LoadConst", 1), ("LoadConst", 1), ("LineMillisecond", 59)],
        "line_intersection_pending_resume": [("LineIntersectionStop", 40)],
        "line_turn_pending_resume": [("LineTurnEncounterLine", 50)],
        "line_bmp_pending_resume": [("LineForBmp", 51)],
        "jump_to_program_end": [("Jump", 14)],
        "division_by_zero": [("Div", 23)],
    }
    for fixture_name, opcodes in fixtures.items():
        check(f"fixture {fixture_name} has Step contract", fixture_name in fixture)
        for name, number in opcodes:
            check(f"{fixture_name} opcode {name} number matches canonical header", opcode_numbers.get(name) == number)

    check("VM exposes legacy Step", "void VM::Step()" in vm)
    step_start = vm.index("void VM::Step()")
    step_end = vm.index("bool VM::ContinuePendingLineOperation()", step_start)
    step_body = vm[step_start:step_end]
    check("Step dispatches current instruction exactly once", step_body.count("ExecuteInstruction(instruction);") == 1)
    check("Step itself has no unbounded instruction loop", "while (" not in step_body and "for (" not in step_body)

    wait_start = vm.index("case Opcode::Wait:")
    wait_end = vm.index("case Opcode::CompareEQ:", wait_start)
    wait_block = vm[wait_start:wait_end]
    check("Wait initializes pending state", "VMPendingOperation::Wait" in wait_block)
    check("Wait does not use blocking delay", "delay(" not in wait_block and "RobotAPI::Wait" not in wait_block)
    check("Wait advances PC on immediate/non-positive or completion paths", wait_block.count("mContext.mProgramCounter++;") >= 2)

    # Cooperative C2 line operations must remain pending/resume dispatches.
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

    # Cleanup is intentionally centralized. Reset/stop/fault must call the
    # helper, while the helper owns line, MP3 and generic pending-state cleanup.
    cancel_start = vm.index("void VM::CancelPendingOperation(bool stopLineMotors)")
    cancel_end = vm.index("void VM::Reset()", cancel_start)
    cancel_body = vm[cancel_start:cancel_end]
    check("central pending cleanup cancels cooperative line state", "CooperativeLineOperation::Cancel(stopLineMotors);" in cancel_body)
    check("central pending cleanup finalizes cooperative MP3", "RobotAPI::EndMp3PlayCooperative();" in cancel_body)
    check("central pending cleanup clears generic pending ownership", "mContext.ClearPendingOperation();" in cancel_body)

    reset_body = vm[vm.index("void VM::Reset()") : vm.index("bool VM::LoadProgram")]
    check("Reset uses centralized pending cleanup", "CancelPendingOperation(true);" in reset_body)
    check("fault cleanup uses centralized pending cleanup", "Stop on a real VM error" in step_body and "CancelPendingOperation(true);" in step_body)
    check("normal program-end cleanup uses centralized pending cleanup", step_body.count("CancelPendingOperation(true);") >= 2)

    # VM-RT G production integration: the firmware loop, not ad-hoc Step calls,
    # is the scheduling owner around RunSlice.
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
    check("platform service progresses once per long-program cycle", long_services == long_cycles)

    stop_cycles, stop_services, stop_work = simulate_bounded_firmware_loop(100, 4, stop_at_cycle=3)
    check("stop is observed at bounded pre-slice service point", stop_cycles == 3 and stop_services == 3)
    check("no VM work runs after observed stop in that cycle", stop_work == 8)

    print("VM responsiveness baseline + production integration: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
