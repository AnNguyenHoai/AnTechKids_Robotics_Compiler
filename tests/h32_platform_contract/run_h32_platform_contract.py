#!/usr/bin/env python3
"""EPIC H32 Platform Contract Consolidation regression gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import platform_contract


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def test_consolidated_contract() -> dict:
    first = platform_contract.build_contract()
    second = platform_contract.build_contract()
    check(first == second, "platform contract generation is deterministic")
    check(first["type"] == "antechkids.robot.platform-contract", "contract type is stable")
    check(first["schema_version"] == 1, "contract schema is stable")
    check(first["generated"] is True, "contract explicitly declares generated projection")
    check(len(first["operations"]) == 60, "all 60 canonical opcodes are consolidated")
    check(len(first["capabilities"]) == 16, "all 16 capabilities are consolidated")
    check(len(first["targets"]) == 3, "all 3 target profiles are consolidated")

    operations = first["operations"]
    check(len({row["id"] for row in operations}) == len(operations), "canonical IDs stay unique")
    check(len({row["producer_name"] for row in operations}) == len(operations), "producer names stay unique")
    check(len({row["numeric_code"] for row in operations}) == len(operations), "wire opcode IDs stay unique")
    check(
        [row["canonical_index"] for row in operations] == list(range(len(operations))),
        "canonical opcode order remains contiguous",
    )
    check(sum(1 for row in operations if row["api"]["public"]) == 38, "38 user/platform operations remain public")
    check(sum(1 for row in operations if not row["api"]["public"]) == 22, "22 VM operations remain internal")
    return first


def test_target_support(contract: dict) -> None:
    by_name = {row["producer_name"]: row for row in contract["operations"]}
    check(
        by_name["MoveInitialize"]["supported_targets"] == ["robosim"],
        "encoder initialization remains RoboSim-only",
    )
    check(
        by_name["MoveRunAngle"]["supported_targets"] == ["robosim"],
        "encoder angle movement remains RoboSim-only",
    )
    check(
        by_name["SetLizard"]["supported_targets"] == ["robosim", "esp32"],
        "lizard capability remains unavailable on Arduino",
    )
    check(
        by_name["Wait"]["supported_targets"] == ["robosim", "esp32", "arduino"],
        "runtime control remains portable across all targets",
    )

    capabilities = {row["id"]: row for row in contract["capabilities"]}
    required = {cap_id for cap_id, row in capabilities.items() if row["required"]}
    check(required == {"motion.basic", "runtime.control"}, "required capability set remains explicit")
    target_ids = [row["id"] for row in contract["targets"]]
    for capability_id in required:
        check(
            capabilities[capability_id]["targets"] == target_ids,
            f"required capability {capability_id} is present on every target",
        )


def test_api_semantic_projection(contract: dict) -> None:
    by_name = {row["producer_name"]: row for row in contract["operations"]}
    ultrasonic = by_name["ReadUltrasonic"]["api"]
    check(ultrasonic["qualified_name"] == "sensor.read_ultrasonic", "API identity joins canonical opcode")
    check(ultrasonic["returns"] == "int", "API return contract survives consolidation")
    check(ultrasonic["args"] == [], "zero-argument API signature survives consolidation")

    line_state = by_name["GetTraceState"]["api"]
    check([arg["type"] for arg in line_state["args"]] == ["int", "int"], "API argument types survive consolidation")
    check(line_state["returns"] == "bool", "boolean return type survives consolidation")

    internal = by_name["JumpIfTrue"]["api"]
    check(internal["public"] is False, "internal control opcode cannot become public through projection")


def test_architecture_manifest() -> None:
    manifest_path = ROOT / "packages" / "robot-isa" / "architecture_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    production = manifest["production"]
    check(
        production["api_source_of_truth"] == "robot-language/specification/api.yaml",
        "architecture manifest declares API semantic owner",
    )
    check(
        production["isa_source_of_truth"] == "packages/robot-isa/canonical_isa.json",
        "architecture manifest declares ISA owner",
    )
    check(
        production["capability_source_of_truth"] == "packages/robot-isa/capability_model.json",
        "architecture manifest declares capability owner",
    )
    check(
        production["target_profile_source_of_truth"] == "packages/robot-isa/target_profiles.json",
        "architecture manifest declares target-profile owner",
    )
    projection = manifest["platform_contract"]
    check(projection["task"] == "H32", "architecture manifest records H32 consolidation")
    check(projection["checked_in_projection"] is False, "generated projection is not a checked-in authority")
    check(projection["generator"] == "tools/platform_contract.py", "projection generator is explicit")


def test_projection_is_not_a_production_dependency() -> None:
    forbidden_token = "platform_contract.json"
    roots = [ROOT / "robot-compiler", ROOT / "robot-platform", ROOT / "robostudio"]
    offenders: list[str] = []
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".cpp", ".c", ".h", ".hpp"}:
                continue
            if forbidden_token in path.read_text(encoding="utf-8", errors="ignore"):
                offenders.append(path.relative_to(ROOT).as_posix())
    check(not offenders, f"production layers do not consume generated projection: {offenders}")


def write_evidence(contract: dict) -> None:
    artifact = ROOT / "artifacts" / "platform_contract.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(platform_contract.render_contract(contract), encoding="utf-8")
    check(artifact.is_file() and artifact.stat().st_size > 0, "consolidated platform contract evidence is emitted")


def main() -> int:
    contract = test_consolidated_contract()
    test_target_support(contract)
    test_api_semantic_projection(contract)
    test_architecture_manifest()
    test_projection_is_not_a_production_dependency()
    write_evidence(contract)
    print("EPIC H32 Platform Contract Consolidation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
