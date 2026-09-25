#!/usr/bin/env python3
"""VM-RT B compatibility baseline gate.

This gate freezes the pre-RunSlice Step()/dispatch contract at source/fixture level.
It intentionally does not pretend to be an ESP32 timing or physical-hardware test.
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


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    vm = VM_CPP.read_text(encoding="utf-8")
    vm_h = VM_H.read_text(encoding="utf-8")
    ctx = CTX_H.read_text(encoding="utf-8")
    opcodes = opcode_map(OPCODE_H.read_text(encoding="utf-8"))
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

    # Direct Step regression boundary: one dispatch invocation per Step() call.
    check("VM exposes legacy Step", "void Step();" in vm_h)
    step_start = vm.index("void VM::Step()")
    step_end = vm.index("bool VM::ContinuePendingLineOperation()", step_start)
    step_body = vm[step_start:step_end]
    check("Step dispatches current instruction exactly once", step_body.count("ExecuteInstruction(instruction);") == 1)
    check("Step itself has no unbounded instruction loop", "while (" not in step_body and "for (" not in step_body)

    # Wait must retain INIT -> PENDING -> COMPLETE PC semantics.
    wait_start = vm.index("case Opcode::Wait:")
    wait_end = vm.index("case Opcode::CompareEQ:", wait_start)
    wait = vm[wait_start:wait_end]
    check("Wait initializes pending state", "VMPendingOperation::Wait" in wait and "mPendingDeadlineMs" in wait)
    check("Wait does not use blocking delay", "delay(" not in wait)
    check("Wait advances PC on immediate/non-positive or completion paths", wait.count("mProgramCounter++") == 2)

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
    check("Reset cancels cooperative line state", "CooperativeLineOperation::Cancel(true);" in vm[vm.index("void VM::Reset()"):vm.index("bool VM::LoadProgram")])
    check("fault cleanup cancels cooperative line state", "Stop on a real VM error" in step_body and "CooperativeLineOperation::Cancel(true);" in step_body)

    # C2 traceability: its historical blocking semantics remain recorded, while
    # the newer audit/matrix explicitly define the cooperative scheduling posture.
    check("C2 contract records original blocking reference", "blocking" in c2.lower() and "LineMillisecond" in c2)
    check("runtime audit records cooperative current baseline", "LineMillisecond" in audit and "COOPERATIVE" in audit)
    check("compatibility matrix protects Step semantics", "`Step()` semantics | unchanged" in matrix)
    check(
        "compatibility matrix classifies RunSlice as compatible extension",
        "`RunSlice(...)`" in matrix
        and "existing `Step()`" in matrix
        and "Compatible extension" in matrix,
    )
    check("compatibility matrix requires H35 for opcode changes", "opcode number changes" in matrix)

    print("VM responsiveness compatibility baseline: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
