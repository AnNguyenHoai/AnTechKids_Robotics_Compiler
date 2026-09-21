#!/usr/bin/env python3
"""Standalone H34 Contract Traceability + CI Gates runner."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "contract_traceability.py"
OUTPUT = ROOT / ".build" / "h34" / "contract-traceability.json"


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, str(TOOL), "--output", str(OUTPUT)],
        cwd=ROOT,
        text=True,
    )
    check("traceability checker exits successfully", result.returncode == 0)
    check("machine-readable traceability evidence is emitted", OUTPUT.is_file())

    report = json.loads(OUTPUT.read_text(encoding="utf-8"))
    check("traceability schema is stable", report.get("schema_version") == 2)
    check("traceability task identity is H34", report.get("task") == "H34")
    check("traceability status is PASS", report.get("status") == "PASS")
    check("traceability has zero contract errors", report.get("summary", {}).get("error_count") == 0)

    rows = report.get("rows", [])
    public_count = report.get("summary", {}).get("public_api_count")
    check("every public API has exactly one trace row", len(rows) == public_count and public_count > 0)

    for row in rows:
        api = row["api"]
        check(f"{api} reaches canonical ISA", bool(row.get("canonical_id")))
        check(f"{api} reaches compiler registry", row.get("compiler_registry") == row.get("logical_opcode"))
        check(f"{api} reaches compiler handler", bool(row.get("compiler_handler")))
        check(f"{api} reaches capability model", bool(row.get("capability")))
        check(f"{api} has at least one supported target", bool(row.get("targets")))

        semantic = row.get("semantic")
        emitted = row.get("emitted_opcodes", [])
        lowering_kind = row.get("lowering_kind")
        if semantic == "Native":
            check(f"{api} preserves Native opcode through lowering", emitted == [row.get("logical_opcode")])
            check(f"{api} Native lowering is classified native", lowering_kind == "native")
        else:
            check(
                f"{api} non-Native semantic has explicit lowering classification",
                lowering_kind in {"degraded", "no_emit", "native"},
            )

        dispatch = row.get("emitted_dispatch", [])
        check(f"{api} has dispatch evidence for every emitted opcode", len(dispatch) == len(emitted))
        for emitted_row in dispatch:
            check(
                f"{api}:{emitted_row['opcode']} reaches VM dispatch",
                bool(emitted_row.get("runtime_endpoints")),
            )

    by_api = {row["api"]: row for row in rows}
    check("GUI update_var is explicitly no-emit", by_api["update_var"]["lowering_kind"] == "no_emit")
    check("GUI display_variable is explicitly no-emit", by_api["display_variable"]["lowering_kind"] == "no_emit")
    check(
        "dummy light sensor API traces actual LoadConst lowering",
        by_api["get_light_sensor_data"]["emitted_opcodes"] == ["LoadConst"],
    )
    check(
        "stub servo API does not falsely claim SetServo runtime dispatch",
        by_api["set_servo"]["emitted_opcodes"] == ["Nop"],
    )

    source = report.get("source_of_truth", {})
    check("API SSoT is declared", source.get("api") == "robot-language/specification/api.yaml")
    check("ISA SSoT is declared", source.get("isa") == "packages/robot-isa/canonical_isa.json")
    check("capability SSoT is declared", source.get("capabilities") == "packages/robot-isa/capability_model.json")
    check("target SSoT is declared", source.get("targets") == "packages/robot-isa/target_profiles.json")

    print(f"H34 Contract Traceability + CI Gates: PASS ({public_count} public APIs traced)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
