#!/usr/bin/env python3
"""Validate recorded S8-C physical evidence completeness, not authenticity."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REQUIRED = {
    "boot_idle", "compile_line7", "initial_motion",
    "line_center", "line_left", "line_right",
    "line_corner_left", "line_corner_right", "line_loss",
    "line5_baseline", "touch_gpio36", "servo_gpio19",
    "ultrasonic", "ota_full_firmware",
}
FIELDS = {
    "test_id", "trial", "decision", "boot_count_before",
    "boot_count_after", "free_heap_before", "free_heap_after",
    "latency_ms", "evidence_link", "notes",
}

def validate(path: Path) -> tuple[bool, list[str]]:
    issues = []
    if not path.is_file():
        return False, [f"Missing evidence CSV: {path}"]
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or set(reader.fieldnames) != FIELDS:
            return False, [f"Expected exact CSV fields {sorted(FIELDS)}"]
        rows = list(reader)
    seen = set()
    for index, row in enumerate(rows, start=2):
        case = row["test_id"].strip()
        if case not in REQUIRED:
            issues.append(f"row {index}: unknown test_id {case!r}")
            continue
        try:
            trial = int(row["trial"])
            before_boot = int(row["boot_count_before"])
            after_boot = int(row["boot_count_after"])
            before_heap = int(row["free_heap_before"])
            after_heap = int(row["free_heap_after"])
            assert trial in (1, 2, 3)
            assert before_boot >= 0 and after_boot >= 0
            assert before_heap > 0 and after_heap > 0
        except (ValueError, TypeError, AssertionError):
            issues.append(f"row {index}: invalid trial/boot/heap values")
            continue
        if (case, trial) in seen:
            issues.append(f"row {index}: duplicate {case} trial={trial}")
        seen.add((case, trial))
        decision = row["decision"].strip().upper()
        if decision != "PASS":
            issues.append(f"row {index}: decision must be PASS (got {decision!r})")
        if after_boot != before_boot:
            issues.append(f"row {index}: boot/reset count changed during trial")
        if not row["evidence_link"].strip():
            issues.append(f"row {index}: evidence_link is required")
        if not row["notes"].strip():
            issues.append(f"row {index}: observations/notes required")
        value = row["latency_ms"].strip()
        if value:
            try:
                assert float(value) >= 0
            except (ValueError, AssertionError):
                issues.append(f"row {index}: invalid latency_ms")
    for case in sorted(REQUIRED):
        for trial in (1, 2, 3):
            if (case, trial) not in seen:
                issues.append(f"missing {case} trial={trial}")
    return not issues, issues

def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_physical_evidence.py <completed-evidence.csv>")
        return 2
    ok, issues = validate(Path(sys.argv[1]))
    if not ok:
        for issue in issues:
            print("BLOCKED:", issue)
        print("PHYSICAL ACCEPTANCE: NOT ESTABLISHED")
        return 1
    print("Physical evidence CSV is structurally complete: 14 cases x 3 trials.")
    print("NOTE: This tool does not authenticate measurements or replace human review.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
