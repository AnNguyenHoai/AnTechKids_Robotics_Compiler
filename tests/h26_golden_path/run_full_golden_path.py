#!/usr/bin/env python3
"""Run the complete H26 acceptance/golden-path regression without pytest."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER_AUDIT = ROOT / "tests" / "h26_runner_audit" / "run_h26_runner_audit.py"
SELF = Path(__file__).resolve()


def acceptance_runners() -> list[Path]:
    """Discover all H26 acceptance runners except infrastructure/self runners."""
    runners = sorted(ROOT.glob("tests/h26_*/run_*.py"))
    excluded = {RUNNER_AUDIT.resolve(), SELF}
    return [path for path in runners if path.resolve() not in excluded]


def run_gate(path: Path) -> int:
    relative = path.relative_to(ROOT)
    print(f"\n=== Running {relative} ===")
    result = subprocess.run([sys.executable, str(path)], cwd=ROOT)
    print(f"=== {relative}: {'PASS' if result.returncode == 0 else 'FAIL'} ===")
    return result.returncode


def main() -> int:
    runners = acceptance_runners()
    if not runners:
        print("H26 Golden Path Regression: FAIL (no acceptance runners discovered)")
        return 1

    failures: list[Path] = []

    # Verify runner portability before executing the individual acceptance gates.
    if run_gate(RUNNER_AUDIT) != 0:
        failures.append(RUNNER_AUDIT)

    for runner in runners:
        if run_gate(runner) != 0:
            failures.append(runner)

    print("\n=== H26 Golden Path Regression Summary ===")
    print(f"Gates discovered: {len(runners)}")
    print(f"Gates failed: {len(failures)}")

    if failures:
        for path in failures:
            print(f"FAIL: {path.relative_to(ROOT)}")
        print("H26 Golden Path Regression: FAIL")
        return 1

    print("H26 Golden Path Regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
