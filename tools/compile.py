#!/usr/bin/env python3
import sys
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "robot-compiler"))

from compiler.compiler import RobotCompiler
from compiler.emitter import HeaderEmitter
import argparse

def compile_file(input_path, output_header=None, report_path=None):
    input_path = Path(input_path)
    if output_header is None:
        build_dir = ROOT / "build" / input_path.stem
        build_dir.mkdir(parents=True, exist_ok=True)
        output_header = build_dir / "program.h"
        report_path = build_dir / "compile_report.json"
    else:
        output_header = Path(output_header)
        if report_path is None:
            report_path = output_header.parent / "compile_report.json"

    start = time.time()
    compiler = RobotCompiler()
    program = compiler.compile(str(input_path))
    compile_time = time.time() - start

    HeaderEmitter().emit(program, output_header)

    report = {
        "input": str(input_path),
        "output": str(output_header),
        "compile_time_seconds": compile_time,
        "instruction_count": len(program.instructions),
        "variable_count": compiler.global_scope.next_index,
        "temp_count": compiler.temp_id,
        "function_count": len(compiler.functions),
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    return report

def main():
    parser = argparse.ArgumentParser(description="Compile .rewrite.py to header")
    parser.add_argument("--input", required=True, help="Input .rewrite.py file")
    parser.add_argument("--output", help="Output header file (optional)")
    parser.add_argument("--report", help="Output JSON report file (optional)")
    args = parser.parse_args()
    compile_file(args.input, args.output, args.report)
    print("Compilation complete.")

if __name__ == "__main__":
    main()