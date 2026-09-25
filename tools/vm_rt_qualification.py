#!/usr/bin/env python3
"""Build a VM-RT physical qualification report from firmware JSONL telemetry."""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

REQUIRED_FIELDS = {
    "type", "slice", "duration_us", "work_units", "reason", "start_pc", "end_pc",
    "max_work_us", "max_work_pc", "pending_op", "pending_state", "pending_pc",
    "pending_gen", "pending_opcode", "pending_opcode_valid", "line_seq", "line_age_us",
    "line_reads", "line_consumers", "line_invalid", "line_valid", "stop_latency_us",
    "max_stop_latency_us",
}


def percentile(values: list[int], p: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(p * len(ordered)) - 1))
    return int(ordered[index])


def parse_telemetry(path: Path) -> list[dict[str, int | str]]:
    records: list[dict[str, int | str]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("type") != "vm_rt":
            continue
        missing = REQUIRED_FIELDS.difference(row)
        if missing:
            raise ValueError(f"telemetry line {line_no} missing fields: {sorted(missing)}")
        records.append(row)
    if not records:
        raise ValueError("no vm_rt telemetry records found")
    return records


def stats(values: list[int]) -> dict[str, int]:
    return {
        "count": len(values),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "max": max(values) if values else 0,
    }


def build_report(records: list[dict[str, int | str]], metadata: dict) -> dict:
    durations = [int(row["duration_us"]) for row in records]
    max_work = [int(row["max_work_us"]) for row in records]
    line_age = [int(row["line_age_us"]) for row in records if int(row["line_valid"]) == 1]
    stop_latency = [int(row["stop_latency_us"]) for row in records if int(row["stop_latency_us"]) > 0]
    reason_counts = Counter(str(row["reason"]) for row in records)
    outliers = sorted(
        ({"slice": int(row["slice"]), "pc": int(row["max_work_pc"]), "duration_us": int(row["max_work_us"])} for row in records),
        key=lambda row: row["duration_us"],
        reverse=True,
    )[:10]

    evidence_kind = str(metadata.get("evidence_kind", "unspecified"))
    physical_robot = bool(metadata.get("physical_robot", False))
    report = {
        "schema_version": 1,
        "issue": 312,
        "evidence_kind": evidence_kind,
        "physical_robot": physical_robot,
        "scenario": metadata.get("scenario"),
        "hardware": metadata.get("hardware"),
        "profile": metadata.get("profile"),
        "firmware_commit": metadata.get("firmware_commit"),
        "program_identity": metadata.get("program_identity"),
        "slice_configuration": metadata.get("slice_configuration"),
        "records": len(records),
        "slice_duration_us": stats(durations),
        "work_unit_duration_us": stats(max_work),
        "line_snapshot_age_us": stats(line_age),
        "stop_latency_us": stats(stop_latency),
        "termination_reason_counts": dict(sorted(reason_counts.items())),
        "line_snapshot": {
            "valid_records": sum(1 for row in records if int(row["line_valid"]) == 1),
            "max_physical_reads": max(int(row["line_reads"]) for row in records),
            "max_invalid_count": max(int(row["line_invalid"]) for row in records),
        },
        "slowest_work_units": outliers,
        "failures_or_outliers": metadata.get("failures_or_outliers", []),
        "thresholds": metadata.get("thresholds"),
        "qualification_status": "PHYSICAL_EVIDENCE_CAPTURED" if physical_robot else "NON_PHYSICAL_EVIDENCE_ONLY",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--telemetry", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    report = build_report(parse_telemetry(args.telemetry), metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"VM-RT qualification report: {report['qualification_status']} ({report['records']} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
