#!/usr/bin/env python3
"""Run the H26-A repository baseline guards without external test frameworks."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_FILE = ROOT / "tests" / "h26_a" / "test_golden_path_baseline.py"


def main() -> int:
    namespace = {"__file__": str(TEST_FILE)}
    exec(TEST_FILE.read_text(encoding="utf-8"), namespace)

    tests = sorted(
        (name, func)
        for name, func in namespace.items()
        if name.startswith("test_") and callable(func)
    )
    failures = 0
    for name, func in tests:
        try:
            func()
            print(f"PASS {name}")
        except Exception as exc:  # pragma: no cover - runner diagnostics
            failures += 1
            print(f"FAIL {name}: {exc}")

    print(f"H26-A baseline: {len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
