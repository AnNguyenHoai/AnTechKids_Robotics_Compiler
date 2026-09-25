#!/usr/bin/env python3
"""Source contract for the September 2026 real-robot latency corrective work."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "robot-platform" / "main" / "main.ino"
VM_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.h"
VM_SLICE = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRunSlice.cpp"
TELEMETRY = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRuntimeTelemetry.cpp"
DIAGNOSTICS = ROOT / "robot-platform" / "main" / "src" / "Diagnostics" / "DiagnosticsManager.cpp"
FOLLOWER = ROOT / "robot-platform" / "main" / "src" / "Services" / "Line" / "LineFollower.cpp"
STATE = ROOT / "robot-platform" / "main" / "src" / "Services" / "Line" / "FollowerStateMachine.cpp"
RECOVERY = ROOT / "robot-platform" / "main" / "src" / "Services" / "Line" / "RecoveryStrategy.cpp"
THRESHOLDS = ROOT / "docs" / "VM_RESPONSIVENESS_THRESHOLDS.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    main = MAIN.read_text(encoding="utf-8")
    vm_h = VM_H.read_text(encoding="utf-8")
    vm_slice = VM_SLICE.read_text(encoding="utf-8")
    telemetry = TELEMETRY.read_text(encoding="utf-8")
    diagnostics = DIAGNOSTICS.read_text(encoding="utf-8")
    follower = FOLLOWER.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")
    recovery = RECOVERY.read_text(encoding="utf-8")
    thresholds = json.loads(THRESHOLDS.read_text(encoding="utf-8"))

    require("VM_WORK_UNITS_PER_FIRMWARE_CYCLE = 16" in main, "corrective work ceiling drifted")
    require("VM_MAX_SLICE_DURATION_US = 2000" in main, "corrective time ceiling drifted")
    require("uint32_t maxDurationUs = 0;" in vm_h, "optional wall-clock budget missing")
    require("TimeBudgetExhausted" in vm_h and "budget.maxDurationUs != 0" in vm_slice,
            "RunSlice wall-clock exit contract missing")

    hot = main[main.index("if (runVmSlice)"):main.index("if (vm.IsRunning())")]
    require("RecordSlice" in hot, "hot path must record slice evidence")
    require("PrintLatestJson" not in hot and "PrintBufferedJson" not in hot,
            "active VM path must not stream qualification JSON")
    require("g_sliceBuffer" in telemetry and "kSliceBufferCapacity = 256" in telemetry,
            "qualification telemetry ring missing")
    require("lastRecord ? g_snapshot.lastStopLatencyUs : 0u" in telemetry,
            "one stop observation must not be duplicated across buffered records")

    # One physical line sample must be shared across platform refresh, VM/control
    # work and diagnostics for the whole firmware cycle. RunSlice owns a cycle
    # only when no outer firmware scope is active (standalone/test compatibility).
    loop = main[main.index("void loop()") :]
    begin = loop.index("LineSensorSnapshot::BeginCycle();")
    sensor_refresh = loop.index("SensorManager::instance().updateAll();")
    vm_slice_call = loop.index("vm.RunSlice(budget);")
    diagnostics_update = loop.index("DiagnosticsManager::instance().updateSensors();")
    end = loop.index("LineSensorSnapshot::EndCycle();")
    require(begin < sensor_refresh < vm_slice_call < diagnostics_update < end,
            "firmware cycle must own one line snapshot across sensor -> VM -> diagnostics")
    require("mOwnsCycle(!LineSensorSnapshot::IsCycleActive())" in vm_slice,
            "RunSlice must detect an outer snapshot owner")
    require("if (mOwnsCycle)" in vm_slice,
            "RunSlice must only begin/end a snapshot it owns")
    require("lineSensor->update();" not in diagnostics,
            "DiagnosticsManager must not own a second physical line read")

    require("kLostConfirmMs = 10" in state and "kLostConfirmSamples" not in state,
            "line-loss confirmation must remain time-based")
    require("_pid(1.2f, 0.0f, 0.0f, 0.02f)" in follower and "_scaleFactor(15.0f)" in follower,
            "responsive P-only line baseline drifted")
    require("kSoftSearchMs = 120" in recovery,
            "soft recovery latency drifted")

    require(thresholds["status"] == "UNAPPROVED_PENDING_PHYSICAL_EVIDENCE",
            "corrective change must not auto-approve physical thresholds")
    require(thresholds["approval"]["approved"] is False,
            "corrective change must keep approval false")
    require(all(value is None for value in thresholds["thresholds"].values()),
            "corrective change must not invent physical thresholds")
    require(thresholds["slice_budget_work_units"] == 16 and thresholds["slice_budget_duration_us"] == 2000,
            "manifest must identify exact corrective scheduler config")

    print("VM control-latency corrective contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
