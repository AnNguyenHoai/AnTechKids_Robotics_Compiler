#!/usr/bin/env python3
"""Standalone H26-B runner; no pytest dependency required."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_contract_drift as checker  # noqa: E402


def main() -> int:
    print("=== H26-B Contract Drift Check ===")
    try:
        findings, baseline = checker.run()
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    errors = [item for item in findings if item.severity == "ERROR"]
    print(f"Baseline commit: {baseline.get('baseline_commit')}")
    print(f"Semantic findings: {len(findings)}; errors: {len(errors)}")
    for item in findings:
        location = f" [{item.path}]" if item.path else ""
        print(f"{item.severity}: {item.check_id}: {item.message}{location}")

    if errors:
        print("H26-B contract check: FAIL")
        return 1

    suite = unittest.defaultTestLoader.loadTestsFromName("test_contract_drift")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        print("H26-B characterization tests: FAIL")
        return 1

    print("H26-B contract check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
