#!/usr/bin/env python3
"""EPIC H29 Runtime Cooperative Execution regression contract."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VM_CPP = ROOT / "robot-platform/main/src/Services/VM/VM.cpp"
VM_H = ROOT / "robot-platform/main/src/Services/VM/VM.h"
VM_CONTEXT = ROOT / "robot-platform/main/src/Services/VM/VMContext.h"
VM_SLICE_CPP = ROOT / "robot-platform/main/src/Services/VM/VMRunSlice.cpp"
COOP_H = ROOT / "robot-platform/main/src/Services/VM/CooperativeLineOperation.h"
COOP_CPP = ROOT / "robot-platform/main/src/Services/VM/CooperativeLineOperation.cpp"
MAIN_INO = ROOT / "robot-platform/main/main.ino"
ROBOT_API_CPP = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
DOC = ROOT / "docs/H29_RUNTIME_COOPERATIVE_EXECUTION.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_positive_constant(source: str, name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(\d+)\s*;", source)
    require(match is not None, f"{name} must be explicitly configured")
    value = int(match.group(1))
    require(value > 0, f"{name} must be positive")
    return value


def test_vm_wait_is_cooperative() -> None:
    source = VM_CPP.read_text(encoding="utf-8")
    context = VM_CONTEXT.read_text(encoding="utf-8")

    require("VMPendingOperation::Wait" in source, "WAIT must use VM pending state")
    require("mPendingDeadlineMs" in source, "WAIT must retain a deadline across Step calls")
    require("mContext.IsPendingDeadlineReached(millis())" in source,
            "WAIT completion must poll the VMContext deadline helper without blocking")
    require("bool IsPendingDeadlineReached(uint32_t nowMs) const" in context,
            "VMContext must expose the cooperative WAIT deadline helper")
    require("static_cast<int32_t>(nowMs - mPendingDeadlineMs) >= 0" in context,
            "WAIT deadline comparison must remain wrap-safe")
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
    vm_slice = VM_SLICE_CPP.read_text(encoding="utf-8")

    slice_call = "vm.RunSlice(budget)"
    require(slice_call in main,
            "production firmware loop must invoke the bounded RunSlice scheduler")
    vm_index = main.index(slice_call)
    vm_slice_region = main[:vm_index]

    serial_index = vm_slice_region.rfind("SerialHandler::instance().handleSerial();")
    motion_index = vm_slice_region.rfind("RobotAPI::updateMotion();")
    ultrasonic_index = vm_slice_region.rfind("Ultrasonic::Handle();")
    require(min(serial_index, motion_index, ultrasonic_index) >= 0,
            "communication and control-plane services must exist before the VM slice")
    require(serial_index < motion_index < ultrasonic_index < vm_index,
            "communication and control motion must be serviced before each bounded VM slice")

    work_budget = require_positive_constant(main, "VM_WORK_UNITS_PER_FIRMWARE_CYCLE")
    time_budget_us = require_positive_constant(main, "VM_MAX_SLICE_DURATION_US")
    require(work_budget > 0 and time_budget_us > 0,
            "production VM scheduling must retain positive work and wall-clock bounds")
    require("budget.maxWorkUnits = VM_WORK_UNITS_PER_FIRMWARE_CYCLE;" in main,
            "production work-unit ceiling must be wired into RunSlice")
    require("budget.maxDurationUs = VM_MAX_SLICE_DURATION_US;" in main,
            "production wall-clock ceiling must be wired into RunSlice")

    require("while (workUnits < budget.maxWorkUnits)" in vm_slice,
            "bounded slice execution must remain work-unit limited")
    require("budget.maxDurationUs > 0" in vm_slice,
            "bounded slice execution must conditionally enforce the wall-clock ceiling")
    require("micros() - sliceStartedUs" in vm_slice,
            "wall-clock slice budget must be measured from the slice start")
    require("RunSliceYieldReason::TimeBudgetExhausted" in vm_slice,
            "wall-clock exhaustion must produce an explicit scheduler yield reason")
    require("Step();" in vm_slice,
            "bounded scheduler must advance VM work through legacy Step() semantics")

    require("vm.Step();" not in main,
            "production firmware must not bypass RunSlice with direct Step scheduling")

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
