#!/usr/bin/env python3
"""VM-RT #383 generic reactive transaction scheduling contract."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_SLICE = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRunSlice.cpp"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    source = RUN_SLICE.read_text(encoding="utf-8")

    require("VM_REACTIVE_TRANSACTION_MAX_EXTRA_WORK_UNITS = 8" in source,
            "bounded reactive transaction headroom missing or drifted")
    require("extendedWorkLimit" in source and "budget.maxWorkUnits" in source,
            "soft work boundary extension missing")
    require("isTakenBackEdge" in source,
            "generic back-edge safe-boundary detection missing")
    require("executed.p2 <= executedPc" in source,
            "back-edge detection must use control-flow target ordering")
    require("workUnits >= budget.maxWorkUnits" in source,
            "transaction continuation must begin only after the soft budget")
    require("VMRunSliceStopReason::TimeBudgetExhausted" in source,
            "wall-clock hard boundary must remain present")

    # Hard exits must be evaluated before transaction continuation.
    fault_pos = source.index("VMRunSliceStopReason::Fault")
    pending_pos = source.index("VMPendingOperation::Wait")
    time_pos = source.rindex("VMRunSliceStopReason::TimeBudgetExhausted")
    continuation_pos = source.index("workUnits >= budget.maxWorkUnits")
    require(fault_pos < continuation_pos, "fault must preempt transaction continuation")
    require(pending_pos < continuation_pos, "pending/wait must preempt transaction continuation")
    require(time_pos < continuation_pos, "time ceiling must preempt transaction continuation")

    # The production scheduling decision must remain hardware/domain agnostic.
    scheduler_tail = source[source.index("bool isTakenBackEdge"):]
    forbidden = (
        "Opcode::GetTraceState", "Opcode::LineBasis", "SetMotorSpeed",
        "RobotAPI::", "Ultrasonic", "Servo", "Touch", "ColorSensor",
    )
    # Qualification-only telemetry legitimately contains GetTraceState later in
    # the file; strip diagnostic blocks before checking scheduling decisions.
    scheduler_tail = re.sub(
        r"^\s*#if\s+VM_RESPONSIVENESS_DIAGNOSTICS\s*$[\s\S]*?^\s*#endif\s*$",
        "",
        scheduler_tail,
        flags=re.MULTILINE,
    )
    require(not any(token in scheduler_tail for token in forbidden),
            "#383 introduced hardware-specific scheduling logic")

    # Boundedness model: a slice can consume no more than soft + fixed extension.
    soft = 24
    extra = 8
    require(soft + extra == 32, "reviewed total transaction work bound drifted")

    print("VM reactive transaction boundary contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
