#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_m_deployment_contract.py"
result = subprocess.run([sys.executable, "-m", "pytest", str(TEST), "-q"], cwd=ROOT)
print("H26-M deployment contract: PASS" if result.returncode == 0 else "H26-M deployment contract: FAIL")
sys.exit(result.returncode)
