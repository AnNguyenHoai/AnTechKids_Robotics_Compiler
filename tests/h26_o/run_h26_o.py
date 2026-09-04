#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_o" / "test_legacy_cleanup.py"
result = subprocess.run([sys.executable, "-m", "pytest", str(TEST), "-q"], cwd=ROOT)
print("H26-O legacy cleanup tests: PASS" if result.returncode == 0 else "H26-O legacy cleanup tests: FAIL")
sys.exit(result.returncode)
