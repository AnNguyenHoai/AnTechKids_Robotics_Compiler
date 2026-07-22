#!/usr/bin/env python3
import sys
import json
import time
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compiler.compiler import RobotCompiler
from compiler.emitter import HeaderEmitter
from compiler.generated.opcode import Opcode


def run_benchmark(source_file, verbose=False):
    """Compile a file and gather metrics."""
    compiler = RobotCompiler()
    program = compiler.compile(source_file)

    # Metrics
    metrics = {
        "source_file": str(source_file),
        "instruction_count": len(program.instructions),
        "variable_count": compiler.global_scope.next_index,
        "temp_count": compiler.temp_id,
        "function_count": len(compiler.functions),
        "loop_count": len(compiler.loop_stack),  # not accurate, but okay
    }

    # Estimate program size (each instruction 7 bytes)
    metrics["program_size_bytes"] = len(program.instructions) * 7

    # Count opcode types
    opcode_counts = {}
    for ins in program.instructions:
        op_name = Opcode(ins.opcode).name
        opcode_counts[op_name] = opcode_counts.get(op_name, 0) + 1
    metrics["opcode_counts"] = opcode_counts

    if verbose:
        print(f"[Benchmark] {source_file}")
        print(f"  Instructions: {metrics['instruction_count']}")
        print(f"  Variables: {metrics['variable_count']}")
        print(f"  Temps: {metrics['temp_count']}")
        print(f"  Functions: {metrics['function_count']}")
        print(f"  Program size: {metrics['program_size_bytes']} bytes")
        print("  Opcode counts:", json.dumps(opcode_counts, indent=2))

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Benchmark runner")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--save", action="store_true", help="Save benchmark results")
    parser.add_argument("--output", default="benchmark_results.json", help="Output JSON file")
    parser.add_argument("files", nargs="*", default=["robot-compiler/examples/demo_forward.py"], 
                        help="Source files to benchmark")
    args = parser.parse_args()

    all_metrics = []
    for file in args.files:
        source_path = Path(file)
        if not source_path.exists():
            print(f"Error: {source_path} not found", file=sys.stderr)
            continue
        metrics = run_benchmark(source_path, args.verbose)
        all_metrics.append(metrics)

    if args.save:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(all_metrics, f, indent=2, ensure_ascii=False)
        print(f"[OK] Benchmarks saved to {args.output}")

    print("[OK] Benchmark complete.")


if __name__ == "__main__":
    main()