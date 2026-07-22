#!/usr/bin/env python3
import unittest
import sys
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def run_tests(verbosity=1, output_json=None):
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Build report
    report = {
        "timestamp": time.time(),
        "testsRun": result.testsRun,
        "errors": len(result.errors),
        "failures": len(result.failures),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
        "details": []
    }
    for test, traceback in result.errors:
        report["details"].append({"test": str(test), "status": "ERROR", "traceback": traceback})
    for test, traceback in result.failures:
        report["details"].append({"test": str(test), "status": "FAIL", "traceback": traceback})

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    return result.wasSuccessful()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument("--json", help="Output JSON report file")
    args = parser.parse_args()
    verbosity = min(args.verbose + 1, 2)
    success = run_tests(verbosity, args.json)
    sys.exit(0 if success else 1)