#!/usr/bin/env python3
"""C5 physical validation preparation and build runner.

This tool intentionally separates software readiness from physical behavior.
It can prove rewrite/compile/header/firmware stages in CI and produces a
physical matrix for real-robot execution. Only a human/robot observation can
mark the final physical behavior PASS.
"""
import argparse, json, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATRIX = ROOT / "tests" / "c5" / "c5_matrix.json"
BUILD_ROOT = ROOT / "build" / "c5"
HEADER_DST = ROOT / "robot-platform" / "main" / "src" / "Application" / "generated_program.h"


def run(cmd):
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--firmware", action="store_true", help="Build firmware for each selected program")
    ap.add_argument("--flash", action="store_true", help="Flash firmware after successful build")
    ap.add_argument("--port")
    ap.add_argument("--test", action="append", dest="selected", help="Run only one C5 test id (repeatable)")
    args = ap.parse_args()

    matrix = json.loads(MATRIX.read_text())
    tests = [t for t in matrix["tests"] if not args.selected or t["id"] in args.selected]
    if not tests:
        raise SystemExit("No matching C5 tests")
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    summary = []

    for t in tests:
        src = ROOT / t["source"]
        out = BUILD_ROOT / t["id"]
        out.mkdir(parents=True, exist_ok=True)
        rewritten = out / "program.rewrite.py"
        header = out / "program.h"
        report = out / "compile_report.json"
        status = {"id": t["id"], "source": t["source"], "rewrite": "FAIL", "compile": "NOT_RUN", "firmware": "NOT_RUN", "flash": "NOT_RUN", "physical_behavior": "PENDING_REAL_ROBOT"}
        try:
            run([sys.executable, str(ROOT / "tools" / "rewrite.py"), "--input", str(src), "--output", str(rewritten)])
            status["rewrite"] = "PASS"
            run([sys.executable, str(ROOT / "tools" / "compile.py"), "--input", str(rewritten), "--output", str(header), "--report", str(report)])
            status["compile"] = "PASS"
            if args.firmware or args.flash:
                shutil.copy2(header, HEADER_DST)
                cmd = [sys.executable, "-m", "platformio", "run", "-d", str(ROOT / "robot-platform")]
                run(cmd)
                status["firmware"] = "PASS"
            else:
                status["firmware"] = "READY"
            if args.flash:
                cmd = [sys.executable, "-m", "platformio", "run", "-t", "upload", "-d", str(ROOT / "robot-platform")]
                if args.port: cmd += ["--upload-port", args.port]
                run(cmd)
                status["flash"] = "PASS"
        except Exception as e:
            status["error"] = str(e)
        summary.append(status)
        print(f"{t['id']}: rewrite={status['rewrite']} compile={status['compile']} firmware={status['firmware']} flash={status['flash']} physical={status['physical_behavior']}")

    (BUILD_ROOT / "c5_build_summary.json").write_text(json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "results": summary}, indent=2))
    if any(x["compile"] != "PASS" for x in summary):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
