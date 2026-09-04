#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_n_physical_validation.py"
result = subprocess.run([sys.executable, "-m", "unittest", str(TEST)], cwd=ROOT)
print("H26-N physical validation: PASS" if result.returncode == 0 else "H26-N physical validation: FAIL")
sys.exit(result.returncode)
