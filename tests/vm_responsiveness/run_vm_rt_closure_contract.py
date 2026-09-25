#!/usr/bin/env python3
"""VM-RT K closure contract: compatibility and evidence truth must stay synchronized."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "packages" / "robot-isa" / "compatibility_policy.json"
THRESHOLDS = ROOT / "docs" / "VM_RESPONSIVENESS_THRESHOLDS.json"
AUDIT = ROOT / "docs" / "VM_RT_CLOSURE_AUDIT.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    thresholds = json.loads(THRESHOLDS.read_text(encoding="utf-8"))
    audit = AUDIT.read_text(encoding="utf-8")

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

    require(thresholds["slice_budget_work_units"] == 4, "slice budget must not be tuned without approved physical evidence")
    require("NO GENERATION CHANGE REQUIRED" in audit, "closure audit must record H35 classification")
    require("#325" in audit, "closure audit must track the physical-evidence blocker")
    require("must remain open until #325 is complete" in audit, "closure audit must prevent premature epic closure")

    print("VM-RT K closure contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
