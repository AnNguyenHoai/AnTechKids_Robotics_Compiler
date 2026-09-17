#!/usr/bin/env python3
"""Standalone H26-O acceptance runner.

This gate intentionally does not depend on pytest because it is a portable
legacy-cleanup/deployment acceptance check that must run on target machines
with only the supported Python runtime available.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_o" / "test_legacy_cleanup.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_test_module():
    spec = importlib.util.spec_from_file_location("h26_o_legacy_cleanup", TEST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load H26-O tests: {TEST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    module = load_test_module()
    tests = [
        getattr(module, name)
        for name in sorted(dir(module))
        if name.startswith("test_") and callable(getattr(module, name))
    ]

    if not tests:
        raise RuntimeError("H26-O acceptance gate contains no test_* functions")

    failures = []
    for test in tests:
        try:
            test()
        except Exception as exc:
            failures.append((test.__name__, exc))
            print(f"FAIL: {test.__name__}: {exc}")
        else:
            print(f"PASS: {test.__name__}")

    if failures:
        print("H26-O legacy cleanup tests: FAIL")
        return 1

    print("H26-O legacy cleanup tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
