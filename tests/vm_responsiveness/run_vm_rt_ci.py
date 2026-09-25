#!/usr/bin/env python3
"""Dedicated host CI runner for the VM responsiveness initiative (#311)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GATES = [
    ROOT / "tests" / "vm_responsiveness" / "run_vm_responsiveness_baseline.py",
    ROOT / "tests" / "vm_responsiveness" / "run_run_slice_core.py",
    ROOT / "tests" / "vm_responsiveness" / "vm_rt_contract_guard.py",
    ROOT / "tests" / "vm_responsiveness" / "run_vm_rt_negative.py",
    ROOT / "tests" / "vm_responsiveness" / "run_compatibility_replay.py",
    ROOT / "robot-compiler" / "tests" / "run_tests.py",
    ROOT / "tests" / "line_follow_stability" / "run_line_follow_stability.py",
    ROOT / "tests" / "h35_compatibility" / "run_h35_compatibility.py",
]


def environment() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    root = str(ROOT)
    env["PYTHONPATH"] = root if not env.get("PYTHONPATH") else root + os.pathsep + env["PYTHONPATH"]
    return env


def main() -> int:
    missing = [str(path.relative_to(ROOT)) for path in GATES if not path.is_file()]
    if missing:
        raise AssertionError(f"missing required VM-RT gate(s): {missing}")

    for gate in GATES:
        rel = gate.relative_to(ROOT)
        print(f"\n=== VM-RT gate: {rel} ===")
        result = subprocess.run([sys.executable, str(gate)], cwd=ROOT, env=environment(), text=True)
        if result.returncode != 0:
            print(f"FAILED: {rel} (exit {result.returncode})", file=sys.stderr)
            return result.returncode or 1
        print(f"PASS: {rel}")

    print("\nVM-RT HOST CI: ALL REQUIRED GATES PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
