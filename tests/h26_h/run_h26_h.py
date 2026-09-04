#!/usr/bin/env python3
"""Standalone H26-H firmware build integration contract runner."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

TEST_DIR = ROOT / "tests" / "h26_h"
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

suite = unittest.defaultTestLoader.loadTestsFromName("test_firmware_build")
result = unittest.TextTestRunner(verbosity=2).run(suite)
print("H26-H firmware build integration: PASS" if result.wasSuccessful() else "H26-H firmware build integration: FAIL")
sys.exit(0 if result.wasSuccessful() else 1)
