#!/usr/bin/env python3
"""Standalone H26-L capability-aware RoboStudio gate runner."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_l" / "test_target_aware_robostudio.py"

result = subprocess.run(
    [sys.executable, "-m", "pytest", str(TEST), "-q"],
    cwd=ROOT / "robostudio",
)
print("H26-L capability-aware RoboStudio: PASS" if result.returncode == 0 else "H26-L capability-aware RoboStudio: FAIL")
sys.exit(result.returncode)
