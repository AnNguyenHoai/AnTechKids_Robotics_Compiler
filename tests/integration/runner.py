#!/usr/bin/env python3
"""
Integration Test Runner

Discovers and executes all integration tests.
"""

import sys
import json
import time
import argparse
import importlib
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "robot-compiler"))

# Import test modules dynamically
TEST_MODULES = [
    "test_motion",
    "test_sensor",
    "test_control",
    "test_output",
    "test_timing",
    "test_obstacle_avoidance",
    "test_compile_execute",
]

class TestResult:
    def __init__(self, name: str, passed: bool, message: str = "",
                 metrics: Dict[str, Any] = None, logs: List[str] = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.metrics = metrics or {}
        self.logs = logs or []

    def to_dict(self):
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "metrics": self.metrics,
            "logs": self.logs,
        }

def run_test_module(module_name: str, verbose: bool = False) -> TestResult:
    """Import and run a test module's run_test function."""
    try:
        mod = importlib.import_module(module_name)
        if not hasattr(mod, "run_test"):
            return TestResult(module_name, False, "Module has no run_test() function")
        start = time.time()
        result = mod.run_test(verbose=verbose)
        elapsed = time.time() - start
        # Ensure result has metrics
        if not isinstance(result, dict):
            result = {"passed": False, "message": "Invalid result type"}
        result.setdefault("metrics", {})
        result["metrics"]["execution_time_seconds"] = elapsed
        return TestResult(
            name=module_name,
            passed=result.get("passed", False),
            message=result.get("message", ""),
            metrics=result.get("metrics", {}),
            logs=result.get("logs", [])
        )
    except Exception as e:
        import traceback
        return TestResult(
            name=module_name,
            passed=False,
            message=f"Exception: {str(e)}",
            logs=[traceback.format_exc()]
        )

def main():
    parser = argparse.ArgumentParser(description="Integration Test Runner")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", help="Output JSON report file")
    parser.add_argument("--test", help="Run a specific test module (e.g., motion)")
    args = parser.parse_args()

    modules_to_run = TEST_MODULES
    if args.test:
        # Allow partial match
        matching = [m for m in TEST_MODULES if args.test in m]
        if not matching:
            print(f"Error: No test module matches '{args.test}'")
            sys.exit(1)
        modules_to_run = matching

    results: List[TestResult] = []
    for mod_name in modules_to_run:
        if args.verbose:
            print(f"\n=== Running {mod_name} ===")
        result = run_test_module(mod_name, verbose=args.verbose)
        results.append(result)
        if args.verbose:
            print(f"  Passed: {result.passed}")
            print(f"  Message: {result.message}")
            if result.metrics:
                print(f"  Metrics: {result.metrics}")
            if result.logs:
                print("  Logs:")
                for line in result.logs[-10:]:  # Show last 10 lines
                    print(f"    {line}")

    # Summary
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Total: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Success rate: {100 * passed_count / total_count:.1f}%")
    print("=" * 60)

    # Save JSON if requested
    if args.json:
        report = {
            "timestamp": time.time(),
            "summary": {
                "total": total_count,
                "passed": passed_count,
                "failed": total_count - passed_count,
            },
            "results": [r.to_dict() for r in results]
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to {args.json}")

    sys.exit(0 if passed_count == total_count else 1)

if __name__ == "__main__":
    main()