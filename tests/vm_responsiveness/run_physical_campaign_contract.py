#!/usr/bin/env python3
"""Contract tests for #325 physical campaign aggregation."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "vm_rt_physical_campaign.py"

spec = importlib.util.spec_from_file_location("vm_rt_physical_campaign", TOOL)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def report(scenario: str, *, stop_count: int = 0, stop_max: int = 0, commit: str = "abc123", budget: int = 4) -> dict:
    return {
        "physical_robot": True,
        "qualification_status": "PHYSICAL_EVIDENCE_CAPTURED",
        "scenario": scenario,
        "firmware_commit": commit,
        "slice_configuration": {"max_work_units": budget},
        "slice_duration_us": {"count": 10, "max": 400},
        "work_unit_duration_us": {"count": 10, "max": 120},
        "line_snapshot_age_us": {"count": 10, "max": 150},
        "stop_latency_us": {"count": stop_count, "max": stop_max},
        "slowest_work_units": [{"slice": 1, "pc": 2, "duration_us": 120}],
        "_source": f"fixture/{scenario}/qualification-report.json",
    }


def main() -> int:
    reports = [report(name) for name in module.REQUIRED_SCENARIOS]
    for row in reports:
        if row["scenario"] == "stop_abort_pending":
            row["stop_latency_us"] = {"count": 3, "max": 220}

    incomplete = module.build_campaign(reports)
    assert incomplete["campaign_status"] == "INCOMPLETE_PHYSICAL_EVIDENCE"
    assert any("sensor-to-decision-to-motor" in item for item in incomplete["blockers"])
    assert incomplete["approval"]["approved"] is False

    external = {
        "reviewed": True,
        "sensor_to_decision_to_motor_us_max": 900,
        "method": "logic_analyzer",
        "evidence": ["artifacts/vm-rt/external/latency.csv"],
    }
    ready = module.build_campaign(reports, external)
    assert ready["campaign_status"] == "READY_FOR_HUMAN_APPROVAL"
    assert ready["blockers"] == []
    assert ready["measured_threshold_proposal"]["slice_duration_us_max"] == 400
    assert ready["measured_threshold_proposal"]["work_unit_duration_us_max"] == 120
    assert ready["measured_threshold_proposal"]["stop_abort_latency_us_max"] == 220
    assert ready["measured_threshold_proposal"]["line_snapshot_age_us_max"] == 150
    assert ready["measured_threshold_proposal"]["sensor_to_decision_to_motor_us_max"] == 900
    assert ready["approval"]["approved"] is False

    drift = [dict(row) for row in reports]
    drift[0] = dict(drift[0], firmware_commit="different")
    drifted = module.build_campaign(drift, external)
    assert drifted["campaign_status"] == "INCOMPLETE_PHYSICAL_EVIDENCE"
    assert any("exactly one firmware commit" in item for item in drifted["blockers"])

    print("VM-RT physical campaign contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
