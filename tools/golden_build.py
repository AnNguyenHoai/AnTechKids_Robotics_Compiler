#!/usr/bin/env python3
import subprocess
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "robot-platform" / "golden"

def main():
    results = []
    for py_file in GOLDEN_DIR.glob("*.py"):
        print(f"Building {py_file.name}...")
        build_script = ROOT / "tools" / "build.py"
        build_dir = ROOT / "build" / py_file.stem
        cmd = [sys.executable, str(build_script), "--input", str(py_file), "--build-dir", str(build_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        report_path = build_dir / "compile_report.json"
        if report_path.exists():
            with open(report_path) as f:
                report = json.load(f)
                report["success"] = result.returncode == 0
                results.append(report)
        else:
            results.append({
                "program": py_file.name,
                "success": False,
                "error": result.stderr
            })

        if result.returncode != 0:
            print(f"  FAILED: {result.stderr}")
        else:
            print(f"  PASSED (instructions: {report.get('instruction_count', 'N/A')})")

    summary_path = ROOT / "build" / "golden_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Golden build summary saved to {summary_path}")

if __name__ == "__main__":
    main()