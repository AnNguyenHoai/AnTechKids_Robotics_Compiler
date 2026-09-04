#!/usr/bin/env python3
"""Run the repository's regression and H26 contract test suites."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_script(script_path: Path) -> bool:
    print(f"\n=== Running {script_path.relative_to(ROOT)} ===")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT,
        text=True,
    )
    if result.returncode != 0:
        print(f"FAILED: {script_path.relative_to(ROOT)} (exit {result.returncode})", file=sys.stderr)
        return False
    print(f"PASS: {script_path.relative_to(ROOT)}")
    return True


def main() -> int:
    tests = [
        # Existing regression suites.
        ROOT / "robot-compiler" / "tests" / "run_tests.py",
        ROOT / "robot-frontend-robosim" / "test" / "run_tests.py",
        ROOT / "robot-compiler" / "integration" / "end_to_end" / "run_integration_tests.py",
        ROOT / "tests" / "c4" / "test_language_semantics.py",
        ROOT / "tests" / "c5" / "test_c5_pipeline.py",
        # H26 contract suites: each task owns a standalone runner.
        ROOT / "tests" / "h26_a" / "run_h26_a.py",
        ROOT / "tests" / "h26_b" / "run_h26_b.py",
        ROOT / "tests" / "h26_c" / "run_h26_c.py",
        ROOT / "tests" / "h26_d" / "run_h26_d.py",
        ROOT / "tests" / "h26_e" / "run_h26_e.py",
        ROOT / "tests" / "h26_f" / "run_h26_f.py",
        ROOT / "tests" / "h26_g" / "run_h26_g.py",
        ROOT / "tests" / "h26_h" / "run_h26_h.py",
    ]

    missing = [path.relative_to(ROOT) for path in tests if not path.exists()]
    if missing:
        print("Missing required test runner(s):", file=sys.stderr)
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        return 2

    for test in tests:
        if not run_script(test):
            return 1

    print("\nALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
