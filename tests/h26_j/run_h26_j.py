#!/usr/bin/env python3
"""Standalone H26-J runtime capability contract runner."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_j" / "test_runtime_capability_contract.py"

result = subprocess.run(
    [sys.executable, "-m", "unittest", str(TEST)],
    cwd=ROOT,
)
if result.returncode == 0:
    print("H26-J runtime capability contract: PASS")
else:
    print("H26-J runtime capability contract: FAIL")
sys.exit(result.returncode)
