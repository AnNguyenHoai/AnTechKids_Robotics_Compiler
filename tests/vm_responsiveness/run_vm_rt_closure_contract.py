#!/usr/bin/env python3
"""VM-RT K closure contract: compatibility and evidence truth must stay synchronized."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "packages" / "robot-isa" / "compatibility_policy.json"
THRESHOLDS = ROOT / "docs" / "VM_RESPONSIVENESS_THRESHOLDS.json"
AUDIT = ROOT / "docs" / "VM_RT_CLOSURE_AUDIT.md"
FIRMWARE_MAIN = ROOT / "robot-platform" / "main" / "main.ino"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_int(source: str, name: str) -> int:
    match = re.search(rf"{re.escape(name)}\s*=\s*(\d+)", source)
    if not match:
        raise AssertionError(f"missing firmware constant {name}")
    return int(match.group(1))


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    thresholds = json.loads(THRESHOLDS.read_text(encoding="utf-8"))
    audit = AUDIT.read_text(encoding="utf-8")
    firmware = FIRMWARE_MAIN.read_text(encoding="utf-8")

    current = policy["current"]
    require(current["platform_contract_generation"] == 1, "VM-RT must not silently bump platform generation")
    require(current["compiler_generation"] == 1, "VM-RT must not silently bump compiler generation")
    require(current["firmware_generation"] == 1, "VM-RT must not silently bump firmware generation")
    require(policy["upgrade_rules"]["unknown_generation"] == "reject", "unknown compatibility generations must remain fail-closed")
    require(any(p["compiler_generation"] == 1 and p["firmware_generation"] == 1 and p["status"] == "supported" for p in policy["supported_pairs"]), "generation 1 compiler/firmware pair must remain explicitly supported")

    approved = bool(thresholds["approval"]["approved"])
    values = thresholds["thresholds"]
    evidence = thresholds["approval"].get("evidence", [])
    if approved:
        require(thresholds["status"] != "UNAPPROVED_PENDING_PHYSICAL_EVIDENCE", "approved thresholds cannot retain pending status")
        require(all(v is not None for v in values.values()), "approved physical qualification requires every threshold to be populated")
        require(bool(evidence), "approved physical qualification requires evidence links")
    else:
        require(thresholds["status"] == "UNAPPROVED_PENDING_PHYSICAL_EVIDENCE", "unapproved thresholds must remain explicitly pending")
        require(all(v is None for v in values.values()), "unapproved physical qualification must not contain guessed thresholds")
        require(not evidence, "unapproved physical qualification must not claim evidence")
        require(str(thresholds.get("runtime_config_status", "")).startswith("PROVISIONAL_"),
                "scheduler config must remain explicitly provisional until physical qualification")

    # Runtime configuration is allowed to change in response to an observed
    # physical failure or deterministic scheduler evidence, but the manifest
    # must always describe the firmware that will be qualified. This does not
    # approve any production threshold.
    firmware_work_budget = extract_int(firmware, "VM_WORK_UNITS_PER_FIRMWARE_CYCLE")
    firmware_time_budget = extract_int(firmware, "VM_MAX_SLICE_DURATION_US")
    require(thresholds["slice_budget_work_units"] == firmware_work_budget,
            "threshold manifest work budget must match firmware under qualification")
    require(thresholds["slice_budget_duration_us"] == firmware_time_budget,
            "threshold manifest time budget must match firmware under qualification")

    require("NO GENERATION CHANGE REQUIRED" in audit, "closure audit must record H35 classification")

    # Historical reconciliation issues remain part of the closure audit trail
    # even when later work supersedes/closes individual owners. The audit must
    # retain traceability and prevent premature epic closure.
    for issue in ("#312", "#325", "#336", "#337", "#338", "#339", "#340", "#341", "#342", "#343", "#344"):
        require(issue in audit, f"closure audit must retain historical blocker traceability {issue}")
    require("#325 is the only" not in audit, "closure audit must not claim #325 is the only blocker after #330")
    require("Parent #302 must remain open until #313" in audit, "closure audit must prevent premature epic closure")

    print("VM-RT K closure contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
