#!/usr/bin/env python3
"""Standalone H26-F safety validation runner."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
suite = unittest.defaultTestLoader.loadTestsFromName("tests.h26_f.test_safety_validator", module=None)
result = unittest.TextTestRunner(verbosity=2).run(suite)
print("H26-F compiler safety: PASS" if result.wasSuccessful() else "H26-F compiler safety: FAIL")
sys.exit(0 if result.wasSuccessful() else 1)
