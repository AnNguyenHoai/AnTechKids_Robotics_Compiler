#!/usr/bin/env python3
"""Standalone H26-I architecture migration gate runner."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
TEST_DIR = ROOT / "tests" / "h26_i"
for path in (TOOLS, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

suite = unittest.defaultTestLoader.loadTestsFromName("test_architecture_migration")
result = unittest.TextTestRunner(verbosity=2).run(suite)
print("H26-I architecture migration: PASS" if result.wasSuccessful() else "H26-I architecture migration: FAIL")
sys.exit(0 if result.wasSuccessful() else 1)
