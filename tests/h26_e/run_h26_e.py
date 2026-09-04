#!/usr/bin/env python3
"""Standalone H26-E capability contract runner."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_e" / "test_capability_model.py"

result = subprocess.run([sys.executable, "-m", "unittest", str(TEST)], cwd=ROOT)
if result.returncode == 0:
    print("H26-E capability model: PASS")
else:
    print("H26-E capability model: FAIL")
sys.exit(result.returncode)
