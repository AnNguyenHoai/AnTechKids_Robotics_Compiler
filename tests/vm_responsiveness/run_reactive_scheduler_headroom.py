#!/usr/bin/env python3
"""VM-RT #382 generic reactive scheduler/headroom contract.

This is a deterministic host/source gate. It does not claim ESP32 wall-clock
performance; physical thresholds remain owned by #312/#325/#386.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "robot-platform" / "main" / "main.ino"
RUN_SLICE = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRunSlice.cpp"
PLATFORMIO = ROOT / "robot-platform" / "platformio.ini"
THRESHOLDS = ROOT / "docs" / "VM_RESPONSIVENESS_THRESHOLDS.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def strip_diagnostic_blocks(source: str) -> str:
    """Remove #382-allowed qualification-only instrumentation before genericity checks.

    RunSlice already contains line-snapshot lifecycle and qualification telemetry from
    earlier VM-RT work. Hardware-agnostic scheduling means those observations must not
    affect scheduling decisions; it does not mean the source file may not observe an
    opcode inside code compiled out of production.
    """
    pattern = re.compile(
        r"^\s*#if\s+VM_RESPONSIVENESS_DIAGNOSTICS\s*$"
        r"[\s\S]*?"
        r"^\s*#endif\s*$",
        re.MULTILINE,
    )
    return pattern.sub("", source)


def main() -> int:
    firmware = MAIN.read_text(encoding="utf-8")
    run_slice = RUN_SLICE.read_text(encoding="utf-8")
    platformio = PLATFORMIO.read_text(encoding="utf-8")
    thresholds = json.loads(THRESHOLDS.read_text(encoding="utf-8"))

    work_match = re.search(r"VM_WORK_UNITS_PER_FIRMWARE_CYCLE\s*=\s*(\d+)", firmware)
    time_match = re.search(r"VM_MAX_SLICE_DURATION_US\s*=\s*(\d+)", firmware)
    require(work_match is not None, "production work-unit ceiling missing")
    require(time_match is not None, "production wall-clock ceiling missing")

    work_units = int(work_match.group(1))
    duration_us = int(time_match.group(1))
    require(work_units == 24, "#382 must use the minimal reviewed 24-work-unit headroom")
    require(duration_us == 2000, "#382 must not weaken the 2 ms wall-clock ceiling")

    # Generic representative control-flow model: three independent predicates,
    # each costing 4 units when false and 7 when true, plus loop back-edge.
    # This deliberately contains no hardware/API names; it models VM structure.
    def reactive_iteration(active_branches: int) -> int:
        return (3 - active_branches) * 4 + active_branches * 7 + 1

    costs = [reactive_iteration(n) for n in range(4)]
    require(costs == [13, 16, 19, 22], f"representative work model drifted: {costs}")
    require(max(costs) <= work_units, "representative reactive iteration still splits on work ceiling")
    require(work_units < 32, "headroom grew beyond the minimal reviewed range without evidence")

    # #382 is scheduler infrastructure, not a line-follow/compiler special case.
    # Existing snapshot ownership and qualification-only reactive telemetry are
    # permitted. What must remain absent from the production scheduling path is
    # hardware/API/opcode-specific decision logic that changes yield/continue/return
    # behavior for a particular device or domain.
    production_scheduler = strip_diagnostic_blocks(run_slice)
    scheduler_specific_tokens = (
        "LineFollower", "LinePerception", "Opcode::GetTraceState",
        "Opcode::LineBasis", "RobotAPI::", "SetMotorSpeed", "Ultrasonic",
        "Servo", "Touch", "ColorSensor",
    )
    require(not any(token in production_scheduler for token in scheduler_specific_tokens),
            "production RunSlice contains hardware/domain-specific scheduling logic")
    require("LineSnapshotCycleGuard" in production_scheduler,
            "pre-existing shared snapshot lifecycle must remain compatible")

    require("#if VM_RESPONSIVENESS_DIAGNOSTICS" in run_slice,
            "detailed per-opcode timing must be qualification/debug gated")
    diag_block_start = run_slice.index("#if VM_RESPONSIVENESS_DIAGNOSTICS")
    step_pos = run_slice.index("Step();")
    require(diag_block_start < step_pos, "qualification timing guard must surround pre-Step timing")
    require("const uint32_t workStartUs = micros();" in run_slice,
            "qualification profile lost per-opcode start timestamp")
    require("const uint32_t workEndUs = micros();" in run_slice,
            "qualification profile lost per-opcode end timestamp")
    require("const uint32_t workDurationUs = workEndUs - workStartUs;" in run_slice,
            "qualification profile lost work-unit duration evidence")
    require("budget.maxDurationUs != 0" in run_slice and "micros() - sliceStartUs" in run_slice,
            "production wall-clock enforcement must remain independent of detailed instrumentation")

    require("[env:esp32dev_vm_qualification]" in platformio and
            "-DVM_RESPONSIVENESS_DIAGNOSTICS=1" in platformio,
            "qualification profile must explicitly enable detailed timing")
    production_section = platformio.split("[env:esp32dev]", 1)[1].split("[env:esp32dev_ota]", 1)[0]
    require("VM_RESPONSIVENESS_DIAGNOSTICS=1" not in production_section,
            "production profile must not enable per-opcode diagnostics")

    require(thresholds["status"] == "UNAPPROVED_PENDING_PHYSICAL_EVIDENCE",
            "host optimization must not approve physical thresholds")
    require(thresholds["approval"]["approved"] is False,
            "host optimization must keep physical approval false")
    require(thresholds["slice_budget_work_units"] == work_units,
            "qualification manifest must identify the active work ceiling")
    require(thresholds["slice_budget_duration_us"] == duration_us,
            "qualification manifest must identify the active time ceiling")

    print("VM reactive scheduler headroom contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
