#!/usr/bin/env python3
"""Standalone H26-K target capability profile runner."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_k" / "test_target_capability_profiles.py"

result = subprocess.run(
    [sys.executable, "-m", "unittest", str(TEST)],
    cwd=ROOT,
)
if result.returncode == 0:
    print("H26-K target capability profiles: PASS")
else:
    print("H26-K target capability profiles: FAIL")
sys.exit(result.returncode)
