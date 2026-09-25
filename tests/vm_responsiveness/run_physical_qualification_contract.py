#!/usr/bin/env python3
"""Host contract test for the VM-RT physical qualification harness."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "vm_rt_qualification.py"
FIXTURES = ROOT / "tests" / "vm_responsiveness" / "fixtures"
OUTPUT = ROOT / ".build" / "vm_rt" / "qualification-fixture-report.json"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    result = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--telemetry", str(FIXTURES / "physical_qualification_sample.jsonl"),
            "--metadata", str(FIXTURES / "physical_qualification_metadata.json"),
            "--output", str(OUTPUT),
        ],
        cwd=ROOT,
        text=True,
    )
    check("qualification tool exits successfully", result.returncode == 0)
    check("qualification report is emitted", OUTPUT.is_file())
    report = json.loads(OUTPUT.read_text(encoding="utf-8"))
    check("qualification report schema is stable", report.get("schema_version") == 1)
    check("fixture cannot masquerade as physical evidence", report.get("qualification_status") == "NON_PHYSICAL_EVIDENCE_ONLY")
    check("all telemetry records are retained", report.get("records") == 3)
    check("slice latency distribution is calculated", report["slice_duration_us"] == {"count": 3, "p50": 240, "p95": 260, "p99": 260, "max": 260})
    check("stop latency is measured when observed", report["stop_latency_us"]["count"] == 1 and report["stop_latency_us"]["max"] == 180)
    check("snapshot physical read bound is preserved", report["line_snapshot"]["max_physical_reads"] == 3)
    check("slowest indivisible work unit is retained", report["slowest_work_units"][0] == {"slice": 3, "pc": 8, "duration_us": 120})
    check("thresholds remain unset without physical approval", report.get("thresholds") is None)
    print("VM-RT physical qualification harness contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
