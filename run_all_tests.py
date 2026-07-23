#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run_script(script_path):
    print(f"Running {script_path} ...")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        return False
    return True

def main():
    tests = [
        ROOT / "robot-compiler" / "tests" / "run_tests.py",
        ROOT / "robot-frontend-robosim" / "test" / "run_tests.py",
    ]
    all_passed = True
    for test in tests:
        if not run_script(test):
            all_passed = False
            break

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()