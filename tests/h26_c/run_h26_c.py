#!/usr/bin/env python3
"""Standalone H26-C runner; no third-party test framework required."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "robot-compiler"))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromName("test_canonical_isa")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("H26-C canonical ISA: PASS" if result.wasSuccessful() else "H26-C canonical ISA: FAIL")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
