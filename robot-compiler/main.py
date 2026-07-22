#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys

from compiler.compiler import RobotCompiler
from compiler.emitter import HeaderEmitter


def main():
    parser = argparse.ArgumentParser(description="Robot Compiler")
    parser.add_argument("--file", default="examples/demo.py", help="Source file (absolute or relative to robot-compiler)")
    parser.add_argument("--output", default=None, help="Output header file path")
    args = parser.parse_args()

    ROOT = Path(__file__).resolve().parent
    source_path = Path(args.file)

    if not source_path.is_absolute():
        source_path = ROOT / args.file

    if not source_path.exists():
        print(f"Error: Source file '{source_path}' not found.", file=sys.stderr)
        return 1

    if args.output:
        output_file = Path(args.output)
    else:
        output_file = (
            ROOT.parent
            / "robot-platform"
            / "main"
            / "src"
            / "Application"
            / "generated_program.h"
        )

    compiler = RobotCompiler()
    program = compiler.compile(source_path)
    HeaderEmitter().emit(program, output_file)
    print(f"[OK] Compiled successfully! Output written to {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())