#!/usr/bin/env python3
"""Run the repository's regression and H26/H27/H28/H29/RSD contract test suites."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_script(script_path: Path) -> bool:
    print(f"\n=== Running {script_path.relative_to(ROOT)} ===")
    result = subprocess.run([sys.executable, str(script_path)], cwd=ROOT, text=True)
    if result.returncode != 0:
        print(f"FAILED: {script_path.relative_to(ROOT)} (exit {result.returncode})", file=sys.stderr)
        return False
    print(f"PASS: {script_path.relative_to(ROOT)}")
    return True


def main() -> int:
    tests = [
        ROOT / "robot-compiler" / "tests" / "run_tests.py",
        ROOT / "robot-frontend-robosim" / "test" / "run_tests.py",
        ROOT / "robot-compiler" / "integration" / "end_to_end" / "run_integration_tests.py",
        ROOT / "tests" / "c4" / "test_language_semantics.py",
        ROOT / "tests" / "c5" / "test_c5_pipeline.py",
        ROOT / "tests" / "rsd_02" / "run_rsd_02.py",
        ROOT / "tests" / "rsd_03" / "run_rsd_03.py",
        ROOT / "tests" / "rsd_04" / "run_rsd_04.py",
        ROOT / "tests" / "rsd_05" / "run_rsd_05.py",
        ROOT / "tests" / "rsd_06" / "run_rsd_06.py",
        ROOT / "tests" / "rsd_07" / "run_rsd_07.py",
        ROOT / "tests" / "rsd_08" / "run_rsd_08.py",
        ROOT / "tests" / "rsd_09" / "run_rsd_09.py",
        ROOT / "tests" / "rsd_10" / "run_rsd_10.py",
        ROOT / "tests" / "rsd_11" / "run_rsd_11.py",
        ROOT / "tests" / "rsd_12" / "run_rsd_12.py",
        ROOT / "tests" / "rsd_13" / "run_rsd_13.py",
        ROOT / "tests" / "rsd_14" / "run_rsd_14.py",
        ROOT / "tests" / "h26_a" / "run_h26_a.py",
        ROOT / "tests" / "h26_b" / "run_h26_b.py",
        ROOT / "tests" / "h26_c" / "run_h26_c.py",
        ROOT / "tests" / "h26_d" / "run_h26_d.py",
        ROOT / "tests" / "h26_e" / "run_h26_e.py",
        ROOT / "tests" / "h26_f" / "run_h26_f.py",
        ROOT / "tests" / "h26_g" / "run_h26_g.py",
        ROOT / "tests" / "h26_h" / "run_h26_h.py",
        ROOT / "tests" / "h26_i" / "run_h26_i.py",
        ROOT / "tests" / "h26_j" / "run_h26_j.py",
        ROOT / "tests" / "h26_k" / "run_h26_k.py",
        ROOT / "tests" / "h26_l" / "run_h26_l.py",
        ROOT / "tests" / "h26_m" / "run_h26_m.py",
        ROOT / "tests" / "h26_ota" / "run_h26_ota.py",
        ROOT / "tests" / "h26_o" / "run_h26_o.py",
        ROOT / "tests" / "h27_a1" / "run_h27_a1.py",
        ROOT / "tests" / "h27_b0" / "run_h27_b0.py",
        ROOT / "tests" / "h27_b" / "run_h27_b.py",
        ROOT / "tests" / "h28_b" / "run_h28_b.py",
        ROOT / "tests" / "h29_a" / "run_h29_a.py",
        ROOT / "tests" / "h29_b" / "run_h29_b.py",
        ROOT / "tests" / "h29_c" / "run_h29_c.py",
        ROOT / "tests" / "h29_d" / "run_h29_d.py",
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
