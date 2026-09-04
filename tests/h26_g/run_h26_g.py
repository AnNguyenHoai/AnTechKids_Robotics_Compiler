#!/usr/bin/env python3
"""Standalone H26-G unified E2E oracle runner."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = ROOT / "tests" / "h26_g"
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

suite = unittest.defaultTestLoader.loadTestsFromName("test_unified_e2e_oracle")
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(
    "H26-G unified E2E oracle: PASS"
    if result.wasSuccessful()
    else "H26-G unified E2E oracle: FAIL"
)
sys.exit(0 if result.wasSuccessful() else 1)
