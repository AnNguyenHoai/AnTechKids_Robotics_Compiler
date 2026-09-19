#!/usr/bin/env python3
"""EPIC H29 Runtime Cooperative Execution regression contract."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VM_CPP = ROOT / "robot-platform/main/src/Services/VM/VM.cpp"
VM_H = ROOT / "robot-platform/main/src/Services/VM/VM.h"
VM_CONTEXT = ROOT / "robot-platform/main/src/Services/VM/VMContext.h"
COOP_H = ROOT / "robot-platform/main/src/Services/VM/CooperativeLineOperation.h"
COOP_CPP = ROOT / "robot-platform/main/src/Services/VM/CooperativeLineOperation.cpp"
MAIN_INO = ROOT / "robot-platform/main/main.ino"
ROBOT_API_CPP = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
DOC = ROOT / "docs/H29_RUNTIME_COOPERATIVE_EXECUTION.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_vm_wait_is_cooperative() -> None:
    source = VM_CPP.read_text(encoding="utf-8")
    context = VM_CONTEXT.read_text(encoding="utf-8")

    require("VMPendingOperation::Wait" in source, "WAIT must use VM pending state")
    require("mPendingDeadlineMs" in source, "WAIT must retain a deadline across Step calls")
    require("deadlineReached(millis(), mContext.mPendingDeadlineMs)" in source,
            "WAIT completion must be polled without blocking")
    require("RobotAPI::Wait(" not in source,
            "VM WAIT must never call the legacy blocking RobotAPI::Wait")
    require("VMPendingOperation" in context and "ClearPendingOperation" in context,
            "VMContext must own cooperative execution state")


def test_long_running_line_opcodes_use_state_machine() -> None:
    vm = VM_CPP.read_text(encoding="utf-8")
    coop = COOP_CPP.read_text(encoding="utf-8")
    header = COOP_H.read_text(encoding="utf-8")

    for legacy_call in (
        "RobotAPI::LineMillisecond(",
        "RobotAPI::LineIntersectionStop(",
        "RobotAPI::LineTurnEncounterLine(",
        "RobotAPI::LineForBmp(",
    ):
        require(legacy_call not in vm, f"VM must not enter blocking legacy path: {legacy_call}")

    for starter in (
        "StartMillisecond",
        "StartIntersectionStop",
        "StartTurnEncounterLine",
        "StartBmp",
    ):
        require(starter in vm and starter in header,
                f"Missing cooperative line starter: {starter}")

    require("ContinuePendingLineOperation" in vm,
            "VM must hold PC while a cooperative line operation is pending")
    require("kLineTickIntervalMs = 20UL" in coop,
            "line state machine must retain the existing 20 ms control cadence")
    require("RobotAPI::LineBasis(g_state.speed)" in coop,
            "each cooperative update must execute one bounded line-control tick")
    require("!follower.isTurnRequested()" in coop,
            "turn completion must use the same line-follower tick state, not a second sensor sample")
    require("delay(" not in coop, "cooperative line operation must never delay")
    require("while (" not in coop and "while(" not in coop,
            "cooperative line operation must never contain an internal loop")


def test_control_plane_keeps_scheduler_priority() -> None:
    main = MAIN_INO.read_text(encoding="utf-8")
    network_index = main.index("RobotNetworkService::update();")
    vm_index = main.index("vm.Step();")
    require(network_index < vm_index,
            "network/control-plane update must run before each VM cooperative step")

    vm = VM_CPP.read_text(encoding="utf-8")
    require("#define VM_TRACE_ENABLED 0" in vm,
            "instruction trace must default off so tight loops cannot flood Serial")
    require("#if VM_TRACE_ENABLED" in vm,
            "trace gate must be value-aware rather than #ifdef")


def test_legacy_blockers_are_isolated_from_vm_path() -> None:
    """Document the migration boundary until legacy wrappers are removed."""
    robot_api = ROBOT_API_CPP.read_text(encoding="utf-8")
    vm = VM_CPP.read_text(encoding="utf-8")

    require("void Wait(uint32_t ms)" in robot_api,
            "legacy Wait wrapper unexpectedly disappeared; update migration contract")
    require("RobotAPI::Wait(" not in vm,
            "student VM path regressed to legacy blocking Wait")


def test_contract_documented() -> None:
    require(DOC.is_file(), "H29 runtime execution contract document is required")
    text = DOC.read_text(encoding="utf-8")
    for phrase in (
        "MUST return control",
        "program counter",
        "Wi-Fi",
        "OTA",
        "discovery",
    ):
        require(phrase in text, f"H29 contract is missing: {phrase}")


def main() -> int:
    tests = [
        test_vm_wait_is_cooperative,
        test_long_running_line_opcodes_use_state_machine,
        test_control_plane_keeps_scheduler_priority,
        test_legacy_blockers_are_isolated_from_vm_path,
        test_contract_documented,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print("EPIC H29 Runtime Cooperative Execution: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
