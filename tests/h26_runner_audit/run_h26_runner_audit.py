#!/usr/bin/env python3
"""Run the H26 acceptance runner audit without third-party dependencies."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "h26_runner_audit" / "test_acceptance_runners.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_tests():
    spec = importlib.util.spec_from_file_location("h26_runner_audit_tests", TEST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load H26 runner audit tests: {TEST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_tests()
    tests = [
        getattr(module, name)
        for name in sorted(dir(module))
        if name.startswith("test_") and callable(getattr(module, name))
    ]
    if not tests:
        raise RuntimeError("H26 runner audit contains no test_* functions")

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
        print("H26 Acceptance Runner Audit: FAIL")
        return 1

    print("H26 Acceptance Runner Audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
