#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_ota" / "test_network_deployment.py"
result = subprocess.run([sys.executable, "-m", "pytest", str(TEST), "-q"], cwd=ROOT)
print("H26 OTA/one-click/physical-validation tests: PASS" if result.returncode == 0 else "H26 OTA/one-click/physical-validation tests: FAIL")
sys.exit(result.returncode)
