#!/usr/bin/env python3
"""Standalone H26 OTA/one-click/physical-validation regression gate."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_ota" / "test_network_deployment.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_tests():
    spec = importlib.util.spec_from_file_location("h26_ota_tests", TEST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load H26 OTA tests: {TEST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Run H26 OTA assertions without depending on pytest."""
    module = load_tests()
    tests = [
        getattr(module, name)
        for name in dir(module)
        if name.startswith("test_") and callable(getattr(module, name))
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print("H26 OTA/one-click/physical-validation tests: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"H26 OTA/one-click/physical-validation tests: FAIL ({exc})")
        raise SystemExit(1)
