#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys
import json
import time

COMPILER_ROOT = Path(__file__).resolve().parent
if str(COMPILER_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPILER_ROOT))

from compiler.compiler import RobotCompiler
from compiler.emitter import HeaderEmitter
from compiler.error import CompilerError

def main():
    parser = argparse.ArgumentParser(description="Robot Compiler")
    parser.add_argument("--file", required=True, help="Source .rewrite.py file")
    parser.add_argument("--output", help="Output header file path (optional)")
    parser.add_argument("--report", help="Output JSON report file (optional)")
    parser.add_argument("--target", default="robosim", help="Compile target profile (default: robosim)")
    args = parser.parse_args()

    source_path = Path(args.file)
    if not source_path.exists():
        print(f"Error: Source file '{source_path}' not found.", file=sys.stderr)
        return 1

    if args.output:
        output_file = Path(args.output)
        report_file = Path(args.report) if args.report else output_file.parent / "compile_report.json"
    else:
        build_dir = Path(__file__).resolve().parent.parent / "build" / source_path.stem
        build_dir.mkdir(parents=True, exist_ok=True)
        output_file = build_dir / "program.h"
        report_file = build_dir / "compile_report.json"

    start = time.time()
    try:
        compiler = RobotCompiler(target=args.target)
        program = compiler.compile(source_path)
    except CompilerError as exc:
        print(json.dumps(exc.to_diagnostic(), sort_keys=True), file=sys.stderr)
        return 1
    compile_time = time.time() - start
    HeaderEmitter().emit(program, output_file)

    report = {
        "input": str(source_path),
        "output": str(output_file),
        "target": compiler.target,
        "compile_time_seconds": compile_time,
        "instruction_count": len(program.instructions),
        "variable_count": compiler.global_scope.next_index,
        "temp_count": compiler.temp_id,
        "function_count": len(compiler.functions),
    }
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Compiled successfully for target '{compiler.target}'! Output written to {output_file}")
    print(f"[OK] Report written to {report_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
