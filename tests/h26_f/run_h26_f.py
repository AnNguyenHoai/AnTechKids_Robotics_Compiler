#!/usr/bin/env python3
"""Standalone H26-F safety validation runner."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_PACKAGE_DIR = ROOT / "tests" / "h26_f"

# The repository intentionally does not require ``tests`` to be an installed
# Python package. Load the H26-F test module by its directory name instead of
# using the package-qualified ``tests.h26_f...`` import.
if str(TEST_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_PACKAGE_DIR))

suite = unittest.defaultTestLoader.loadTestsFromName("test_safety_validator")
result = unittest.TextTestRunner(verbosity=2).run(suite)
print("H26-F compiler safety: PASS" if result.wasSuccessful() else "H26-F compiler safety: FAIL")
sys.exit(0 if result.wasSuccessful() else 1)
