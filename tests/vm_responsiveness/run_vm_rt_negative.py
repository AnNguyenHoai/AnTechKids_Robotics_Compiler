#!/usr/bin/env python3
"""Negative mutation tests for VM-RT host contracts.

Each mutation models a regression called out by #311/#328/#331. The reusable
guard must reject every mutation; otherwise CI is not proving the intended
fail-closed behavior.
"""
from __future__ import annotations

from dataclasses import replace

from vm_rt_contract_guard import Sources, load_sources, validate


def expect_rejected(name: str, mutated: Sources, token: str) -> None:
    errors = validate(mutated)
    if not errors:
        raise AssertionError(f"{name}: mutation unexpectedly passed")
    if not any(token in error for error in errors):
        raise AssertionError(f"{name}: expected evidence containing {token!r}, got {errors}")
    print(f"PASS: {name} -> rejected")


def main() -> int:
    base = load_sources()
    if validate(base):
        raise AssertionError(f"baseline must pass before mutation tests: {validate(base)}")

    expect_rejected(
        "budget off-by-one regression",
        replace(
            base,
            run_slice_cpp=base.run_slice_cpp.replace(
                "while (workUnits < budget.maxWorkUnits)",
                "while (workUnits <= budget.maxWorkUnits)",
                1,
            ),
        ),
        "budget",
    )

    wait_end = base.vm_cpp.index("case Opcode::CompareEQ:", base.vm_cpp.index("case Opcode::Wait:"))
    mutated_wait = base.vm_cpp[:wait_end] + "        mContext.mProgramCounter++; // injected double advance\n" + base.vm_cpp[wait_end:]
    expect_rejected(
        "pending PC double-advance regression",
        replace(base, vm_cpp=mutated_wait),
        "PC advance",
    )

    wait_start = base.vm_cpp.index("case Opcode::Wait:")
    blocking_wait = base.vm_cpp[:wait_start] + base.vm_cpp[wait_start:].replace(
        "const int32_t requestedMs = mContext.mVariables[instruction.p1];",
        "const int32_t requestedMs = mContext.mVariables[instruction.p1];\n            RobotAPI::Wait(requestedMs);",
        1,
    )
    expect_rejected(
        "blocking Wait regression",
        replace(base, vm_cpp=blocking_wait),
        "blocking",
    )

    expect_rejected(
        "MP3 excluded from deadline helper regression",
        replace(
            base,
            vm_context_h=base.vm_context_h.replace(
                "operation != VMPendingOperation::Wait &&\n            operation != VMPendingOperation::Mp3Play",
                "operation != VMPendingOperation::Wait",
                1,
            ),
        ),
        "Mp3Play",
    )

    expect_rejected(
        "deadline ownership guard removed",
        replace(
            base,
            vm_context_h=base.vm_context_h.replace(
                "!mPendingOperation.IsOwnedBy(mProgramCounter)",
                "false",
                1,
            ),
        ),
        "current-PC ownership",
    )

    expect_rejected(
        "unbounded Pow work regression",
        replace(
            base,
            vm_cpp=base.vm_cpp.replace(
                "mContext.mPendingPowRemaining > 0 &&\n                       multiplies < POW_MULTIPLIES_PER_STEP",
                "mContext.mPendingPowRemaining > 0",
                1,
            ),
        ),
        "Pow work",
    )

    expect_rejected(
        "duplicate line-snapshot physical read regression",
        replace(
            base,
            snapshot_cpp=base.snapshot_cpp.replace(
                "if (g_sampledThisCycle)",
                "if (false && g_sampledThisCycle)",
                1,
            ),
        ),
        "reuse guard",
    )

    expect_rejected(
        "legacy Step double-dispatch regression",
        replace(
            base,
            vm_cpp=base.vm_cpp.replace(
                "ExecuteInstruction(instruction);",
                "ExecuteInstruction(instruction);\n    ExecuteInstruction(instruction);",
                1,
            ),
        ),
        "dispatch count",
    )

    expect_rejected(
        "firmware opcode compatibility drift",
        replace(
            base,
            firmware_opcode_h=base.firmware_opcode_h.replace("Forward = 2,", "Forward = 99,", 1),
        ),
        "firmware opcode drift",
    )

    print("VM-RT negative regression mutations: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
